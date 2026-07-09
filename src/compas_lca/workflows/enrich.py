import json

import csv

from pathlib import Path

from dataclasses import dataclass
from dataclasses import field

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from compas_lca.helpers import load_json
from compas_lca.helpers import merge_llm_meta

from compas_lca.workflows.extraction import extract_json_with_agent

from compas_lca.enums import ConcreteStrength

from compas_lca.llm.ctx.speculation_context import CONCRETE_STRENGTH_CTX
from compas_lca.llm.ctx.speculation_context import STUD_RATIO_CTX

from compas_lca.model.lca_element import LcaElement

from compas_lca.matching_core.core import MatchingCore

# ===================================================================
# Enrichment CSV template (updated BoQ & Logging)
# ===================================================================

def create_boq_enriched(
    *,
    input_dir: Path,
    enriched_dir: Path,
    input_filename: str = "BoQ_extracted.csv",
    output_filename: str = "BoQ_enriched.csv",
) -> Path:
    """
    Create baseline BoQ_enriched.csv by copying BoQ_extracted.csv and ensuring
    a last column 'Enriched' exists, with empty values for all rows.

    - UTF-8
    - comma-delimited
    - writes all rows

    Returns path to BoQ_enriched.csv
    """
    input_path = Path(input_dir) / input_filename
    if not input_path.exists():
        raise FileNotFoundError(f"Missing BoQ CSV: {input_path}")

    enriched_dir = Path(enriched_dir)
    enriched_dir.mkdir(parents=True, exist_ok=True)
    output_path = enriched_dir / output_filename

    with input_path.open("r", encoding="utf-8", newline="") as f_in, \
         output_path.open("w", encoding="utf-8", newline="") as f_out:

        reader = csv.reader(f_in)
        writer = csv.writer(f_out)

        header = next(reader, None)
        if not header:
            raise ValueError(f"BoQ CSV has no header: {input_path}")

        if "Enriched" in header:
            enriched_idx = header.index("Enriched")
            out_header = [h for h in header if h != "Enriched"] + ["Enriched"]
        else:
            enriched_idx = None
            out_header = header + ["Enriched"]

        writer.writerow(out_header)

        # copy rows
        for row in reader:
            if enriched_idx is None:
                writer.writerow(row + [""])
            else:
                row_no_enriched = row[:enriched_idx] + row[enriched_idx + 1 :]
                writer.writerow(row_no_enriched + [""])

    return output_path


# ===================================================================
# Concrete Strength Class Enrichment
# ===================================================================

# -----------------------------
# Core mutation helpers
# -----------------------------

def _is_concrete_material_lca_element(elem: LcaElement) -> bool:
    cores = elem.element_core or []
    if not cores:
        return False
    if getattr(cores[0], "entry_type", None) != "material":
        return False
    return any(
        getattr(c.facet, "material_type", "").casefold() == "concrete"
        for c in cores
        if getattr(c, "facet", None) is not None
    )


def _apply_strengths_to_cores_by_index(
    cores: List[MatchingCore],
    strength_by_idx_1b: Dict[int, ConcreteStrength],
) -> List[MatchingCore]:
    updated: List[MatchingCore] = []
    for i, c in enumerate(cores):
        n = i + 1  # 1-based
        strength = strength_by_idx_1b.get(n)
        if strength is None:
            updated.append(c)
            continue
        if getattr(getattr(c, "facet", None), "material_type", "").casefold() != "concrete":
            updated.append(c)
            continue
        mf = c.facet.material_facet
        mf2 = mf.model_copy(update={"strength_class": strength})
        facet2 = c.facet.model_copy(update={"material_facet": mf2})
        updated.append(c.model_copy(update={"facet": facet2}))
    return updated


def _enrich_element_by_strengths(elem: LcaElement, strength_by_idx_1b: Dict[int, ConcreteStrength]) -> LcaElement:
    return elem.model_copy(
        update={"element_core": _apply_strengths_to_cores_by_index(elem.element_core or [], strength_by_idx_1b)}
    )

