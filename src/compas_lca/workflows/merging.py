from typing import List
from typing import Dict
from typing import Any

from compas_lca.model.lca_element import LcaElement
from compas_lca.model.match import Match
from compas_lca.model.match import Matches

from compas_lca.model.match import Matches


# -----------------------------
# Helpers
# -----------------------------

def _element_core_ids(elem: LcaElement) -> List[str]:
    """Return the element's core_id values, in the same order as element.element_core."""
    ids: List[str] = []
    for core in elem.element_core:
        # MatchingCore.core_id is UUID; store as str in Matches
        ids.append(core.core_id)
    return ids

def attach_matches_for_core(
    elem: LcaElement,
    core_id: str,
    scored_items: List[Dict[str, Any]],
    *,
    top_k: int = 20,
    include_explain: bool = True,
) -> LcaElement:
    """
    Attach matches for a single core (by core_id) into elem.matched_items.
    Creates or replaces the Matches entry for that core_id.
    """
    # build top-k Match objects in place
    ranked = sorted(scored_items, key=lambda r: float(r["score"]), reverse=True)[:top_k]
    matches: List[Match] = []
    for row in ranked:
        item = row["item"]
        meta = item.metadata
        if meta is None:
            meta_dict = {}
        else:
            meta_dict = meta.model_dump()
        matches.append(
            Match(
                item_id=str(item.id),
                score=float(row["score"]),
                snapshot=item.snapshot(), #classmethod of InventoryItem
                explain=row.get("explain") if include_explain else None,
                dataset_source=meta_dict.get("dataset_source") or None,
            )
        )
    if elem.matched_items is None:
        elem.matched_items = []

    # replace or append Matches for this core_id
    for cm in elem.matched_items:
        if cm.core_id == core_id:
            cm.matches = matches
            break
    else:
        elem.matched_items.append(Matches(core_id=core_id, matches=matches))

    return elem

def attach_all_core_matches(
    elem: LcaElement,
    scored_items_per_core: Dict[str, List[Dict[str, Any]]],
    *,
    top_k: int = 5,
    include_explain: bool = True,
    ensure_all_cores: bool = False,
) -> LcaElement:
    """
    Attach matches for ALL cores at once, keyed by core_id.

    scored_items_per_core: { "<core_id_str>": [ {item, score, explain?}, ... ], ... }

    If ensure_all_cores=True, the function ensures that every MatchingCore present in
    elem.element_core has a Matches record (with an empty match list if absent from input).
    """
    elem.matched_items = []
    for cid, rows in scored_items_per_core.items():
        attach_matches_for_core(
            elem,
            core_id=cid,
            scored_items=rows,
            top_k=top_k,
            include_explain=include_explain,
        )

    if ensure_all_cores:
        # Create empty buckets for any cores not in the dict
        known = {cm.core_id for cm in (elem.matched_items or [])}
        for cid in _element_core_ids(elem):
            if cid not in known:
                elem.matched_items.append(Matches(core_id=cid, matches=[]))

    return elem


# -----------------------------
# Optional convenience: from a list-of-lists keyed by element order
# -----------------------------

def attach_all_core_matches_ordered(
    elem: LcaElement,
    scored_items_per_core_ordered: List[List[Dict[str, Any]]],
    *,
    top_k: int = 5,
    include_explain: bool = True,
) -> LcaElement:
    """
    If your calling code still produces a list aligned with element.element_core order,
    this adapter converts it to a {core_id: rows} mapping and delegates to the id-based function.
    """
    cid_list = _element_core_ids(elem)
    by_id: Dict[str, List[Dict[str, Any]]] = {}
    for i, rows in enumerate(scored_items_per_core_ordered):
        if i < len(cid_list):
            by_id[cid_list[i]] = rows
    return attach_all_core_matches(
        elem,
        scored_items_per_core=by_id,
        top_k=top_k,
        include_explain=include_explain,
        ensure_all_cores=True,
    )
