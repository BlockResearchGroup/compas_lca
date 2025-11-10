# Self-contained matching core: flattening, clause ops, facet-aware filter generation, scoring.

from dataclasses import dataclass

from enum import Enum

from typing import Any
from typing import Dict
from typing import List
from typing import Iterable
from typing import Tuple
from typing import Optional

from compas_lca.inventory.item import snapshot
from compas_lca.model.lca_element import LcaElement
from compas_lca.model.match import Match
from compas_lca.model.match import Matches

from compas_lca.match_rules import MATCH_RULES
from compas_lca.match_rules import MATERIAL_FACETS
from compas_lca.match_rules import COMPONENT_FACETS

from compas_lca.helpers import coerce_to_dict

"""
MATCHING GOAL:
Receive a set of InventoryItem's that correspond to the LcaElement's MatchingCore,
and adapts to the LOI inside of the LcaElement's MatchingCore. If the LOI is very low,
naturally a lot of InventoryItems will be appended.

Idea for later: crucial things like for instance concrete strength class can be speculated,
if it is not given. So for instance, if we have a generic concrete wall on the element side,
but no concrete strength class is given, then naturally it doesnt make a lot of sense to
match inventory item concretes with extremely high strength classes (as it's overkill for the element).
Another example would be a generic door, where there is no "special function" like security etc, but
no value is given on the element side, then it is not common sense to match speciality doors to said element.
This needs to be done in an intermediate step (speculation agent for specific material facets and component types)

MATCHING LOGIC (between LcaElement's MatchingCore and InventoryItem's MatchingCore)
- Only evaluate fields present on the element side, each element-specified field contributes an equal slice of the score.
- If the element doesn't specify a field (None/“unknown”), skip it entirely.
- If the element specifies a field and the item has no value → penalize.
- If both specify and they mismatch per the operator → penalize.
- If both specify and they match → reward.
- Extra info on the item that the element didn't ask for → ignored. (this might become relevant later)

EXAMPLE:
- If the element specifies 10 fields, each is worth 0.1
- matches add their slice, mismatches add 0
- partials (for numeric values) add a fraction (e.g., approx = 0.6 → adds 0.06)
- Missing on the item side with on_missing="penalty" counts as 0 (still in the denominator)
- Fields not specified by the element are ignored (not in the denominator).
"""


# -------------------------
# Helpers / Utilities
# -------------------------

def _as_list(x):
    if x is None:
        return []
    return x if isinstance(x, list) else [x]

def _norm_str(x: Any) -> Any:
    if isinstance(x, str):
        return x.strip().lower()
    if isinstance(x, list):
        return [_norm_str(v) for v in x]
    return x

def _get(d: Dict[str, Any], path: str, default=None):
    """Dot-path get for plain dicts."""
    cur = d
    for part in path.split('.'):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur

def _is_unknown(value: Any) -> bool:
    """Return True if value is an 'unknown' sentinel."""
    if value is None:
        return True
    if isinstance(value, str):
        return _norm_str(value) == "unknown"
    if isinstance(value, list):
        return any(_norm_str(v) == "unknown" for v in value if isinstance(v, str))
    return False

def _present_nontrivial(val: Any) -> bool:
    """True if the item core specifies a value (works for bool/enum/str/list/number)."""
    if val is None:
        return False
    if isinstance(val, str):
        s = _norm_str(val)
        return s not in ("", "unknown", "none", "null")
    if isinstance(val, (list, tuple, set, dict)):
        return len(val) > 0
    return True  # numbers, booleans, other non-None values

def to_dotmap(
    obj: Any,
    prefix: str = "",
    out: Optional[Dict[str, Any]] = None,
    _seen: Optional[set] = None
) -> Dict[str, Any]:
    """
    Flatten nested dicts / Pydantic models into dot-path keys.
    - Lists/tuples are kept as-is (no index expansion).
    - Enums and primitives are treated as leaf values.
    - Recurse ONLY into dicts and Pydantic models.
    - No use of collections.abc.
    """
    if out is None:
        out = {}
    if _seen is None:
        _seen = set()

    # Leaf/terminal: primitives & Enum
    if obj is None or isinstance(obj, (str, int, float, bool, Enum)):
        if prefix:
            out[prefix] = obj
        return out

    # Keep sequences as-is (don’t recurse into elements)
    if isinstance(obj, (list, tuple)):
        if prefix:
            out[prefix] = obj
        return out

    # Prevent cycles
    oid = id(obj)
    if oid in _seen:
        return out
    _seen.add(oid)

    # Pydantic model → to dict
    if hasattr(obj, "model_dump"):
        try:
            items = obj.model_dump(exclude_none=False).items()
        except Exception:
            # If model_dump fails, treat it as a leaf
            if prefix:
                out[prefix] = obj
            return out

    # Plain dict
    elif isinstance(obj, dict):
        items = obj.items()

    else:
        # Anything else is treated as a leaf (no __dict__ recursion)
        if prefix:
            out[prefix] = obj
        return out

    for k, v in items:
        key = f"{prefix}.{k}" if prefix else str(k)
        # Recurse only into dicts or Pydantic models
        if hasattr(v, "model_dump") or isinstance(v, dict):
            to_dotmap(v, key, out, _seen)
        else:
            out[key] = v

    return out

