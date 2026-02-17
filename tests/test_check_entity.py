import ifcopenshell
from typing import Any, Dict, List, Optional

# ==============================
# USER INPUT (EDIT THESE)
# ==============================

IFC_PATH = r"data/building_model/1072_HiLo_Model-Architecture.ifc"
TARGET_GLOBAL_ID = "1a1$QVmKz8nRXZVkIMOO8T"

# ==============================
# INTERNAL FUNCTIONS
# ==============================


def _safe_getattr(obj: Any, name: str, default=None):
    try:
        return getattr(obj, name)
    except Exception:
        return default


def material_to_records(mat: Any) -> List[Dict[str, Optional[str]]]:
    if mat is None:
        return []

    t = mat.is_a()

    # --- Simple material ---
    if t == "IfcMaterial":
        return [{
            "kind": "IfcMaterial",
            "name": _safe_getattr(mat, "Name"),
            "category": _safe_getattr(mat, "Category"),
        }]

    # --- Layered materials (walls, slabs) ---
    if t == "IfcMaterialLayerSetUsage":
        return material_to_records(mat.ForLayerSet)

    if t == "IfcMaterialLayerSet":
        out = []
        for layer in mat.MaterialLayers or []:
            m = layer.Material
            out.append({
                "kind": "IfcMaterialLayer",
                "name": _safe_getattr(m, "Name") if m else None,
                "category": _safe_getattr(m, "Category") if m else None,
                "layer_thickness": _safe_getattr(layer, "LayerThickness"),
            })
        return out

    # --- Profile-based materials (beams, columns) ---
    if t == "IfcMaterialProfileSetUsage":
        return material_to_records(mat.ForProfileSet)

    if t == "IfcMaterialProfileSet":
        out = []
        for mp in mat.MaterialProfiles or []:
            m = mp.Material
            prof = mp.Profile
            out.append({
                "kind": "IfcMaterialProfile",
                "name": _safe_getattr(m, "Name") if m else None,
                "category": _safe_getattr(m, "Category") if m else None,
                "profile": _safe_getattr(prof, "ProfileName") if prof else None,
            })
        return out

    # --- Constituent set ---
    if t == "IfcMaterialConstituentSet":
        out = []
        for c in mat.MaterialConstituents or []:
            m = c.Material
            out.append({
                "kind": "IfcMaterialConstituent",
                "name": _safe_getattr(m, "Name") if m else None,
                "category": _safe_getattr(m, "Category") if m else None,
                "constituent": _safe_getattr(c, "Name"),
            })
        return out

    # --- Material list ---
    if t == "IfcMaterialList":
        out = []
        for m in mat.Materials or []:
            out.extend(material_to_records(m))
        return out

    # --- Fallback ---
    return [{
        "kind": t,
        "name": _safe_getattr(mat, "Name"),
        "category": _safe_getattr(mat, "Category"),
    }]


def get_materials_for_object(obj: Any) -> List[Dict[str, Optional[str]]]:
    records: List[Dict[str, Optional[str]]] = []

    for rel in _safe_getattr(obj, "HasAssociations", []) or []:
        if rel.is_a("IfcRelAssociatesMaterial"):
            mat = rel.RelatingMaterial
            records.extend(material_to_records(mat))

    return records


# ==============================
# MAIN EXECUTION
# ==============================

def main():
    model = ifcopenshell.open(IFC_PATH)

    element = model.by_guid(TARGET_GLOBAL_ID)
    if element is None:
        print(f"No element found with GlobalId = {TARGET_GLOBAL_ID}")
        return

    print("\nELEMENT")
    print("--------")
    print(f"GlobalId : {element.GlobalId}")
    print(f"Type     : {element.is_a()}")
    print(f"Name     : {_safe_getattr(element, 'Name')}")
    print(f"Tag      : {_safe_getattr(element, 'Tag')}")

    # --- Check instance materials ---
    materials = get_materials_for_object(element)

    print("\nINSTANCE MATERIALS")
    print("------------------")
    if materials:
        for i, m in enumerate(materials, 1):
            print(f"{i}. {m}")
    else:
        print("No material directly assigned to instance.")

    # --- Check type materials (very common in Revit exports) ---
    for rel in _safe_getattr(element, "IsDefinedBy", []) or []:
        if rel.is_a("IfcRelDefinesByType"):
            typ = rel.RelatingType
            if typ:
                type_materials = get_materials_for_object(typ)
                if type_materials:
                    print("\nTYPE MATERIALS")
                    print("--------------")
                    print(f"Type: {typ.is_a()} | Name: {_safe_getattr(typ, 'Name')}")
                    for i, m in enumerate(type_materials, 1):
                        print(f"{i}. {m}")
            break


if __name__ == "__main__":
    main()
