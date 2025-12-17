
from compas_lca.workflows.raw_extraction.ifc.ifc_processing import process_ifc_element
from compas_lca.workflows.raw_extraction.ifc.ifc_caches import IfcCaches
from compas_lca.workflows.raw_extraction.ifc.ifc_readers import load_ifc_units
from compas_lca.workflows.raw_extraction.ifc.ifc_helpers import write_bytes
from compas_ifc.model import Model
from pathlib import Path

IFC_PATH = "temp/ifc_files/1072_HiLo_Model-Architecture.ifc"

output_dir = Path("temp/ifc_preprocessed/0_samples/HiLo/layers")

SAMPLES = [
    "Floor:DCH_DÄ+BLECH_113:11165689",
    "Floor:BBA_BE-DÄ_100-BG1:7326415",
    "Basic Wall:WAN_TWÄ_MW+VS_300 - EI60:11586674",
    "Floor:AHD_DÄ_150:10969563",
    "Basic Wall:Holzbau_Archisonic_Vorbauschale:2146702",
    "Basic Wall:Isolamin 100:2350191",
    "Basic Wall:Exterior - Brick on Block:138062",
    "Basic Wall:WAN_ASW_DÄ-PU_300:5370817",
    "Basic Wall:FAS_ASW_DÄ-ABD_120:13861927",
    "Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:139234",
    "Basic Wall:Blechverkleidung gedämmt:1829613",
    "Floor:DCH_DÄ-AS_250:7601562",
    "Floor:Funicular Floor:687636",
    "Basic Wall:Interior - Plumbing (152mm Stud):144138",
    "Floor:DCH_BLECH_53:13862065",
    "Basic Wall:WAN_TWÄ_GK_100_VS:4246877",
    "Basic Wall:WAN_ASW_DÄ-PU_220:5059297",
    "Floor:Residential - Wood Joist with Subflooring:144800",
    "Floor:Galerie Fussbodenaufbau:1353081",
    "Basic Wall:FAS_ASW_DÄ-VHF_180:13656021",
    "Floor:Dämmung Galerie:1708478",
    "Basic Roof:Bef TRP70:1206363",
    "Floor:BBA_BE-DÄ_120-Schmutzstreifen:12439757",
    "Floor:Finish Floor - Ceramic Tile:169772",
    "Floor:Bodenaufbau 12 beton + 5 aufbau:2462797",
    "Floor:Concrete - Existing - 50+160:1699978",
    "Basic Wall:Holzfassade hinterlüftet:1105047",
    "Basic Wall:WAN_ASW_DÄ-BET_300:5102504",
    "Basic Wall:WAN_TWÄ_GK_100 - EI30:4246887",
    "Basic Wall:FAS_ASW_DÄ-PU_325:11226723",
    "Floor:Finish Floor - Wood:169093"
]

def main():
    # Model setup
    model = Model(IFC_PATH)
    caches = IfcCaches(model)
    units = load_ifc_units(model)

    # Retrieve all IfcBuildingElement entities once
    building_elements = model.get_entities_by_type("IfcBuildingElement")

    # Index them by name for faster lookup
    name_to_elements = {}
    for e in building_elements:
        ename = getattr(e, "Name", None)
        if not ename:
            continue
        name_to_elements.setdefault(ename, []).append(e)

    matched_entities = []

    for name in SAMPLES:
        elements = name_to_elements.get(name, [])
        if not elements:
            continue

        print(f"\nFound {len(elements)} building element(s) with name: {name}")

        for element in elements:
            # Optional: skip elements that are obviously incomplete
            if not getattr(element, "GlobalId", None):
                # If this is an issue in your file, log and continue
                print(f"  Skipping element #{element.id()}: missing GlobalId")
                continue

            # Process a single element
            data = process_ifc_element(element, caches, units)

            # If your process_ifc_element logs errors and returns None on failure,
            # then guard against that here:
            if data is None:
                print(f"  Skipping element #{element.id()}: processing returned None")
                continue

            meta = data.metadata
            gid = meta.global_id

            # Fallback if meta.global_id is somehow missing
            if gid is None:
                # Try to recover from the IFC entity itself
                gid = getattr(element, "GlobalId", None)
                if gid is None:
                    print(f"  Skipping element #{element.id()}: no global_id in metadata or entity")
                    continue

            json_str = data.model_dump_json(
                exclude_none=False,
                by_alias=True,
                indent=2,
            )
            json_blob = json_str.encode("utf-8")
            write_bytes(output_dir / f"{gid}.json", json_blob)

            matched_entities.append(element)

    print("\nSummary:")
    print(f"Total building elements found for names in SAMPLES: {len(matched_entities)}")


if __name__ == "__main__":
    main()