def _concrete_core_indices_1based(elem: LcaElement) -> List[int]:
    idxs: List[int] = []
    for i, c in enumerate(elem.element_core or []):
        if getattr(getattr(c, "facet", None), "material_type", "").casefold() == "concrete":
            idxs.append(i + 1)
    return idxs

# -----------------------------
# IO helpers (by element_eid)
# -----------------------------

def _index_lca_elements_by_eid(extracted_dir: Path) -> Dict[str, Path]:
    """
    Build map: element_eid -> path to serialized LcaElement JSON.
    Looks through all output buckets.
    """
    buckets = ["single_materials", "layered_elements", "abstract_components", "undefined_elements"]
    idx: Dict[str, Path] = {}

    for b in buckets:
        d = extracted_dir / b
        if not d.exists():
            continue
        for p in d.glob("*.json"):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                eid = str((data.get("descriptor") or {}).get("element_eid") or "").strip()
                if eid:
                    idx[eid] = p
            except Exception:
                continue
    return idx


def _load_lca_element(path: Path) -> LcaElement:
    return LcaElement.model_validate_json(path.read_text(encoding="utf-8"))


def _write_lca_element(elem: LcaElement, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(elem.model_dump_json(indent=2), encoding="utf-8")


def _copy_structure_base(extracted_dir: Path, enriched_dir: Path) -> None:
    """
    Copy metadata directory content and create bucket dirs.
    We do not copy element JSONs here; we write enriched ones explicitly.
    """
    (enriched_dir / "metadata").mkdir(parents=True, exist_ok=True)
    for b in ["single_materials", "layered_elements", "abstract_components", "undefined_elements"]:
        (enriched_dir / b).mkdir(parents=True, exist_ok=True)

    # copy existing metadata files if you want
    meta_src = extracted_dir / "metadata"
    meta_dst = enriched_dir / "metadata"
    if meta_src.exists():
        for p in meta_src.glob("*.json"):
            meta_dst.joinpath(p.name).write_text(p.read_text(encoding="utf-8"), encoding="utf-8")


# -----------------------------
# Find representative IFC JSON (preprocessed)
# -----------------------------

def _find_preprocessed_ifc_jsons_for_concrete_cores(
    preprocessed_all_dir: Path,
    eid: str,
    elem: LcaElement,
) -> Dict[int, Path]:
    """
    Return mapping: concrete core index (1-based) -> preprocessed IFC JSON path.

    Rules (same as before, but for each concrete core):
    - single/no_material: <eid>.json (applies to index 1 only, because BoQ uses blank/1)
    - multi_layer: <eid>_L{n}.json (n = 1-based core index)
    - multi_material: <eid>_M{n}.json
    """
    eid = str(eid).strip()
    if not eid:
        return {}

    out: Dict[int, Path] = {}

    # Single material / no_material: only one JSON for whole element.
    single_candidates = [
        preprocessed_all_dir / "elements" / "single_material" / f"{eid}.json",
        preprocessed_all_dir / "elements" / "no_material" / f"{eid}.json",
    ]
    for c in single_candidates:
        if c.exists():
            out[1] = c
            return out

    ml_dir = preprocessed_all_dir / "elements" / "multi_layer" / eid
    mm_dir = preprocessed_all_dir / "elements" / "multi_material" / eid

    for n in _concrete_core_indices_1based(elem):
        # Try multi_layer first
        if ml_dir.exists():
            p = ml_dir / f"{eid}_L{n}.json"
            if p.exists():
                out[n] = p
                continue

        # Try multi_material next
        if mm_dir.exists():
            p = mm_dir / f"{eid}_M{n}.json"
            if p.exists():
                out[n] = p
                continue

        # Cross-try patterns if pipeline is mixed
        if ml_dir.exists():
            p = ml_dir / f"{eid}_M{n}.json"
            if p.exists():
                out[n] = p
                continue
        if mm_dir.exists():
            p = mm_dir / f"{eid}_L{n}.json"
            if p.exists():
                out[n] = p
                continue

    return out

# -----------------------------
# Main runner
# -----------------------------

@dataclass
class ConcreteStrengthEnricher:
    preprocessed_all_dir: Path
    extracted_dir: Path
    enriched_dir: Path
    representatives_map_path: Path

    cache: Dict[Tuple[str, int], Dict[str, Any]] = field(default_factory=dict)
    protocol: List[Dict[str, Any]] = field(default_factory=list)
    llm_meta: Dict[str, Any] = field(default_factory=dict)

    def run(self) -> dict:
        reps_map = json.loads(self.representatives_map_path.read_text(encoding="utf-8"))

        # build index for extracted element JSON files
        element_index = _index_lca_elements_by_eid(self.extracted_dir)

        # Determine which elements are concrete and will be enriched
        total_to_enrich = 0

        for path in element_index.values():
            try:
                elem = _load_lca_element(path)
                if _is_concrete_material_lca_element(elem):
                    total_to_enrich += 1
            except Exception:
                continue

        progress_counter = 0

        # prepare output dir
        _copy_structure_base(self.extracted_dir, self.enriched_dir)

        # ---- BoQ_enriched.csv update (add concrete strength tag) ----
        boq_path = self.enriched_dir / "BoQ_enriched.csv"
        if not boq_path.exists():
            raise FileNotFoundError(
                f"Missing BoQ_enriched.csv: {boq_path} (call create_boq_enriched first)"
            )

        with boq_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            fieldnames = list(reader.fieldnames or [])
            rows = list(reader)

        required = {"EID", "Enriched"}
        missing = sorted(required - set(fieldnames))
        if missing:
            raise ValueError(f"BoQ_enriched.csv missing columns: {missing}")

        # index rows by EID (apply to all layers/materials for that element)
        required = {"EID", "Layer/Material Number", "Enriched"}
        missing = sorted(required - set(fieldnames))
        if missing:
            raise ValueError(f"BoQ_enriched.csv missing columns: {missing}")

        # index rows by (eid, layer_number_normalized)
        boq_index: Dict[Tuple[str, str], List[int]] = {}
        for i, r in enumerate(rows):
            eid = _norm_id(r.get("EID"))
            ln = _norm_layer_no_1based(r.get("Layer/Material Number"))
            boq_index.setdefault((eid, ln), []).append(i)

        def apply_concrete_strengths_to_boq(
            eid: str,
            strength_by_idx_1b: Dict[int, ConcreteStrength],
        ) -> int:
            eidn = _norm_id(eid)
            updated = 0

            for idx_1b, strength in strength_by_idx_1b.items():
                key = (eidn, _norm_layer_no_1based(str(int(idx_1b))))
                hit = boq_index.get(key, [])
                if not hit:
                    avail = sorted({ln for (xe, ln) in boq_index.keys() if xe == eidn})
                    print(f"[MISS] EID={eidn} wanted layer='{idx_1b}' but BoQ has layers={avail}")
                    continue

                token = f"CONCRETE_STRENGTH={strength.value}"
                for row_i in hit:
                    r = rows[row_i]
                    r["Enriched"] = _append_enriched(r.get("Enriched"), token)
                    updated += 1

            return updated


        enriched_eids: set[str] = set()

        for rep_eid, entry in reps_map.items():
            rep_eid_str = str(rep_eid).strip()
            rep_path = element_index.get(rep_eid_str)
            if not rep_path:
                continue

            rep_elem = _load_lca_element(rep_path)
            if not _is_concrete_material_lca_element(rep_elem):
                self._write_same_bucket(rep_elem, rep_path)
                continue

            strengths = self._infer_strengths_for_rep(rep_eid_str, rep_elem)
            strength_by_idx = {i: s for i, (s, _exp) in strengths.items()}
            apply_concrete_strengths_to_boq(rep_eid_str, strength_by_idx)
            rep_elem_enriched = _enrich_element_by_strengths(rep_elem, strength_by_idx)
            self._write_same_bucket(rep_elem_enriched, rep_path)
            enriched_eids.add(rep_eid_str)

            progress_counter += 1
            strength_summary = ", ".join(
                f"{idx}:{st.value}" for idx, (st, _exp) in sorted(strengths.items())
            )

            print(
                f"[{progress_counter}/{total_to_enrich}] "
                f"Enriched representative: {rep_elem.descriptor.element_name} "
                f"(EID={rep_eid_str}) -> {strength_summary}"
            )

            for idx_1b, (strength, explanation) in strengths.items():
                self.protocol.append({
                    "representative_eid": rep_eid_str,
                    "representative_name": rep_elem.descriptor.element_name,
                    "object_type": rep_elem.descriptor.object_type,
                    "core_index_1based": idx_1b,
                    "strength_class": strength.value,
                    "explanation": explanation,
                    "members_count": len(entry.get("members") or []),
                })

            # members
            for m in (entry.get("members") or []):
                me = str((m or {}).get("eid") or "").strip()
                if not me or me == rep_eid_str:
                    continue
                m_path = element_index.get(me)
                if not m_path:
                    continue
                m_elem = _load_lca_element(m_path)
                # only apply if member actually has concrete material cores
                if _is_concrete_material_lca_element(m_elem):
                    m_elem = _enrich_element_by_strengths(m_elem, strength_by_idx)
                    apply_concrete_strengths_to_boq(me, strength_by_idx)
                    progress_counter += 1
                    strength_summary = ", ".join(
                        f"{idx}:{st.value}" for idx, (st, _exp) in sorted(strengths.items())
                    )

                    print(
                        f"[{progress_counter}/{total_to_enrich}] "
                        f"Enriched representative: {rep_elem.descriptor.element_name} "
                        f"(EID={rep_eid_str}) -> {strength_summary}"
                    )

                self._write_same_bucket(m_elem, m_path)

        # write any elements not touched at all (copy as-is)
        for eid, src_path in element_index.items():
            if eid in enriched_eids:
                continue
            elem = _load_lca_element(src_path)
            self._write_same_bucket(elem, src_path)

        # ---- rewrite BoQ_enriched.csv with CONCRETE_STRENGTH tags ----
        with boq_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        # metadata outputs
        self._write_protocol()

        return self.llm_meta

    def _infer_strengths_for_rep(
        self,
        rep_eid: str,
        rep_elem: LcaElement,
    ) -> Dict[int, Tuple[ConcreteStrength, str]]:
        """
        Returns: idx_1b -> (strength, explanation)
        """
        paths_by_idx = _find_preprocessed_ifc_jsons_for_concrete_cores(self.preprocessed_all_dir, rep_eid, rep_elem)

        results: Dict[int, Tuple[ConcreteStrength, str]] = {}

        for idx_1b in _concrete_core_indices_1based(rep_elem):
            ck = (rep_eid, idx_1b)
            if ck in self.cache:
                results[idx_1b] = (self.cache[ck]["strength"], self.cache[ck]["explanation"])
                continue

            ifc_path = paths_by_idx.get(idx_1b)
            if ifc_path is None:
                strength = ConcreteStrength.C30_37
                explanation = f"No IFC JSON found for concrete core index {idx_1b}; assigned conservative default."
                self.cache[ck] = {"strength": strength, "explanation": explanation, "meta": {}, "ifc_path": None}
                results[idx_1b] = (strength, explanation)
                continue

            print("")
            print(f"Using input (core {idx_1b}): {ifc_path}")
            print("")

            rep_ifc_json = load_json(ifc_path)
            out, meta = extract_json_with_agent(input_json=rep_ifc_json, context=CONCRETE_STRENGTH_CTX)
            self.llm_meta = merge_llm_meta(self.llm_meta, meta)

            strength = ConcreteStrength(str(out["strength_class"]))
            explanation = str(out.get("explanation") or "").strip()

            self.cache[ck] = {"strength": strength, "explanation": explanation, "meta": meta, "ifc_path": str(ifc_path)}
            results[idx_1b] = (strength, explanation)

        return results

    def _write_same_bucket(self, elem: LcaElement, src_path: Path) -> None:
        # preserve bucket name by mirroring relative path from extracted_dir
        rel = src_path.relative_to(self.extracted_dir)
        out_path = self.enriched_dir / rel
        _write_lca_element(elem, out_path)

    def _write_protocol(self) -> None:
        meta_dir = self.enriched_dir / "metadata"
        meta_dir.mkdir(parents=True, exist_ok=True)
        protocol_path = meta_dir / "LOG_concrete_strength_enrichment.json"
        payload = {
            "count": len(self.protocol),
            "items": self.protocol,
        }
        protocol_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

def enrich_concrete_strength(
    *,
    preprocessed_all_dir: Path,
    extracted_dir: Path,
    enriched_dir: Path,
) -> None:
    reps_map = extracted_dir / "metadata" / "representatives_map.json"
    if not reps_map.exists():
        raise FileNotFoundError(f"Missing representatives map: {reps_map}")

    enricher = ConcreteStrengthEnricher(
        preprocessed_all_dir=preprocessed_all_dir,
        extracted_dir=extracted_dir,
        enriched_dir=enriched_dir,
        representatives_map_path=reps_map,
    )
    llm_meta = enricher.run()
    print("")
    return llm_meta or {}


# ===================================================================
# Stud Ratio Enrichment (BoQ CSV)
# ===================================================================

# -----------------------------
# Core detection helpers
# -----------------------------

def _as_token(x: Any) -> str:
    if x is None:
        return ""
    # Enum -> use value if available
    v = getattr(x, "value", None)
    if v is not None:
        return str(v).strip().casefold()
    return str(x).strip().casefold()

def _is_stud_layer_core(core: MatchingCore) -> bool:
    if getattr(core, "entry_type", None) != "material":
        return False
    facet = getattr(core, "facet", None)
    if facet is None:
        return False
    fts = getattr(facet, "functional_types", None) or []
    return any(_as_token(x) == "stud_layer" for x in fts)


def _has_any_stud_layer(elem: LcaElement) -> bool:
    cores = elem.element_core or []
    return any(_is_stud_layer_core(c) for c in cores)


def _first_stud_layer_index_1based(elem: LcaElement) -> Optional[int]:
    """
    Deterministic: first stud_layer core by element_core order.
    Returns 1-based index (to match your file naming & BoQ Layer/Material Number).
    """
    cores = elem.element_core or []
    for i, c in enumerate(cores):
        if _is_stud_layer_core(c):
            return i + 1
    return None

def _stud_layer_indices_1based(elem: LcaElement) -> list[int]:
    cores = elem.element_core or []
    out: list[int] = []
    for i, c in enumerate(cores):
        if _is_stud_layer_core(c):
            out.append(i + 1)
    return out

# -----------------------------
# IO helpers (by element_eid)
# -----------------------------

def _index_lca_elements_by_eid(extracted_dir: Path) -> Dict[str, Path]:
    buckets = ["single_materials", "layered_elements", "abstract_components", "undefined_elements"]
    idx: Dict[str, Path] = {}
    for b in buckets:
        d = extracted_dir / b
        if not d.exists():
            continue
        for p in d.glob("*.json"):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                eid = str((data.get("descriptor") or {}).get("element_eid") or "").strip()
                if eid:
                    idx[eid] = p
            except Exception:
                continue
    return idx


def _load_lca_element(path: Path) -> LcaElement:
    return LcaElement.model_validate_json(path.read_text(encoding="utf-8"))


# -----------------------------
# Find representative IFC JSON (preprocessed)
# -----------------------------

def _find_preprocessed_ifc_json_for_stud_layer(
    preprocessed_all_dir: Path,
    eid: str,
    rep_elem: LcaElement,
) -> Optional[Path]:
    """
    Locate representative preprocessed IFC JSON by EID.

    Rules:
    - single/no_material: <eid>.json
    - multi_layer: <eid>_L{n}.json where n is 1-based index into rep_elem.element_core
    - multi_material: <eid>_M{n}.json where n is 1-based index into rep_elem.element_core

    We pick the FIRST stud_layer core we find.
    """
    eid = str(eid).strip()
    if not eid:
        return None

    # fast paths
    candidates = [
        preprocessed_all_dir / "elements" / "single_material" / f"{eid}.json",
        preprocessed_all_dir / "elements" / "no_material" / f"{eid}.json",
    ]
    for c in candidates:
        if c.exists():
            return c

    ml_dir = preprocessed_all_dir / "elements" / "multi_layer" / eid
    mm_dir = preprocessed_all_dir / "elements" / "multi_material" / eid

    idx_1b = _first_stud_layer_index_1based(rep_elem)
    if idx_1b is None:
        return None

    n = idx_1b

    # Try multi_layer then multi_material
    if ml_dir.exists():
        p = ml_dir / f"{eid}_L{n}.json"
        if p.exists():
            return p
    if mm_dir.exists():
        p = mm_dir / f"{eid}_M{n}.json"
        if p.exists():
            return p

    # Cross-try patterns if pipeline is mixed
    if ml_dir.exists():
        p = ml_dir / f"{eid}_M{n}.json"
        if p.exists():
            return p
    if mm_dir.exists():
        p = mm_dir / f"{eid}_L{n}.json"
        if p.exists():
            return p

    return None

# -----------------------------
# Minimal CSV helpers
# -----------------------------


def _available_layers_for_eid(boq_index, eid: str) -> list[str]:
    e = _norm_id(eid)
    return sorted({ln for (xe, ln) in boq_index.keys() if xe == e})

def _norm(x: Any) -> str:
    if x is None:
        return ""
    s = str(x).strip()
    return "" if s.lower() in {"nan", "none", "null"} else s

def _norm_id(x: Any) -> str:
    s = _norm(x)
    if not s:
        return ""
    if s.endswith(".0"):
        s = s[:-2]
    return s

def _norm_layer_no_1based(x: Any) -> str:
    s = _norm_id(x)
    if not s:
        return "1"
    if s.endswith(".0"):
        s = s[:-2]
    return s

def _parse_float(x: Any) -> Optional[float]:
    s = _norm(x)
    if not s:
        return None
    s = s.replace(" ", "")
    if "," in s and "." not in s:
        s = s.replace(",", ".")
    elif "," in s and "." in s:
        s = s.replace(",", "")
    try:
        return float(s)
    except Exception:
        return None


def _fmt_float(v: float) -> str:
    return f"{v:.6f}".rstrip("0").rstrip(".")


def _layer_key(layer_idx_1b: Optional[int]) -> str:
    return "" if layer_idx_1b is None else str(int(layer_idx_1b))

def _append_enriched(existing: str, token: str) -> str:
    existing = _norm(existing)
    token = _norm(token)
    if not token:
        return existing
    key = token.split("=", 1)[0] if "=" in token else token
    parts = [p.strip() for p in existing.split(";") if p.strip()] if existing else []
    parts = [p for p in parts if not p.startswith(f"{key}=") and p != key]
    parts.append(token)
    return "; ".join(parts)

# -----------------------------
# Main runner
# -----------------------------

@dataclass
class StudRatioEnricher:
    preprocessed_all_dir: Path
    extracted_dir: Path
    enriched_dir: Path
    representatives_map_path: Path

    cache: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # rep_eid -> {"ratio": float, "explanation": str, "meta": dict, "layer_index": Optional[int]}
    protocol: List[Dict[str, Any]] = field(default_factory=list)
    llm_meta: Dict[str, Any] = field(default_factory=dict)

    def run(self) -> dict:
        reps_map = json.loads(self.representatives_map_path.read_text(encoding="utf-8"))

        element_index = _index_lca_elements_by_eid(self.extracted_dir)

        boq_path = self.enriched_dir / "BoQ_enriched.csv"
        if not boq_path.exists():
            raise FileNotFoundError(
                f"Missing BoQ_enriched.csv: {boq_path} (call create_boq_enriched first)"
            )

        with boq_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            fieldnames = list(reader.fieldnames or [])
            rows = list(reader)

        required = {"EID", "Layer/Material Number", "Area [m2]", "Volume [m3]", "Enriched"}
        missing = sorted(required - set(fieldnames))
        if missing:
            raise ValueError(f"BoQ_enriched.csv missing columns: {missing}")

        boq_index: Dict[Tuple[str, str], List[int]] = {}
        for i, r in enumerate(rows):
            eid = _norm_id(r.get("EID"))
            ln = _norm_layer_no_1based(r.get("Layer/Material Number"))
            boq_index.setdefault((eid, ln), []).append(i)

        # -------------------------------------------------------
        # Mirror ConcreteStrengthEnricher: pre-count total targets
        # -------------------------------------------------------
        total_to_enrich = 0
        for path in element_index.values():
            try:
                elem = _load_lca_element(path)
                if _has_any_stud_layer(elem):
                    total_to_enrich += 1
            except Exception:
                continue

        progress_counter = 0
        enriched_eids: set[str] = set()

        updated_rows = 0

        for rep_eid, entry in reps_map.items():
            
            rep_eid = _norm(rep_eid)
            rep_path = element_index.get(rep_eid)
            if not rep_path:
                continue

            rep_elem = _load_lca_element(rep_path)

            rep_has = _has_any_stud_layer(rep_elem)

            if not _has_any_stud_layer(rep_elem):
                continue

            if not rep_has:
                fts = []
                for c in (rep_elem.element_core or []):
                    facet = getattr(c, "facet", None)
                    if facet:
                        fts.append(getattr(facet, "functional_types", None))
                print(f"[DEBUG] rep {rep_eid} functional_types={fts}")
                continue

            ratio, explanation, rep_layer_idx_1b = self._infer_for_rep(rep_eid, rep_elem)

            for n in _stud_layer_indices_1based(rep_elem):
                updated_rows += self._apply_ratio(rows, boq_index, rep_eid, str(n), ratio)

            if rep_eid not in enriched_eids:
                enriched_eids.add(rep_eid)
                progress_counter += 1
                print(
                    f"[{progress_counter}/{total_to_enrich}] "
                    f"Enriched representative: {rep_elem.descriptor.element_name} "
                    f"(EID={rep_eid}) -> {ratio}"
                )

            self.protocol.append({
                "representative_eid": rep_eid,
                "representative_name": rep_elem.descriptor.element_name,
                "object_type": rep_elem.descriptor.object_type,
                "stud_ratio": ratio,
                "layer_index_1based": rep_layer_idx_1b,
                "explanation": explanation,
                "members_count": len(entry.get("members") or []),
            })

            # members
            for m in (entry.get("members") or []):
                me = _norm_id((m or {}).get("eid"))
                if not me or me == rep_eid:
                    continue
                m_path = element_index.get(me)
                if not m_path:
                    continue
                m_elem = _load_lca_element(m_path)
                if not _has_any_stud_layer(m_elem):
                    continue

                member_indices = _stud_layer_indices_1based(m_elem)
                for n in member_indices:
                    updated_rows += self._apply_ratio(rows, boq_index, me, str(n), ratio)

                if me not in enriched_eids:
                    enriched_eids.add(me)
                    progress_counter += 1
                    print(
                        f"[{progress_counter}/{total_to_enrich}] "
                        f"Enriched member: {m_elem.descriptor.element_name} "
                        f"(EID={me}) -> {ratio}"
                    )

        # rewrite the same BoQ_enriched.csv
        self.enriched_dir.mkdir(parents=True, exist_ok=True)
        with boq_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        # write protocol + llm_meta
        meta_dir = self.enriched_dir / "metadata"
        meta_dir.mkdir(parents=True, exist_ok=True)

        (meta_dir / "LOG_stud_ratio_enrichment.json").write_text(
            json.dumps({"count": len(self.protocol), "items": self.protocol}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"Stud ratio enrichment done. Updated rows: {updated_rows}. BoQ updated: {boq_path}")
        return self.llm_meta
        

    def _infer_for_rep(self, rep_eid: str, rep_elem: LcaElement) -> Tuple[float, str, Optional[int]]:
        if rep_eid in self.cache:
            c = self.cache[rep_eid]
            return float(c["ratio"]), str(c["explanation"]), c.get("layer_index")

        layer_idx_1b = _first_stud_layer_index_1based(rep_elem)

        ifc_path = _find_preprocessed_ifc_json_for_stud_layer(self.preprocessed_all_dir, rep_eid, rep_elem)
        if ifc_path is None:
            ratio = 0.15
            explanation = "Representative IFC JSON not found; assigned typical stud-layer ratio default."
            self.cache[rep_eid] = {"ratio": ratio, "explanation": explanation, "meta": {}, "layer_index": layer_idx_1b}
            return ratio, explanation, layer_idx_1b

        rep_ifc_json = load_json(ifc_path)
        out, meta = extract_json_with_agent(input_json=rep_ifc_json, context=STUD_RATIO_CTX)
        self.llm_meta = merge_llm_meta(self.llm_meta, meta)

        ratio_val = out.get("stud_ratio", out.get("ratio"))
        if ratio_val is None:
            ratio = 0.15
            explanation = "LLM output missing stud_ratio; assigned typical stud-layer ratio default."
        else:
            ratio = float(ratio_val)
            explanation = _norm(out.get("explanation"))

        self.cache[rep_eid] = {"ratio": ratio, "explanation": explanation, "meta": meta, "layer_index": layer_idx_1b}
        return ratio, explanation, layer_idx_1b

    def _apply_ratio(
        self,
        rows: List[Dict[str, Any]],
        boq_index: Dict[Tuple[str, str], List[int]],
        eid: str,
        layer_str: str,
        ratio: float,
    ) -> int:
        """
        Apply ratio to (eid, layer_str). If no exact match and layer_str != "",
        """
        key = (_norm_id(eid), _norm_id(layer_str))
        hit = boq_index.get(key, [])
        updated = 0

        if not hit:
            avail = _available_layers_for_eid(boq_index, eid)
            print(f"[MISS] EID={_norm_id(eid)} wanted layer='{layer_str}' but BoQ has layers={avail}")
            return 0

        for idx in hit:
            r = rows[idx]
            a0 = _parse_float(r.get("Area [m2]"))
            v0 = _parse_float(r.get("Volume [m3]"))

            if a0 is not None:
                r["Area [m2]"] = _fmt_float(a0 * ratio)
            if v0 is not None:
                r["Volume [m3]"] = _fmt_float(v0 * ratio)

            r["Enriched"] = _append_enriched(
                r.get("Enriched"),
                f"STUD_LAYER_RATIO={_fmt_float(ratio)}"
            )
            updated += 1

        return updated


def enrich_stud_ratio(
    *,
    preprocessed_all_dir: Path,
    extracted_dir: Path,
    enriched_dir: Path,
) -> dict:
    reps_map = extracted_dir / "metadata" / "representatives_map.json"
    if not reps_map.exists():
        raise FileNotFoundError(f"Missing representatives map: {reps_map}")

    enricher = StudRatioEnricher(
        preprocessed_all_dir=preprocessed_all_dir,
        extracted_dir=extracted_dir,
        enriched_dir=enriched_dir,
        representatives_map_path=reps_map,
    )
    llm_meta = enricher.run()
    return llm_meta or {}



