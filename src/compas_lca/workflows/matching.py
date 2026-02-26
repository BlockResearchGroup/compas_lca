import json

from dataclasses import dataclass

from enum import Enum

from pathlib import Path

from typing import Any
from typing import Dict
from typing import List
from typing import Iterable
from typing import Iterator
from typing import Tuple
from typing import Optional

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
match inventory item concretes with extremely high strength classes (as it's probably overkill for the element).
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

def _norm_leaf(x):
    if isinstance(x, Enum):
        return x.value  # or x.name, depending on your enums
    return x

def _is_unknown(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return _norm_str(value) == "unknown"
    if isinstance(value, list):
        return any(_norm_str(v) == "unknown" for v in value if isinstance(v, str))
    return False

def _has_value(v: Any) -> bool:
    """True if v is meaningfully specified (not None/unknown/empty)."""
    if _is_unknown(v):
        return False
    if isinstance(v, (list, tuple, set)):
        return len([x for x in v if not _is_unknown(x)]) > 0
    if isinstance(v, str):
        return v.strip() != ""
    return True

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


def _identity_match(item_map: Dict[str, Any], elem_map: Dict[str, Any]) -> bool:
    """
    Identity gate used by eval_filter. Filters out candidates that are not applicable
    in terms of entry_, material_, and component_type. For underdefined elements where
    only the functional type is defined (plaster, insulation), prioritize the subsequent
    inventory items that includes said type in the functional_types list.

    Enforce:
      R1: entry_type equal
      R2: if element.material_type set -> equal (materials)
          if element.component_type set -> equal (components)
      R3: if element has NO material_type BUT has functional_types -> require intersection
    note: item_map/elem_map are DOTMAPS (flattened), so use direct .get().
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
        # INSULATION OVERRIDE: do NOT enforce material_type identity gate
        # If element says "insulation" by function, we only require functional intersection (below).
        insulation_override = _element_is_insulation(elem_map)

        mt_elem = _norm_str(elem_map.get("facet.material_type"))

        if (not insulation_override) and mt_elem and mt_elem != "unknown":
            mt_item = _norm_str(item_map.get("facet.material_type"))
            return mt_item == mt_elem

        # fallback: require intersection if element has functional_types
        elem_funcs = {_norm_str(v) for v in _as_list(elem_map.get("facet.functional_types")) if v}
        if elem_funcs:
            item_funcs = {_norm_str(v) for v in _as_list(item_map.get("facet.functional_types")) if v}
            return bool(elem_funcs & item_funcs)

        return True

    elif et_elem == "component":
        ct_elem = _norm_str(elem_map.get("facet.component_type"))
        if ct_elem and ct_elem != "unknown":
            ct_item = _norm_str(item_map.get("facet.component_type"))
            return ct_item == ct_elem
        return True

    return False

def _element_is_insulation(elem_map: Dict[str, Any]) -> bool:
    funcs = _as_list(elem_map.get("facet.functional_types"))
    funcs_norm = {_norm_str(v) for v in funcs if isinstance(v, str)}
    return "insulation" in funcs_norm

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
        - abs_tol / rel_tol:  tolerance for numeric comparisons (only `approx`)
        - hard_fail:       if True, a mismatch on this clause results in an immediate score of 0.0 for the entire item (used for critical fields)

    Each clause compares a field on the element side against 
    a corresponding field on the item side ('elem_path').
    """
    item_path: str                     # Path to field in the ITEM
    op: str                            # Operator (eq, equals, approx, intersects, etc.)
    value: Any = None
    elem_path: Optional[str] = None    # Path to field in the ELEMENT
    abs_tol: Optional[float] = None    # Absolute tolerance (numeric ops)
    rel_tol: Optional[float] = None    # Relative tolerance (numeric ops)
    hard_fail: bool = False 
    source: str = "unknown"             # "common"|"material_common"|"material_facet"|...

def approx_score(x: Optional[float], target: Optional[float], abs_tol: Optional[float], rel_tol: Optional[float]) -> float:
    """
    For numeric values like U-Value, thermal conductivity, density.
    Tolerances are defined in compas_lca/match_rules.py for each specific 
    quantitative property, as reasonable ranges vary depending on the attribute
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

def eval_clause(
        item_map: Dict[str, Any], # dotmap
        elem_map: Dict[str, Any], # dotmap
        clause: Clause
        ) -> Tuple[Optional[float], str]:
    """
    Evaluate a single matching rule ("clause") between an InventoryItem and an LcaElement core.

    Simplified "weightless, element-driven" semantics:
      - We only evaluate fields that the ELEMENT specifies.
      - If the element's item side value is None/"unknown"/empty (for lists), the clause is skipped → returns (None, ...).
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
          human-readable detail of what was compared (traceability).
    """
    # Retrieve values
    item_value = item_map.get(clause.item_path, None)
    elem_value = clause.value
    if clause.elem_path:
        elem_value = elem_map.get(clause.elem_path, elem_value)

    # If the element value is (None/"unknown"), skip entirely
    if clause.elem_path and _is_unknown(elem_value):
        return None, f"{clause.op} skipped → element unspecified/unknown"

    # Special case for list-type item side where element provided an empty list
    if clause.op == "intersects_other":
        elem_list = _as_list(elem_value)
        if len(elem_list) == 0:
            return None, "intersects(...) → neutral (element empty)"

    # If the element specified a value but the item value is missing → hard mismatch (0.0)
    if item_value is None:
        return 0.0, f"{clause.op} missing on item → 0.00"

    # equals_other: scalar equality (works for strings, numbers, booleans)
    if clause.op == "equals_other":
        a = _norm_leaf(item_value)
        b = _norm_leaf(elem_value)
        score = 1.0 if a == b else 0.0
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
    LcaElement core (`elem_map`) using a weightless, element-driven schema.

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
        The full `MATCH_RULES` structure, referring to specific operations per field

    apply_overspec : bool, default False
        Whether to apply "overspecification" penalties for item fields that the element didn't specify but are present on the item. 
        This allows us to subtly penalize items that are "too specific" compared to the element's requirements, 
        while still keeping the core matching logic clean and focused on the element's specified fields.

    ----------------------------
    Returns
    ----------------------------
    (score, parts) : Tuple[float, List[Dict[str, Any]]]
        score : float
            Final normalized similarity score in [0, 1].

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

    # --- insulation exception for missing material type ----
    insulation_override = (_norm_str(elem_map.get("entry_type")) == "material") and _element_is_insulation(elem_map)

    # --- identity hard gate ---
    if not _identity_match(item_map, elem_map):
        parts = [{
            "path": "identity",
            "op": "gate",
            "score": 0.0,
            "detail": "identity gate failed (entry_type/material_type/component_type/functional_types)",
        }]
        return 0.0, parts
    
    

    # --- clause scoring ---
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

        hard_fail_active = clause.hard_fail

        # If element is insulation, ignore hard_fail for MATERIAL_FACETS-derived clauses
        if insulation_override and clause.source == "material_facet":
            hard_fail_active = False

        if hard_fail_active and float(clause_score) < 1.0:
            parts.append({
                "path": clause.item_path,
                "op": clause.op,
                "score": float(clause_score),
                "detail": detail + " [HARD_FAIL]"
            })
            return 0.0, parts

        n_eval += 1
        sim_sum += float(clause_score)
        parts.append({
            "path": clause.item_path,
            "op": clause.op,
            "score": float(clause_score),
            "detail": detail
        })

    base_score = (sim_sum / n_eval) if n_eval > 0 else 0.0

    # --- overspec penalties ---
    penalty_sum = 0.0
    if apply_overspec and rules_by_group and n_eval > 0:

        # collect all rule dicts we might apply overspec to
        candidate_rules = []
        candidate_rules.extend(rules_by_group.get("common", []))

        et = _norm_str(elem_map.get("entry_type"))
        if et == "material":
            candidate_rules.extend(rules_by_group.get("material_common", []))
            mt = elem_map.get("facet.material_type")
            if mt and mt in MATERIAL_FACETS:
                candidate_rules.extend(MATERIAL_FACETS[mt])

        elif et == "component":
            candidate_rules.extend(rules_by_group.get("component_common", []))
            ct = elem_map.get("facet.component_type")
            if ct and ct in COMPONENT_FACETS:
                candidate_rules.extend(COMPONENT_FACETS[ct])

        for r in candidate_rules:
            overspec = r.get("overspec")
            if not isinstance(overspec, dict):
                continue

            strength = float(overspec.get("strength", 0.0))
            if strength <= 0.0:
                continue

            item_path, elem_path = _normalize_rule_paths(r)

            # element didn't specify this field -> eligible
            elem_v = elem_map.get(elem_path, None) if elem_path else None
            if not _is_unknown(elem_v):
                continue

            # item *did* specify -> penalize
            item_v = item_map.get(item_path, None)
            if not _has_value(item_v):
                continue

            penalty = (strength / n_eval)
            penalty_sum += penalty

            parts.append({
                "path": item_path,
                "op": "overspec",
                "score": -penalty,
                "detail": f"overspec penalty: item has {item_path}={item_v} but element unspecified; strength={strength}"
            })

    final_score = max(0.0, min(1.0, base_score - penalty_sum))
    return final_score, parts

def _normalize_rule_paths(rule: dict) -> Tuple[str, Optional[str]]:
    """
    Return (item_path, elem_path) for a rule.
    """
    if "item_path" in rule or "elem_path" in rule:
        return rule.get("item_path") or rule.get("path"), rule.get("elem_path") or rule.get("path")
    p = rule["path"]
    return p, p

def _add_clause(clauses, element_map, rule, *, source: str):
    if rule.get("ignore") is True:
        return

    item_path, elem_path = _normalize_rule_paths(rule)

    is_field_to_field = rule.get("value") is None
    if is_field_to_field and elem_path:
        item_side = element_map.get(elem_path, None)
        if _is_unknown(item_side):
            return

    # SPECIAL CASE: concrete masonry_unit -> concrete_form is a dealbreaker
    hard_fail = bool(rule.get("hard_fail", False))
    if (
        source in {"material_facet", "material_common"}  # mainly material_facet
        and elem_path == "facet.material_facet.concrete_form"
    ):
        mt = _norm_str(element_map.get("facet.material_type"))
        cf = _norm_str(element_map.get("facet.material_facet.concrete_form"))
        if mt == "concrete" and cf == "masonry_unit":
            hard_fail = True

    clauses.append(Clause(
        item_path=item_path,
        elem_path=elem_path if is_field_to_field else None,
        op=rule["op"],
        value=rule.get("value"),
        abs_tol=rule.get("abs_tol"),
        rel_tol=rule.get("rel_tol"),
        hard_fail=hard_fail,
        source=source,
    ))

def build_clauses(element_map: dict) -> List[Clause]:
    """Create the concrete Clause list from the 3-level rules."""
    clauses: List[Clause] = []

    # hard-fail if element entry_type is unknown
    elem_et = element_map.get("entry_type")
    if elem_et == "unknown":
        return clauses

    # common (always)
    for r in MATCH_RULES["common"]:
        _add_clause(clauses, element_map, r, source="common")

    # specific_common
    if elem_et == "material":
        # material_common
        for r in MATCH_RULES["material_common"]:
            _add_clause(clauses, element_map, r, source="material_common")

        # material facets (skip for insulation override)
        if not _element_is_insulation(element_map):
            mat_type = element_map.get("facet.material_type")
            if mat_type and mat_type in MATERIAL_FACETS:
                for r in MATERIAL_FACETS[mat_type]:
                    _add_clause(clauses, element_map, r, source="material_facet")

    elif elem_et == "component":
        # component_common
        for r in MATCH_RULES["component_common"]:
            _add_clause(clauses, element_map, r, source="component_common")

        # component facets
        comp_type = element_map.get("facet.component_type") or element_map.get("facet.component_facet.component_type")
        if comp_type and comp_type in COMPONENT_FACETS:
            for r in COMPONENT_FACETS[comp_type]:
                _add_clause(clauses, element_map, r, source="component_facet")

    return clauses

# ==================
# SCORING & MATCHING
# ==================

# ----------------------------------------------------------
# Score ONE item against ONE element core's clauses -> Match
# ----------------------------------------------------------

def score_item_to_core(
    item: Any,
    elem_map: Any, # dotmap
    clauses: Any,
    *,
    include_explain: bool = False,
) -> Match:
    
    # Extract item fields
    item_dict = coerce_to_dict(item)
    item_id = item_dict.get("id")
    item_core = item_dict.get("item_core")
    item_map = normalize_core_map(to_dotmap(item_core))
    item_name = item_core.get("name")
    item_meta = item_dict.get("metadata") or {}
    dataset_source = item_meta.get("dataset_source")
    registration_number = item_meta.get("registration_number")

    # Score
    final_score, parts = eval_filter(
        item_map,
        elem_map,
        clauses,
        rules_by_group=MATCH_RULES,
        apply_overspec=True,
    )

    # Return a Match object
    return Match(
        item_id=item_id,
        item_name=item_name,
        dataset_source=dataset_source,
        registration_number=registration_number,
        match_score=float(final_score),
        match_criteria=parts if include_explain else None,
    )

# --------------------------------------------
# Score MANY items against ONE core -> Matches
# --------------------------------------------

def score_items_to_core(
    items: Iterable[Any],
    element_core: Any,
    *,
    top_k: int = 5,  # Default: add items with top 5 score
    include_explain: bool = True,
    score_threshold: float = 0.0,  # New argument
) -> Matches:
    """
    Scores MANY items against ONE core -> Matches
    Only includes matches with score >= score_threshold.
    """
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
            include_explain=include_explain,
        )
        scored.append(match)

    # Filter out matches below the threshold
    scored = [m for m in scored if m.match_score >= score_threshold]

    # Rank remaining matches by descending score
    scored.sort(key=lambda m: -m.match_score)

    # Return top_k matches (after threshold filter)
    return Matches(core_id=core_id, matches=scored[: max(0, int(top_k))])

# -----------------------------------------------------------------------------------
# Score items to each core of an LcaElement, and append matched_items = List[Matches]
# -----------------------------------------------------------------------------------

def score_items_to_element(
    items: Iterable[Any],   # Many InventoryItem instances, or dicts
    element: Any,           # LcaElement instance, or dict
    *,
    top_k: int = 5,  # Default: add items with top 5 score
    include_explain: bool = True,
    score_threshold: float = 0.0,
) -> LcaElement:
    """
    Score a collection of inventory items against all MatchingCores of a given LcaElement.

    For each MatchingCore in `element.element_core`, this function computes similarity
    scores between the core and all provided `items` (typically `InventoryItem`
    instances or their dict representations). It then selects the top-k matches per core,
    filters them by a minimum score threshold, and writes the resulting `Matches`
    objects into `element.matched_items`. The same `LcaElement` (identified by its
    original ID) is returned, now enriched with matching results.

    Parameters
    ----------
    items : Iterable[Any]
        Iterable of candidate inventory records to be matched against the element.
        Each item is expected to be either:
        - an `InventoryItem` instance, or
        - a dict that can be used to construct an `InventoryItem`.
    element : Any
        The building-model element to be matched. Can be:
        - an `LcaElement` instance, or
        - a serialized `LcaElement`.
        The element's `element_core` attribute (a list of MatchingCore objects)
        defines the matching queries.
    top_k : int, optional
        Maximum number of top-scoring matches to retain per MatchingCore.
        Defaults to 5.
    include_explain : bool, optional
        If True, matching results include explanation metadata (e.g., per-attribute
        contributions to the final score). If False, only scores and references are stored.
        Defaults to True.
    score_threshold : float, optional
        Minimum similarity score required for a match to be included. Matches with
        scores below this value are discarded. Defaults to 0.0.

    Returns
    -------
    LcaElement
        The same `LcaElement` (or an instance constructed from the provided dict),
        with its `matched_items` attribute populated by a list of `Matches` objects
        (one per MatchingCore). The element's id is preserved.

    """
    # Ensure model instance
    if not isinstance(element, LcaElement):
        element = LcaElement(**element)  # preserves id from the dict

    results: List[Matches] = []
    for core in (element.element_core or []):
        results.append(
            score_items_to_core(
                items=items,
                element_core=core,
                top_k=top_k,
                include_explain=include_explain,
                score_threshold=score_threshold,
            )
        )

    # Attach results to the same instance
    element.matched_items = results
    return element


# -------------------------------------------------------------------
# Score items to LCA MODEL
# -------------------------------------------------------------------

# INTERNAL HELPERS (kept private)

def _load_inventory_items(directory: Path, pattern: str = "*.json") -> list[dict[str, Any]]:
    """Load all inventory items from directory (recursively), skipping llm_metadata.json, if present"""
    items: list[dict[str, Any]] = []
    for file in directory.rglob(pattern):
        if file.name == "llm_metadata.json":
            continue
        try:
            with file.open("r", encoding="utf-8") as f:
                items.append(json.load(f))
        except Exception as e:
            print(f"[WARN] Could not load inventory file {file}: {e}")

    return items

def _iter_element_files(
    root: Path,
    allowed_element_dirs: set[str],
) -> Iterator[Tuple[Path, dict[str, Any]]]:
    """
    Iterate over all element JSON files under root, skipping root llm_metadata.json
    and only yielding files in allowed first-level subdirectories.
    """
    for file in root.rglob("*.json"):
        if file.name == "llm_metadata.json" and file.parent == root:
            continue

        try:
            rel = file.relative_to(root)
        except ValueError:
            continue

        parts = rel.parts
        if not parts:
            continue

        first_level = parts[0]
        if first_level not in allowed_element_dirs:
            continue

        try:
            with file.open("r", encoding="utf-8") as f:
                yield file, json.load(f)
        except Exception as e:
            print(f"[WARN] Could not load element file {file}: {e}")


# -------------------------------------------------------------------
# EXPORTED FUNCTION
# -------------------------------------------------------------------


INVENTORY_DIR = Path("data/lca_database/oekobaudat_2024-I")
INPUT_ROOT = Path("temp/projects/duplex/03_extracted")
OUTPUT_ROOT = Path("temp/projects/duplex/05_matched")

def match_lca_model(
    *,
    inventory_dir: Path,
    input_root: Path,
    output_root: Path,
    top_k: int = 10,
    include_explain: bool = True,
    score_threshold: float = 0.5,
) -> dict[str, Any]:
    """
    Load inventory items once, score them against each serialized LcaElement JSON
    under input_root, and write matched elements to output_root mirroring structure.
    """

    # Define allowed dirs locally (no mutable default issue)
    allowed_element_dirs: set[str] = {
        "abstract_components",
        "layered_elements",
        "single_materials",
        "undefined_elements",
    }

    inventory_dir = Path(inventory_dir)
    input_root = Path(input_root)
    output_root = Path(output_root)

    items = _load_inventory_items(inventory_dir)
    print("")
    print("Starting matching process...")
    print(f"Loaded {len(items)} inventory items from {inventory_dir}")
    print("")

    processed = 0
    written_paths: list[Path] = []

    for element_path, element in _iter_element_files(input_root, allowed_element_dirs):
        matched_element = score_items_to_element(
            items=items,
            element=element,
            top_k=top_k,
            include_explain=include_explain,
            score_threshold=score_threshold,
        )

        relative = element_path.relative_to(input_root)
        out_path = output_root / relative
        out_path.parent.mkdir(parents=True, exist_ok=True)

        out_path.write_text(
            matched_element.model_dump_json(indent=2, exclude_none=False),
            encoding="utf-8",
        )

        processed += 1
        written_paths.append(out_path)
        print(f"→ Written matched element to {out_path}")

    return {
        "inventory_dir": inventory_dir,
        "input_root": input_root,
        "output_root": output_root,
        "inventory_items_loaded": len(items),
        "elements_processed": processed,
        "outputs_written": written_paths,
    }