def normalize_core_map(m: Dict[str, Any]) -> Dict[str, Any]:
    """
    Light normalization: lowercase str and Optional[str] fields.
    Enables semantic matching (e.g., 'Holcim', 'HOLCIM', 'holcim' is the same)
    Not relevant yet, only if we wanna include manufacturer and provenance
    later for fuzzy matching.
    """
    out = dict(m)
    # Fields to normalize if present
    stringy = [
        "manufacturer",
        "provenance",
        "production_location",
        "strength_class"
    ]
    for k in stringy:
        if k in out and out[k] is not None:
            out[k] = _norm_str(out[k])
    return out



def compute_overspec_penalty(
    item_map: Dict[str, Any],
    elem_map: Dict[str, Any],
    rules_by_group: Dict[str, list],
    n_eval: int,
    apply_overspec: bool = True,
    max_total_strength: float = 1.0,
) -> Tuple[float, List[Dict[str, Any]]]:
    """
    Universal overspec deduction:
      If ELEMENT did not specify path (None/unknown/empty) but ITEM specifies a nontrivial value
      AND the rule has overspec enabled, subtract (1/n_eval) * strength from the score.

    strength defaults to 0.25 if overspec == True; you can customize with:
      "overspec": {"strength": 0.35}

    A soft cap (max_total_strength) prevents runaway deductions.
    """
    if not apply_overspec or n_eval <= 0:
        return 0.0, []

    unit = 1.0 / float(n_eval)
    total_penalty = 0.0
    total_strength = 0.0
    details: List[Dict[str, Any]] = []

    for _, rules in rules_by_group.items():
        for r in rules:
            ospec = r.get("overspec", False)
            if not ospec:
                continue

            # Determine strength
            strength = 0.25
            if isinstance(ospec, dict):
                strength = float(ospec.get("strength", strength))
            strength = max(0.0, min(1.0, strength))

            # Which element path to check (same as item path unless overridden)
            _, elem_path = _normalize_rule_paths(r)

            # If element specified a value -> NOT overspec
            if not _is_unknown(elem_map.get(elem_path)):
                continue

            # Item has a nontrivial value?
            item_val = item_map.get(r.get("path"))
            if not _present_nontrivial(item_val):
                continue

            # Respect cap
            if total_strength + strength > max_total_strength:
                strength = max(0.0, max_total_strength - total_strength)
                if strength == 0.0:
                    break

            p = unit * strength
            total_penalty += p
            total_strength += strength
            details.append({
                "path": r.get("path"),
                "penalty": p,
                "strength": strength,
                "reason": "overspecified on item (element unspecified)"
            })

    return total_penalty, details

# --- identity gate used by eval_filter --------------------------------
def _identity_match(item_map: Dict[str, Any], elem_map: Dict[str, Any]) -> bool:
    """
    Enforce:
      R1: entry_type equal
      R2: if element.material_type set -> equal (materials)
          if element.component_type set -> equal (components)
      R3: if element has NO material_type BUT has functional_types -> require intersection
    note: item_map/elem_map are DOTMAPS (flattened), so use direct .get("a.b.c").
    """
    def _as_list(x):
        if x is None:
            return []
        return x if isinstance(x, list) else [x]

    def _norm_str(x):
        return x.strip().lower() if isinstance(x, str) else x

    et_item = _norm_str(item_map.get("entry_type"))
    et_elem = _norm_str(elem_map.get("entry_type"))
    if et_item != et_elem:
        return False

    if et_elem == "material":
        mt_elem = _norm_str(elem_map.get("facet.material_type"))
        if mt_elem and mt_elem != "unknown":
            mt_item = _norm_str(item_map.get("facet.material_type"))
            return mt_item == mt_elem

        # fallback: no material_type on element, but functional_types present
        elem_funcs = {_norm_str(v) for v in _as_list(elem_map.get("facet.material_facet.functional_types")) if v}
        if elem_funcs:
            item_funcs = {_norm_str(v) for v in _as_list(item_map.get("facet.material_facet.functional_types")) if v}
            return bool(elem_funcs & item_funcs)

        return True

    elif et_elem == "component":
        ct_elem = _norm_str(elem_map.get("facet.component_facet.component_type"))
        if ct_elem and ct_elem != "unknown":
            ct_item = _norm_str(item_map.get("facet.component_facet.component_type"))
            return ct_item == ct_elem
        return True

    return False


