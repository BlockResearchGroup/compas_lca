import csv
import json
import re
from pathlib import Path
from typing import Any
from typing import Dict
from typing import Optional

import pandas as pd

# ------------------------
# BOQ PREPROCESSED (BOQ 01)
# ------------------------

_LAYER_RE = re.compile(r"_L(\d+)\.json$", re.IGNORECASE)
_MATERIAL_RE = re.compile(r"_M(\d+)\.json$", re.IGNORECASE)


def _layer_from_path(p: Path) -> int | None:
    m = _LAYER_RE.search(p.name)
    return int(m.group(1)) if m else None


def _material_from_path(p: Path) -> int | None:
    m = _MATERIAL_RE.search(p.name)
    return int(m.group(1)) if m else None


def process_ifc_model_boq(output_parent: Path | str) -> None:
    output_parent = Path(output_parent)
    processed_directory = output_parent

    if not processed_directory.exists() or not processed_directory.is_dir():
        raise FileNotFoundError(f"Required directory not found: {processed_directory.resolve()}\nRun the IFC preprocessing step first (process_ifc_model).")

    # Directories (as Path objects)
    single_material_dir = processed_directory / "elements" / "single_material"
    multi_layer_dir = processed_directory / "elements" / "multi_layer"
    multi_material_dir = processed_directory / "elements" / "multi_material"
    no_material_dir = processed_directory / "elements" / "no_material"

    boq_rows_all: list[dict] = []
    boq_rows_dissected: list[dict] = []

    # Iterate over single material source files
    if single_material_dir.exists() and single_material_dir.is_dir():
        for source_path in single_material_dir.glob("*.json"):
            try:
                with source_path.open("r", encoding="utf-8") as file:
                    data = json.load(file)

                metadata = data.get("metadata", {})
                material = data.get("material_data", {})
                quantities = data.get("quantities", {})

                # material conditionals
                if material.get("entity") in ("IfcMaterialLayerSetUsage", "IfcMaterialLayerSet"):
                    layers = material.get("material_layers") or []
                    material_d = layers[0] if layers else {}
                    material_name = material_d.get("material_name", None)
                    thickness = material_d.get("thickness", None)
                elif material.get("entity") == ("IfcMaterialList"):
                    materials = material.get("materials") or []
                    material_d = materials[0] if materials else {}
                    material_name = material_d.get("material_name", None)
                    thickness = None
                else:
                    material_name = material.get("material_name")
                    thickness = None

                boq_rows_all.append(
                    {
                        "EID": metadata.get("eid", None),
                        "GlobalId": metadata.get("global_id", None),
                        "Name": metadata.get("name", None),
                        "Entity": metadata.get("entity", None),
                        "Object Type": metadata.get("object_type", None),
                        "Material Type": "single_material",
                        "Material Entity": material.get("entity", None),
                        "Material Name(s)": material_name,
                        "Thickness": thickness,
                        "Length": quantities.get("length", None),
                        "Width": quantities.get("width", None),
                        "Height": quantities.get("height", None),
                        "Depth": quantities.get("depth", None),
                        "LENGTHUNIT": quantities.get("LENGTHUNIT"),
                        "Net Area": quantities.get("net_area", None),
                        "Net Side Area": quantities.get("net_side_area", None),
                        "Net Footprint Area": quantities.get("net_footprint_area", None),
                        "Net Surface Area": quantities.get("net_surface_area", None),
                        "Cross-sectional Area": quantities.get("cross_section_area", None),
                        "OBB Largest Area": quantities.get("compas_obb_largest_area", None),
                        "AREAUNIT": quantities.get("AREAUNIT"),
                        "Net Volume": quantities.get("net_volume", None),
                        "BRep Volume": quantities.get("compas_brep_volume", None),
                        "VOLUMEUNIT": quantities.get("VOLUMEUNIT"),
                    }
                )

                boq_rows_dissected.append(
                    {
                        "EID": metadata.get("eid", None),
                        "GlobalId": metadata.get("global_id", None),
                        "Name": metadata.get("name", None),
                        "Layer/Material Number": None,
                        "Entity": metadata.get("entity", None),
                        "Object Type": metadata.get("object_type", None),
                        "Material Type": "single_material",
                        "Material Entity": material.get("entity", None),
                        "Material Name": material_name,
                        "Thickness": thickness,
                        "Length": quantities.get("length", None),
                        "Width": quantities.get("width", None),
                        "Height": quantities.get("height", None),
                        "Depth": quantities.get("depth", None),
                        "LENGTHUNIT": quantities.get("LENGTHUNIT"),
                        "Net Area": quantities.get("net_area", None),
                        "Net Side Area": quantities.get("net_side_area", None),
                        "Net Footprint Area": quantities.get("net_footprint_area", None),
                        "Net Surface Area": quantities.get("net_surface_area", None),
                        "Cross-sectional Area": quantities.get("cross_section_area", None),
                        "OBB Largest Area": quantities.get("compas_obb_largest_area", None),
                        "AREAUNIT": quantities.get("AREAUNIT"),
                        "Net Volume": quantities.get("net_volume", None),
                        "BRep Volume": quantities.get("compas_brep_volume", None),
                        "VOLUMEUNIT": quantities.get("VOLUMEUNIT"),
                    }
                )

            except Exception as e:
                print(f"[WARN] Skipping {source_path.name}: {e}")

    if multi_layer_dir.exists() and multi_layer_dir.is_dir():
        for element_dir in multi_layer_dir.iterdir():
            if not element_dir.is_dir():
                continue

            eid = element_dir.name

            # --- aggregate file ---
            source_path = element_dir / f"{eid}.json"
            if not source_path.exists():
                continue

            try:
                with source_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)

                metadata = data.get("metadata", {}) or {}
                material = data.get("material_data", {}) or {}
                quantities = data.get("quantities", {}) or {}
                layers = material.get("material_layers") or []

                material_names = [layer.get("material_name") for layer in layers if isinstance(layer, dict) and layer.get("material_name")]
                material_name = " | ".join(material_names) if material_names else None

                thickness = sum((layer.get("thickness") or 0.0) for layer in layers if isinstance(layer, dict))

                boq_rows_all.append(
                    {
                        "EID": metadata.get("eid"),
                        "GlobalId": metadata.get("global_id"),
                        "Name": metadata.get("name"),
                        "Entity": metadata.get("entity"),
                        "Object Type": metadata.get("object_type"),
                        "Material Type": "multi_layer",
                        "Material Entity": material.get("entity"),
                        "Material Name(s)": material_name,
                        "Thickness": thickness,
                        "Length": quantities.get("length", None),
                        "Width": quantities.get("width", None),
                        "Height": quantities.get("height", None),
                        "Depth": quantities.get("depth", None),
                        "LENGTHUNIT": quantities.get("LENGTHUNIT"),
                        "Net Area": quantities.get("net_area", None),
                        "Net Side Area": quantities.get("net_side_area", None),
                        "Net Footprint Area": quantities.get("net_footprint_area", None),
                        "Net Surface Area": quantities.get("net_surface_area", None),
                        "Cross-sectional Area": quantities.get("cross_section_area", None),
                        "OBB Largest Area": quantities.get("compas_obb_largest_area", None),
                        "AREAUNIT": quantities.get("AREAUNIT"),
                        "Net Volume": quantities.get("net_volume", None),
                        "BRep Volume": quantities.get("compas_brep_volume", None),
                        "VOLUMEUNIT": quantities.get("VOLUMEUNIT"),
                    }
                )

                # --- nested loop over per-layer files ---
                layer_paths = list(element_dir.glob(f"{eid}_L*.json"))

                # sort by L-number so output is stable
                layer_paths.sort(key=lambda p: (_layer_from_path(p) is None, _layer_from_path(p) or 0))

                for lp in layer_paths:
                    try:
                        layer_no = _layer_from_path(lp)

                        with lp.open("r", encoding="utf-8") as f:
                            layer_data = json.load(f)

                        target_layer = layer_data.get("target_layer", {}) or {}

                        boq_rows_dissected.append(
                            {
                                "EID": metadata.get("eid"),
                                "GlobalId": metadata.get("global_id"),
                                "Name": metadata.get("name"),
                                "Layer/Material Number": layer_no,
                                "Entity": metadata.get("entity"),
                                "Object Type": metadata.get("object_type"),
                                "Material Type": "multi_layer",
                                "Material Entity": material.get("entity"),
                                "Material Name": target_layer.get("material_name"),
                                "Thickness": target_layer.get("thickness"),
                                "Length": None,
                                "Width": None,
                                "Height": None,
                                "Depth": None,
                                "LENGTHUNIT": quantities.get("LENGTHUNIT"),
                                "Net Area": None,
                                "Net Side Area": None,
                                "Net Footprint Area": None,
                                "Net Surface Area": None,
                                "Cross-sectional Area": None,
                                "OBB Largest Area": None,
                                "AREAUNIT": quantities.get("AREAUNIT"),
                                "Net Volume": None,
                                "BRep Volume": None,
                                "VOLUMEUNIT": quantities.get("VOLUMEUNIT"),
                            }
                        )

                    except Exception as e:
                        print(f"[WARN] Skipping layer file {lp}: {e}")

            except Exception as e:
                print(f"[WARN] Skipping {source_path}: {e}")

    if multi_material_dir.exists() and multi_material_dir.is_dir():
        for element_dir in multi_material_dir.iterdir():
            if not element_dir.is_dir():
                continue

            eid = element_dir.name

            # Only pick the JSON whose filename matches the directory name
            source_path = element_dir / f"{element_dir.name}.json"
            if not source_path.exists():
                continue

            try:
                with source_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)

                metadata = data.get("metadata", {})
                material = data.get("material_data", {})
                quantities = data.get("quantities", {})
                materials = material.get("materials") or []

                # Collect all material names
                material_names = [m.get("material_name") for m in materials if isinstance(m, dict) and m.get("material_name")]

                # Join into one CSV-safe string
                material_name = " | ".join(material_names) if material_names else None

                boq_rows_all.append(
                    {
                        "EID": metadata.get("eid", None),
                        "GlobalId": metadata.get("global_id", None),
                        "Name": metadata.get("name", None),
                        "Entity": metadata.get("entity", None),
                        "Object Type": metadata.get("object_type", None),
                        "Material Type": "multi_material",
                        "Material Entity": material.get("entity", None),
                        "Material Name(s)": material_name,
                        "Thickness": None,
                        "Length": quantities.get("length", None),
                        "Width": quantities.get("width", None),
                        "Height": quantities.get("height", None),
                        "Depth": quantities.get("depth", None),
                        "LENGTHUNIT": quantities.get("LENGTHUNIT"),
                        "Net Area": quantities.get("net_area", None),
                        "Net Side Area": quantities.get("net_side_area", None),
                        "Net Footprint Area": quantities.get("net_footprint_area", None),
                        "Net Surface Area": quantities.get("net_surface_area", None),
                        "Cross-sectional Area": quantities.get("cross_section_area", None),
                        "OBB Largest Area": quantities.get("compas_obb_largest_area", None),
                        "AREAUNIT": quantities.get("AREAUNIT"),
                        "Net Volume": quantities.get("net_volume", None),
                        "BRep Volume": quantities.get("compas_brep_volume", None),
                        "VOLUMEUNIT": quantities.get("VOLUMEUNIT"),
                    }
                )

                # --- nested loop over per-material files ---
                material_paths = list(element_dir.glob(f"{eid}_M*.json"))

                # sort by M-number so output is stable
                material_paths.sort(key=lambda p: (_material_from_path(p) is None, _material_from_path(p) or 0))

                for mp in material_paths:
                    try:
                        material_no = _material_from_path(mp)

                        with mp.open("r", encoding="utf-8") as f:
                            material_data = json.load(f)

                        target_material = material_data.get("target_material", {}) or {}

                        boq_rows_dissected.append(
                            {
                                "EID": metadata.get("eid"),
                                "GlobalId": metadata.get("global_id"),
                                "Name": metadata.get("name"),
                                "Layer/Material Number": material_no,
                                "Entity": metadata.get("entity"),
                                "Object Type": metadata.get("object_type"),
                                "Material Type": "multi_material",
                                "Material Entity": material.get("entity"),
                                "Material Name": target_material.get("material_name"),
                                "Thickness": None,
                                "Length": None,
                                "Width": None,
                                "Height": None,
                                "Depth": None,
                                "LENGTHUNIT": quantities.get("LENGTHUNIT"),
                                "Net Area": None,
                                "Net Side Area": None,
                                "Net Footprint Area": None,
                                "Net Surface Area": None,
                                "Cross-sectional Area": None,
                                "OBB Largest Area": None,
                                "AREAUNIT": quantities.get("AREAUNIT"),
                                "Net Volume": None,
                                "BRep Volume": None,
                                "VOLUMEUNIT": quantities.get("VOLUMEUNIT"),
                            }
                        )

                    except Exception as e:
                        print(f"[WARN] Skipping layer file {mp}: {e}")

            except Exception as e:
                print(f"[WARN] Skipping {source_path}: {e}")

    # Iterate over no-material source files
    if no_material_dir.exists() and no_material_dir.is_dir():
        for source_path in no_material_dir.glob("*.json"):
            try:
                with source_path.open("r", encoding="utf-8") as file:
                    data = json.load(file)

                metadata = data.get("metadata", {}) or {}
                quantities = data.get("quantities", {}) or {}

                boq_rows_all.append(
                    {
                        "EID": metadata.get("eid", None),
                        "GlobalId": metadata.get("global_id", None),
                        "Name": metadata.get("name", None),
                        "Entity": metadata.get("entity", None),
                        "Object Type": metadata.get("object_type", None),
                        "Material Type": "no_material",
                        "Material Entity": None,
                        "Material Name(s)": None,
                        "Thickness": None,
                        "Length": quantities.get("length", None),
                        "Width": quantities.get("width", None),
                        "Height": quantities.get("height", None),
                        "Depth": quantities.get("depth", None),
                        "LENGTHUNIT": quantities.get("LENGTHUNIT"),
                        "Net Area": quantities.get("net_area", None),
                        "Net Side Area": quantities.get("net_side_area", None),
                        "Net Footprint Area": quantities.get("net_footprint_area", None),
                        "Net Surface Area": quantities.get("net_surface_area", None),
                        "Cross-sectional Area": quantities.get("cross_section_area", None),
                        "OBB Largest Area": quantities.get("compas_obb_largest_area", None),
                        "AREAUNIT": quantities.get("AREAUNIT"),
                        "Net Volume": quantities.get("net_volume", None),
                        "BRep Volume": quantities.get("compas_brep_volume", None),
                        "VOLUMEUNIT": quantities.get("VOLUMEUNIT"),
                    }
                )

                # Optional: include no-material rows in dissected too (1 row per element)
                boq_rows_dissected.append(
                    {
                        "EID": metadata.get("eid", None),
                        "GlobalId": metadata.get("global_id", None),
                        "Name": metadata.get("name", None),
                        "Layer/Material Number": None,
                        "Entity": metadata.get("entity", None),
                        "Object Type": metadata.get("object_type", None),
                        "Material Type": "no_material",
                        "Material Entity": None,
                        "Material Name": None,
                        "Thickness": None,
                        "Length": quantities.get("length", None),
                        "Width": quantities.get("width", None),
                        "Height": quantities.get("height", None),
                        "Depth": quantities.get("depth", None),
                        "LENGTHUNIT": quantities.get("LENGTHUNIT"),
                        "Net Area": quantities.get("net_area", None),
                        "Net Side Area": quantities.get("net_side_area", None),
                        "Net Footprint Area": quantities.get("net_footprint_area", None),
                        "Net Surface Area": quantities.get("net_surface_area", None),
                        "Cross-sectional Area": quantities.get("cross_section_area", None),
                        "OBB Largest Area": quantities.get("compas_obb_largest_area", None),
                        "AREAUNIT": quantities.get("AREAUNIT"),
                        "Net Volume": quantities.get("net_volume", None),
                        "BRep Volume": quantities.get("compas_brep_volume", None),
                        "VOLUMEUNIT": quantities.get("VOLUMEUNIT"),
                    }
                )

            except Exception as e:
                print(f"[WARN] Skipping {source_path.name}: {e}")

    # Export the Bill of Quantities to a CSV file
    boq_all_output_path = processed_directory / "BoQ_processed_all.csv"
    boq_all_fieldnames = [
        "EID",
        "GlobalId",
        "Name",
        "Entity",
        "Object Type",
        "Material Type",
        "Material Entity",
        "Material Name(s)",
        "Thickness",
        "Length",
        "Width",
        "Height",
        "Depth",
        "LENGTHUNIT",
        "Net Area",
        "Net Side Area",
        "Net Footprint Area",
        "Net Surface Area",
        "Cross-sectional Area",
        "OBB Largest Area",
        "AREAUNIT",
        "Net Volume",
        "BRep Volume",
        "VOLUMEUNIT",
    ]

    with boq_all_output_path.open("w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=boq_all_fieldnames)
        writer.writeheader()
        writer.writerows(boq_rows_all)

    boq_dissected_output_path = processed_directory / "BoQ_processed_dissected.csv"
    boq_dissected_fieldnames = [
        "EID",
        "GlobalId",
        "Name",
        "Layer/Material Number",
        "Entity",
        "Object Type",
        "Material Type",
        "Material Entity",
        "Material Name",
        "Thickness",
        "Length",
        "Width",
        "Height",
        "Depth",
        "LENGTHUNIT",
        "Net Area",
        "Net Side Area",
        "Net Footprint Area",
        "Net Surface Area",
        "Cross-sectional Area",
        "OBB Largest Area",
        "AREAUNIT",
        "Net Volume",
        "BRep Volume",
        "VOLUMEUNIT",
    ]

    with boq_dissected_output_path.open("w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=boq_dissected_fieldnames)
        writer.writeheader()
        writer.writerows(boq_rows_dissected)

    print(f"Preliminary BoQ of entire elements stored in: {boq_all_output_path}. Rows written: {len(boq_rows_all)}")
    print(f"Preliminary BoQ of dissected elements stored in: {boq_dissected_output_path}. Rows written: {len(boq_rows_dissected)}")
    print("")


# ------------------------
# BOQ EXTRACTED (BOQ 02)
# ------------------------


def extract_lca_model_boq(input_csv_path: str, output_dir: str) -> None:
    """
    Reads input CSV, deletes certain columns, adds LCA columns,
    and enriches rows using JSON files found under output_dir subfolders.

    Implemented:
      - abstract_components/*.json enrichment
      - single_materials/*.json enrichment
      - layered_elements/*.json enrichment (per-layer mapping using Layer/Material Number)

    Output:
      - writes to: Path(output_dir) / "BoQ_extracted.csv"
    """

    # ----------------------
    # CONFIG
    # ----------------------
    columns_to_delete = [
        "Material Type",
        "Thickness",
        "Length",
        "Width",
        "Height",
        "Depth",
        "LENGTHUNIT",
        "Net Area",
        "Net Side Area",
        "Net Footprint Area",
        "Net Surface Area",
        "Cross-sectional Area",
        "OBB Largest Area",
        "AREAUNIT",
        "Net Volume",
        "BRep Volume",
        "VOLUMEUNIT",
    ]

    columns_to_add = [
        "Loadbearing",
        "Placement",
        "Entry Type",
        "Material Type",
        "Component Type",
        "Facet Type",
        "Thickness [m]",
        "Length [m]",
        "Area [m2]",
        "Volume [m3]",
    ]

    subdirs = {
        "abstract_components": "abstract_components",
        "layered_elements": "layered_elements",
        "single_materials": "single_materials",
        "undefined_elements": "undefined_elements",
    }

    # abstract_components: facet.component_facet.<one-of-these>
    component_facet_keys = [
        "building_service_type",
        "ceiling_type",
        "conveyor_type",
        "curtain_wall_type",
        "door_type",
        "insulation_element_type",
        "infill_type",
        "railing_type",
        "roof_type",
        "shading_device_type",
        "stair_type",
        "window_fitting_type",
        "frame_type",
    ]

    # materials: facet.material_facet.<one-of-these>
    material_facet_keys = [
        "biobased_type",
        "bituminous_type",
        "concrete_type",
        "metallic_type",
        "mineral_type",
        "polymeric_type",
        "wood_type",
    ]

    # element_core[*]["thickness"] is in millimeters
    THICKNESS_INPUT_UNIT = "mm"  # used only for conversion here
    # ----------------------

    input_path = Path(input_csv_path)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = out_dir / "BoQ_extracted.csv"

    # ----------------------
    # Helpers
    # ----------------------
    def _safe_get(d: Any, path: list[str], default: Any = None) -> Any:
        cur = d
        for key in path:
            if not isinstance(cur, dict) or key not in cur:
                return default
            cur = cur[key]
        return cur

    def _first(lst: Any, default: Any = None) -> Any:
        return lst[0] if isinstance(lst, list) and len(lst) > 0 else default

    def _load_json_files(folder: Path) -> list[Dict[str, Any]]:
        if not folder.exists() or not folder.is_dir():
            return []
        items: list[Dict[str, Any]] = []
        for p in folder.glob("*.json"):
            try:
                items.append(json.loads(p.read_text(encoding="utf-8")))
            except Exception:
                continue
        return items

    def _stringify_facet_value(v: Any) -> str:
        if v is None:
            return ""
        if isinstance(v, list):
            if len(v) == 0:
                return ""
            str_items = [x.strip() for x in v if isinstance(x, str) and x.strip()]
            if str_items:
                return ", ".join(str_items)
            return str(v[0])
        if isinstance(v, str):
            return v.strip()
        return str(v)

    def _extract_first_key_value(container: Any, keys: list[str]) -> str:
        if not isinstance(container, dict):
            return ""
        for k in keys:
            if k not in container:
                continue
            s = _stringify_facet_value(container.get(k))
            if s != "":
                return s
        return ""

    def _extract_abstract_facet_type(core0: Dict[str, Any]) -> str:
        component_facet = _safe_get(core0, ["facet", "component_facet"], default={})
        return _extract_first_key_value(component_facet, component_facet_keys)

    def _extract_material_facet_type(core0: Dict[str, Any]) -> str:
        material_facet = _safe_get(core0, ["facet", "material_facet"], default={})
        return _extract_first_key_value(material_facet, material_facet_keys)

    def _quantities_to_map(payload: Dict[str, Any]) -> Dict[str, Optional[float]]:
        q_list = _safe_get(payload, ["quantities", "quantities"], default=[])
        out: Dict[str, Optional[float]] = {"thickness": None, "length": None, "area": None, "volume": None}
        if not isinstance(q_list, list):
            return out
        for q in q_list:
            if not isinstance(q, dict):
                continue
            name = q.get("name")
            val = q.get("value")
            if name in out:
                out[name] = val
        return out

    def _to_float(x: Any) -> Optional[float]:
        if x is None:
            return None
        try:
            if isinstance(x, str):
                x = x.strip()
                if x == "":
                    return None
            return float(x)
        except Exception:
            return None

    def _thickness_to_meters(x: Any) -> Optional[float]:
        t = _to_float(x)
        if t is None:
            return None
        if THICKNESS_INPUT_UNIT == "mm":
            return t / 1000.0
        return t

    # ----------------------
    # Load input CSV
    # ----------------------
    df = pd.read_csv(input_path, dtype="string")

    df = df.drop(columns=[c for c in columns_to_delete if c in df.columns])

    for col in columns_to_add:
        if col not in df.columns:
            df[col] = ""

    if "EID" not in df.columns:
        raise ValueError('Input CSV must contain a column named "EID".')

    # Required for layered mapping
    has_layer_number_col = "Layer/Material Number" in df.columns

    # ----------------------
    # Load JSON payloads
    # ----------------------
    json_by_category: Dict[str, list[Dict[str, Any]]] = {}
    for key, sub in subdirs.items():
        json_by_category[key] = _load_json_files(out_dir / sub)

    # Index payloads by element_eid
    abstract_index: Dict[str, Dict[str, Any]] = {}
    for payload in json_by_category["abstract_components"]:
        element_eid = _safe_get(payload, ["descriptor", "element_eid"])
        if element_eid is None:
            continue
        abstract_index[str(element_eid)] = payload

    single_index: Dict[str, Dict[str, Any]] = {}
    for payload in json_by_category["single_materials"]:
        element_eid = _safe_get(payload, ["descriptor", "element_eid"])
        if element_eid is None:
            continue
        single_index[str(element_eid)] = payload

    layered_index: Dict[str, Dict[str, Any]] = {}
    for payload in json_by_category["layered_elements"]:
        element_eid = _safe_get(payload, ["descriptor", "element_eid"])
        if element_eid is None:
            continue
        layered_index[str(element_eid)] = payload

    # ----------------------
    # Enrich rows
    # Priority: layered (if layer number exists and payload exists) -> abstract -> single
    # ----------------------
    eids = df["EID"].astype("string").fillna("")

    # Cache per-layered-element computations (sum thickness, total volume, etc.)
    layered_cache: Dict[str, Dict[str, Any]] = {}

    for i, eid in enumerate(eids):
        eid_str = str(eid)

        # 1) Layered (row-level mapping using Layer/Material Number)
        if has_layer_number_col and eid_str in layered_index:
            payload = layered_index[eid_str]

            layer_no_raw = df.at[i, "Layer/Material Number"]
            layer_no = _to_float(layer_no_raw)
            if layer_no is None:
                # Can't map to a specific layer; skip layered handling for this row.
                pass
            else:
                layer_idx = int(layer_no) - 1  # CSV is 1-based, list is 0-based

                cores = payload.get("element_core", [])
                if isinstance(cores, list) and 0 <= layer_idx < len(cores):
                    coreN = cores[layer_idx] or {}

                    # Build/cache element-level computations
                    if eid_str not in layered_cache:
                        qmap_total = _quantities_to_map(payload)
                        total_volume = _to_float(qmap_total.get("volume"))
                        total_length = _to_float(qmap_total.get("length"))
                        total_area = _to_float(qmap_total.get("area"))

                        # Sum layer thicknesses from element_core entries
                        layer_thicknesses_m: list[float] = []
                        for c in cores:
                            t_m = _thickness_to_meters((c or {}).get("thickness"))
                            if t_m is not None and t_m > 0:
                                layer_thicknesses_m.append(t_m)

                        sum_thickness_m = sum(layer_thicknesses_m) if layer_thicknesses_m else None

                        layered_cache[eid_str] = {
                            "total_volume": total_volume,
                            "total_length": total_length,
                            "total_area": total_area,
                            "sum_thickness_m": sum_thickness_m,
                        }

                    cache = layered_cache[eid_str]

                    # Row fields (material-like)
                    df.at[i, "Loadbearing"] = coreN.get("loadbearing") or ""
                    df.at[i, "Placement"] = coreN.get("placement") or ""
                    df.at[i, "Entry Type"] = coreN.get("entry_type") or ""

                    # Component Type empty for layered material rows (same as single material)
                    df.at[i, "Component Type"] = ""

                    # Material Type from facet.material_type
                    df.at[i, "Material Type"] = _safe_get(coreN, ["facet", "material_type"], default="") or ""

                    # Facet Type from facet.material_facet.<one-of-keys>
                    df.at[i, "Facet Type"] = _extract_material_facet_type(coreN)

                    # Quantities for layered rows:
                    # - length/area copied from total quantities
                    # - thickness is per-layer from coreN.thickness
                    # - volume proportional by thickness ratio
                    df.at[i, "Length [m]"] = "" if cache["total_length"] is None else str(cache["total_length"])
                    df.at[i, "Area [m2]"] = "" if cache["total_area"] is None else str(cache["total_area"])

                    t_layer_m = _thickness_to_meters(coreN.get("thickness"))
                    df.at[i, "Thickness [m]"] = "" if t_layer_m is None else str(t_layer_m)

                    vol_total = cache["total_volume"]
                    sum_t = cache["sum_thickness_m"]
                    if vol_total is None or sum_t is None or sum_t == 0 or t_layer_m is None:
                        df.at[i, "Volume [m3]"] = ""
                    else:
                        df.at[i, "Volume [m3]"] = str(vol_total * (t_layer_m / sum_t))
                    continue

        # 2) Abstract components
        payload = abstract_index.get(eid_str)
        if payload:
            core0 = _first(payload.get("element_core"), default={}) or {}

            df.at[i, "Loadbearing"] = core0.get("loadbearing") or ""
            df.at[i, "Placement"] = core0.get("placement") or ""
            df.at[i, "Entry Type"] = core0.get("entry_type") or ""

            # Material Type stays empty
            df.at[i, "Component Type"] = _safe_get(core0, ["facet", "component_type"], default="") or ""
            df.at[i, "Facet Type"] = _extract_abstract_facet_type(core0)

            qmap = _quantities_to_map(payload)
            df.at[i, "Thickness [m]"] = "" if qmap["thickness"] is None else str(qmap["thickness"])
            df.at[i, "Length [m]"] = "" if qmap["length"] is None else str(qmap["length"])
            df.at[i, "Area [m2]"] = "" if qmap["area"] is None else str(qmap["area"])
            df.at[i, "Volume [m3]"] = "" if qmap["volume"] is None else str(qmap["volume"])
            continue

        # 3) Single materials
        payload = single_index.get(eid_str)
        if payload:
            core0 = _first(payload.get("element_core"), default={}) or {}

            df.at[i, "Loadbearing"] = core0.get("loadbearing") or ""
            df.at[i, "Placement"] = core0.get("placement") or ""
            df.at[i, "Entry Type"] = core0.get("entry_type") or ""

            df.at[i, "Component Type"] = ""
            df.at[i, "Material Type"] = _safe_get(core0, ["facet", "material_type"], default="") or ""
            df.at[i, "Facet Type"] = _extract_material_facet_type(core0)

            qmap = _quantities_to_map(payload)
            df.at[i, "Thickness [m]"] = "" if qmap["thickness"] is None else str(qmap["thickness"])
            df.at[i, "Length [m]"] = "" if qmap["length"] is None else str(qmap["length"])
            df.at[i, "Area [m2]"] = "" if qmap["area"] is None else str(qmap["area"])
            df.at[i, "Volume [m3]"] = "" if qmap["volume"] is None else str(qmap["volume"])
            continue

    # Scaffold placeholders for undefined_elements (not implemented yet)
    # undef_payloads = json_by_category["undefined_elements"]

    print(f"Updated BoQ of dissected elements saved to: {output_path}.")
    print("")
    print("IFC extraction complete - LCA model successfully assembled.\n")

    df.to_csv(output_path, index=False)