# -------------------------
# Clause + Operators
# -------------------------

@dataclass
class Clause:
    """
    Represents one matching rule between an InventoryItem and an LcaElement.

    A Clause has the following key attributes:
        - item_path:      dot-path to the field in `item_map`
        - op:             operator string ("equals_other", "approx", etc.)
        - value:          value for comparisons
        - elem_path:      dot-path to a field in `elem_map` (used in `equals_other`, etc.)
        - weight:         weight used later for scoring aggregation
        - abs_tol / rel_tol:  tolerance for numeric comparisons (only `approx`)
        - on_missing:     how to handle missing values ("penalty" | "netural" | "fail")

    Each clause compares a field on the item side against either:
      - a fixed literal value (via 'value'), OR
      - a corresponding field on the element side ('elem_path').
    """
    item_path: str                     # Path to field in the ITEM
    op: str                            # Operator (eq, equals, approx, intersects, etc.)
    value: Any = None
    elem_path: Optional[str] = None    # Path to field in the ELEMENT
    abs_tol: Optional[float] = None    # Absolute tolerance (numeric ops)
    rel_tol: Optional[float] = None    # Relative tolerance (numeric ops)

def approx_score(x: Optional[float], target: Optional[float], abs_tol: Optional[float], rel_tol: Optional[float]) -> float:
    """
    For numeric values like U-Value, thermal conductivity, density.
    Should be defined for each specific quantitative property, as reasonable tolerances vary
    """
    if x is None or target is None:
        return 0.0
    diff = abs(float(x) - float(target))
    if abs_tol is not None:
        return max(0.0, 1.0 - diff / float(abs_tol))
    if rel_tol is not None:
        base = abs(float(target)) if float(target) != 0.0 else 1.0
        return max(0.0, 1.0 - diff / (base * float(rel_tol)))
    return 1.0 if float(x) == float(target) else 0.0

def satisfies(item_value: Optional[str], wanted: Optional[str]) -> float:
    """
    For enums like loadbearing/placement with 'either' acting as wildcard.
    Returns 1.0 if satisfied, else 0.0. Missing -> 0.0 (penalty handling happens elsewhere).
    """
    if item_value is None or wanted is None:
        return 0.0
    item_value = _norm_str(item_value)
    wanted = _norm_str(wanted)
    if item_value == wanted:
        return 1.0
    if item_value == "either":
        return 1.0
    if wanted == "either":
        return 1.0
    return 0.0

def eval_clause(item_map: Dict[str, Any], elem_map: Dict[str, Any], clause: Clause) -> Tuple[Optional[float], str]:
    """
    Evaluate a single matching rule ("clause") between an InventoryItem and an LcaElement core.

    Simplified "weightless, element-driven" semantics:
      - We only evaluate fields that the ELEMENT specifies.
      - If the element's RHS value is None/"unknown"/empty (for lists), the clause is skipped → returns (None, ...).
      - If the element specifies a value but the ITEM is missing it, that's a hard mismatch → returns (0.0, ...).
      - Otherwise, apply the operator and return a similarity in [0, 1].

    Returns
    -------
    (score, explanation)
        score:
          1.0 → perfect match
          0.0 → mismatch or item missing
          None → clause skipped because the element didn't specify a value
        explanation:
          human-readable detail of what was compared.
    """
    # Retrieve values
    item_value = item_map.get(clause.item_path, None)
    elem_value = clause.value
    if clause.elem_path:
        elem_value = elem_map.get(clause.elem_path, elem_value)

    # If the element value is (None/"unknown"), skip entirely
    if clause.elem_path and _is_unknown(elem_value):
        return None, f"{clause.op} skipped → element unspecified/unknown"

    # Special case for list-type RHS where element provided an empty list
    if clause.op == "intersects_other":
        elem_list = _as_list(elem_value)
        if len(elem_list) == 0:
            return None, "intersects(...) → neutral (element empty)"

    # If the element specified a value but the item value is missing → hard mismatch (0.0)
    if item_value is None:
        return 0.0, f"{clause.op} missing on item → 0.00"

    # equals_other: scalar equality (works for strings, numbers, booleans)
    if clause.op == "equals_other":
        score = 1.0 if item_value == elem_value else 0.0
        return score, f"equals_other(item={item_value}, elem={elem_value}) → {score :.2f}"

    # intersects_other: list overlap
    if clause.op == "intersects_other":
        item_set = {_norm_str(v) for v in set(_as_list(item_value)) if v is not None}
        elem_set = {_norm_str(v) for v in set(_as_list(elem_value)) if v is not None}
        if "unknown" in elem_set:
            return None, "intersects(...) → neutral (element unknown)"
        score = 1.0 if (item_set & elem_set) else 0.0
        return score, f"intersects(item={list(item_set)}, elem={list(elem_set)}) → {score:.2f}"

    # approx: numeric tolerance
    if clause.op == "approx":
        score = approx_score(item_value, elem_value, clause.abs_tol, clause.rel_tol)
        return score, f"approx(item={item_value}, elem={elem_value}, abs={clause.abs_tol}, rel={clause.rel_tol}) → {score:.2f}"

    # satisfies: directional enum with 'either' wildcard (loadbearing, placement)
    if clause.op == "satisfies":
        score = satisfies(item_value, elem_value)
        return score, f"satisfies(item={item_value} ⟶ elem={elem_value}) → {score:.2f}"

    return 0.0, f"unknown_op({clause.op})"



def eval_filter(item_map: Dict[str, Any],
                elem_map: Dict[str, Any],
                clauses: List[Clause],
                rules_by_group: Optional[Dict[str, list]] = None,
                apply_overspec: bool = False) -> Tuple[float, List[Dict[str, Any]]]:
    """
    Evaluate and aggregate multiple Clause objects to compute the overall
    similarity score between an InventoryItem core (`item_map`) and an
    LcaElement core (`elem_map`) using a weightless, element-driven scheme
    with optional "overspecification" penalty support.

    ----------------------------
    Parameters
    ----------------------------
    item_map : dict
        Flattened (dot-path) dictionary of the InventoryItem's `item_core`.

    elem_map : dict
        Flattened (dot-path) dictionary of the LcaElement's `element_core`.

    clauses : List[Clause]
        Concrete comparison rules for this element. These are already filtered
        so that only element-specified fields produce clauses.

    rules_by_group : dict, optional
        The full `MATCH_RULES` structure, used for identifying which fields
        are marked with `"overspec"` for the optional penalty step.

    apply_overspec : bool, default=False
        Whether to apply the overspec penalty. If False, the scoring ignores
        all `"overspec"` flags and behaves purely element-driven.

    ----------------------------
    Returns
    ----------------------------
    (score, parts) : Tuple[float, List[Dict[str, Any]]]
        score : float
            Final normalized similarity score in [0, 1].
            Includes the overspec penalty if `apply_overspec=True`.

        parts : list of dict
            Detailed per-clause and per-penalty diagnostics. Each entry contains:
              - "path"     : item-side path of the evaluated rule
              - "op"       : operator used (e.g. "equals_other", "approx", "overspec")
              - "score"       : numeric similarity (or negative value for overspec penalty)
              - "neutral"  : True if the clause was excluded from scoring
              - "detail"   : explanation of what was compared or penalized


    ----------------------------
    Scoring model
    ----------------------------
    • Only fields that the **element** actually specifies are evaluated.

    • For each evaluated clause, `eval_clause(...)` returns:
        - 1.0 for a perfect match
        - a value in (0, 1) for partial matches (e.g. numeric `approx`)
        - 0.0 for mismatches OR when the item lacks the corresponding field

    • Clauses that return `None` are neutral and are excluded from both
      the numerator and denominator. These are typically cases where the
      element value was unspecified or "unknown" (e.g. an empty list).

    • The final score is the simple arithmetic mean across all evaluated
      (non-neutral) clauses

    ----------------------------
    Overspec penalty (optional)
    ----------------------------
    If `apply_overspec=True`, the function applies an additional post-hoc
    deduction to slightly reduce the score when the item is more specific 
    than the*element. It ensures,  that whenver there are generic inventory 
    items, they get slightly more prioritized for generic/vague element 
    descriptors (and when ranked, show up highest), although the items with 
    more specific information are technically not 'less correct'.

    This is determined by scanning the `MATCH_RULES` definitions (passed in
    `rules_by_group`) for any rules with `"overspec": True` or
    `"overspec": {"strength": <float>}`.

    For each such rule:
        • If the element did not specify a value (None / "unknown" / empty)
        • and the item did specify a nontrivial value
        → then a small penalty is subtracted from the score.

    The penalty per overspecified field is computed as:
        penalty_i = (1 / n_eval) * strength
    where:
        - n_eval is the number of evaluated (non-neutral) clauses
        - strength ∈ [0, 1] (default = 0.25 unless overridden per rule)

    The total penalty is capped so that it can never push the score below 0.
    Note: perhaps the score and "strength" is too convoluted and it should rather
    just adjust the score a little bit instead of custom weights etc.

    ----------------------------
    Example behavior
    ----------------------------
    • If 4 element fields were specified and matched 3 out of 4 item fields,
      score ≈ 0.75.
    • If an item also included `fire_retardant=True` while the element left
      that field unspecified, and the rule has `"overspec": {"strength": 0.5}`,
      then penalty = (1/4)*0.5 = 0.125 → final score ≈ 0.625.

    This allows subtle penalization of “overly specific” items while keeping
    the baseline matching logic clean and predictable.
    """
    # --- base score ---
    parts: List[Dict[str, Any]] = []
    sim_sum = 0.0
    n_eval = 0

    # --- identity hard gate ---
    if not _identity_match(item_map, elem_map):
        parts = [{
            "path": "identity",
            "op": "gate",
            "score": 0.0,
            "detail": "identity gate failed (entry_type/material_type/component_type/functional_types)",
        }]
        return 0.0, parts

    for clause in clauses:
        clause_score, detail = eval_clause(item_map, elem_map, clause)

        if clause_score is None:
            parts.append({
                "path": clause.item_path,
                "op": clause.op,
                "neutral": True,
                "detail": detail
            })
            continue

        n_eval += 1
        sim_sum += float(clause_score)
        parts.append({
            "path": clause.item_path,
            "op": clause.op,
            "score": float(clause_score),
            "detail": detail
        })

    final_score = (sim_sum / n_eval) if n_eval > 0 else 0.0

    # --- overspec ---
    if rules_by_group is not None and apply_overspec:
        penalty, pen_parts = compute_overspec_penalty(
            item_map, elem_map, rules_by_group, n_eval, apply_overspec=True
        )
        final_score = max(0.0, min(1.0, final_score - penalty))
        for pp in pen_parts:
            parts.append({
                "path": pp["path"],
                "op": "overspec",
                "score": -pp["penalty"],
                "detail": f"overspec penalty {pp['penalty']:.4f} (strength={pp['strength']})"
            })

    return final_score, parts


def _normalize_rule_paths(rule: dict) -> Tuple[str, Optional[str]]:
    """
    Return (item_path, elem_path) for a rule.
    - If explicit item_path/elem_path exist, use them.
    - Else, use 'path' for both sides.
    """
    if "item_path" in rule or "elem_path" in rule:
        return rule.get("item_path") or rule.get("path"), rule.get("elem_path") or rule.get("path")
    # compact form: one 'path' used on both sides
    p = rule["path"]
    return p, p

def _add_clause(clauses, element_map, rule):
    """
    Add a Clause if (a) this rule compares field-to-field, and
    (b) the ELEMENT has a specified value (not None/unknown) for the RHS.
    Literal-value rules ('value' provided) are always added.
    For 'boost_if_missing', duplicate the clause if the given element paths are missing.
    """
    item_path, elem_path = _normalize_rule_paths(rule)

    is_field_to_field = rule.get("value") is None
    if is_field_to_field and elem_path:
        rhs = element_map.get(elem_path, None)
        if _is_unknown(rhs):
            return  # skip when element doesn't specify

    # base clause
    def _append():
        clauses.append(Clause(
            item_path=item_path,
            elem_path=elem_path if is_field_to_field else None,
            op=rule["op"],
            value=rule.get("value"),
            abs_tol=rule.get("abs_tol"),
            rel_tol=rule.get("rel_tol"),
        ))

    _append()

    """
    TRY LATER (SHOULD THINK THROUGH THE SCORING METHOD)
    # Optional: duplicate if element is missing some key(s)
    # Only important for clear functional types without material descriptors
    # (i.e. descriptor says "rigid insulation", but no material descriptor is given,
    # then it should match (and boost the score) for any rigid_insulation entry)
    boost = rule.get("boost_if_missing")
    if isinstance(boost, dict):
        for missing_path, copies in boost.items():
            if _is_unknown(element_map.get(missing_path)):
                copies = max(0, int(copies))
                for _ in range(copies):
                    _append()
    """


def build_clauses(element_map: dict) -> List[Clause]:
    """Create the concrete Clause list from the 3-level rules."""
    clauses: List[Clause] = []

    # hard-fail if element entry_type is unknown
    elem_et = element_map.get("entry_type")
    if elem_et == "unknown":
        return clauses

    # common (always)
    for r in MATCH_RULES["common"]:
        _add_clause(clauses, element_map, r)

    # specific_common
    if elem_et == "material":
        for r in MATCH_RULES["material_common"]:
            _add_clause(clauses, element_map, r)
    elif elem_et == "component":
        for r in MATCH_RULES["component_common"]:
            _add_clause(clauses, element_map, r)

    # facet
    if elem_et == "material":
        mat_type = element_map.get("facet.material_type")
        if mat_type and mat_type in MATERIAL_FACETS:
            for r in MATERIAL_FACETS[mat_type]:
                _add_clause(clauses, element_map, r)

    elif elem_et == "component":
        comp_type = element_map.get("facet.component_facet.component_type")
        if comp_type and comp_type in COMPONENT_FACETS:
            for r in COMPONENT_FACETS[comp_type]:
                _add_clause(clauses, element_map, r)

    return clauses

# -------------------------
# score one item vs one element core
# -------------------------

# Score ONE item against ONE element core's clauses -> Match
def score_item_to_core(
    item: Any,
    elem_map: Any, # dotmap
    clauses: Any,
    *,
    apply_overspec: Optional[bool] = None,
    include_explain: bool = True,
) -> Match:
    
    # Extract item fields
    item_dict = coerce_to_dict(item)
    item_id = item_dict.get("id")
    item_core = item_dict.get("item_core")
    item_map = normalize_core_map(to_dotmap(item_core))
    item_name = item_core.get("name")
    item_meta = item_dict.get("metadata") or {}
    dataset_source = item_meta.get("dataset_source")
    item_snapshot = snapshot(item_dict)

    # Score
    final_score, parts = eval_filter(
        item_map,
        elem_map,
        clauses,
        rules_by_group=MATCH_RULES,
        apply_overspec=apply_overspec,
    )

    # Return a proper Match model
    return Match(
        item_id=item_id,
        item_name=item_name,
        score=float(final_score),
        explain=parts if include_explain else None,
        dataset_source=dataset_source,
        snapshot=item_snapshot,
    )

# Score MANY items against ONE core -> Matches
def score_items_to_core(
    items: Iterable[Any],
    element_core: Any,
    *,
    top_k: int = 5,
    apply_overspec: bool = False,
    include_explain: bool = False
) -> Matches:
    
    # Build clauses for this specific element_core once, use for all items
    ec_dict = coerce_to_dict(element_core)
    elem_map = normalize_core_map(to_dotmap(ec_dict))
    clauses = build_clauses(elem_map)
    core_id = str(ec_dict.get("core_id"))

    scored: List[Match] = []
    for item in items:
        match = score_item_to_core(
            item,
            elem_map,
            clauses,
            apply_overspec=apply_overspec if apply_overspec else False,
            include_explain=include_explain if include_explain else False,
        )
        scored.append(match)

    # rank all scored items
    scored.sort(key=lambda m: -m.score)

    # return top_k matches (this number can be customized)
    return Matches(core_id=core_id, matches=scored[: max(0, int(top_k))])


def score_items_to_element(
    items: Iterable[Any],   # Many InventoryItem instances, or dicts
    element: Any, # LcaElement instance, or dict
    *,
    top_k: int = 5,
    apply_overspec: Optional[bool] = None,
    include_explain: bool = True,
) -> LcaElement:
    """
    Scores `items` against each MatchingCore in `element.element_core`,
    writes the top-k Matches per core into `element.matched_items`,
    and returns the same LcaElement (same id).
    """
    # Ensure we have a model instance
    if not isinstance(element, LcaElement):
        element = LcaElement(**element)  # preserves id from the dict
    results: List[Matches] = []
    for core in (element.element_core or []):
        results.append(
            score_items_to_core(
                items=items,
                element_core=core,
                top_k=top_k,
                apply_overspec=bool(apply_overspec),
                include_explain=include_explain,
            )
        )

    # attach results to the same instance
    element.matched_items = results
    return element  # id is unchanged
