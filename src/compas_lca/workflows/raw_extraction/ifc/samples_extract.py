
from compas_lca.workflows.raw_extraction.ifc.ifc_processing import process_ifc_element
from compas_lca.workflows.raw_extraction.ifc.ifc_caches import IfcCaches
from compas_lca.workflows.raw_extraction.ifc.ifc_readers import load_ifc_units
from compas_lca.workflows.raw_extraction.ifc.ifc_helpers import write_bytes
from compas_ifc.model import Model
from pathlib import Path

IFC_PATH = "temp/ifc_files/Duplex_A_20110907.ifc"

output_dir = Path("temp/ifc_preprocessed/0_samples/Duplex")

SAMPLES = [
    "Column Planed Wood:38x145:946122",
    "",
    "Floor:Perimeterdämmung:4784219",
    "Floor:OSB 25mm:5183063",
    "TU DF 1 - Pfostenstock Falztüre:DL - 900 x 2130:1118965",
    "Stair:Concrete:716803:1",
    "Plate (face based):Plate (face based):1696783",
    "M_Single-Glass 1:0813 x 2420mm:0813 x 2420mm:171853",
    "Basic Wall:WAT_ASW_STB_250:2826560",
    "BSH Stütze - rechteckig:KVH 60 x 60:5755285",
    "Basic Wall:Technikschnittstelle:6225020",
    "Floor:AHD_DÄ_160:12312285",
    "Fassade Ecke EG1:FAS_ECK_EG:12651885",
    "Bolt:M16:1248900",
    "Floor:BBA_BL_15-Mieterausbau:11598222",
    "Floor:Gitterrost schwarz:354156",
    "1OG-I-1-2",
    "Basic Wall:Brick- Existing - 200:1441293",
    "Storen_ZIP:SOS_STO_275x395:14112561",
    "Wall Foundation:Bearing Footing - 900 x 300:186596",
    "Basic Wall:Holzfassade_Hinterlüftet_Laibung:2906806",
    "HEB Träger:TRA_HEB_STA_180:10123612",
    "Beam Planed Timber:45x95:1091811",
    "Basic Wall:GEL_FÜL_OPK_BALK_100:11023610",
    "Abdeckblech gerundet-neu:Abdeckblech gerundet-neu:6385866",
    "Floor:AHD_DÄ_90:13984336",
    "Floor:AHD_DÄ_150:13817755",
    "Attikablech Galerie Südost:Attikablech Galerie Südost:6350725",
    "EG-A-1-1",
    "Floor:BBA_HBE_30-BG2 geschliffen:9576469",
    "Floor:3-Schichtplatte 40mm:5206093",
    "Systemelement:Dämmelement:1123941",
    "Basic Roof:Live Roof over Wood Joist Flat Roof:184483",
    "Floor:GDE_BAL_MET_30:7151537",
    "Blechabdeckung Brüstung:Blechabdeckung Brüstung:7933804",
    "Basic Wall:3-Schichtplatte 27mm - Schalplatte:3555236",
    "Assembled Stair:Stair:11892954 Landing 1",
    "Kemper Wandtresor:TRES_350x350:15539713",
    "Anfahrschutz Rohr:2350 x 400:13363728",
    "Basic Wall:WAN_ASW_MW_225:7610934",
    "Basic Wall:STB 1560:3067474",
    "Floor:GDE_STB_200:6529254",
    "Floor:DCH_SUB_100:14297034",
    "Basic Wall:Holzwerkstoffplatte 20mm:21680813",
    "Attikablech Galerie Südwest:Attikablech Galerie Südwest:6351305",
    "Basic Wall:WAN_TWÄ_MW_150-KS:10152070",
    "Rebar Bar:12 B500C-T : Shape A:2111867",
    "hlks1:hlks:10122938",
    "Basic Wall:Wärmedämmung_Mineralwolle_130:1839774",
    "Basic Wall:Innenwandelement Archisonic ohne MDF:3995377",
    "2OG-Balkon-1-1",
    "Fire Protection_Beam 3 sides:200x190:1171719",
    "Vierkantstahl Stütze:140 x 80:12651870",
    "TU DF 1 - Pfostenstock Falztüre verglast:TUI_ZAR_MET_ML - 1100 x 2375_E 30:7560858",
    "Basic Wall:WAT_ASW_STB_250:5585349",
    "Basic Wall:Fensterlaibung 40mm:6514187",
    "Dämmung2:Dämmung:21751352",
    "Surface:2872326",
    "Floor:DÄ_FUN_HOR_100:12567832",
    "Systemelement:Profilglas 15 -  mittig:21414704",
    "1072_210525_TreppeInnenRevitExport_MK:1072_210525_TreppeInnenRevitExport_MK:7935324",
    "Stiffener:Stiffener:1094120",
    "Basic Wall:DÄ_FUN_VER_100:12568941",
    "FE Dachkuppel rund:Ø=1200:13668242",
    "Floor:BBA_HBE_50-BG1:7590425",
    "M_Skylight:1180 x 1170mm:1180 x 1170mm:185337",
    "Basic Wall:Panel Holz beidseitig gelocht mit Dämmung 54mm:22849485",
    "Shell_V12:Shell_V12:5294566",
    "Stufen Dach5:Stufen Dach:13656116",
    "Basic Wall:WAN_ASW_MW_100:8756190",
    "Dachdämmung_V3:Dachdämmung_V3:5659319",
    "Basic Wall:Wärmedämmung_Slentex 70:687731",
    "Basic Wall:WAN_DCK_DÄ_100:8137387",
    "Basic Wall:WAN_ASW_MW_145:10993756",
    "Vordach-1",
    "Floor:BBA_GIT_MET_30:11023640:10",
    "Screwed Pin:M24:1238114",
    "Assembled Stair:Stair:11892954 Run 1",
    "Floor:BBA_ASP_120:11419651",
    "Systemelement:Glas 100 - Versatz 25:5102516",
    "Floor:Floor_Holz_40mm:21756579",
    "Systemelement:PAN_GLAS_45 - OG:11226128",
    "Basic Wall:FUN_STB_1500:3010518",
    "Rechteckiger Pfosten:VF_PFT T_L_60 x 200:8880687",
    "1OG-Fenster-1-1",
    "Geländer Kern 6.OG2:GEL_TREP_6OG:14099961",
    "STB Stütze - rechteckig:STZ_RTE_STB_450 x 450:2634854",
    "Basic Wall:KVH Balken 120mm:6158104",
    "TO - Falttor - 1 x 3 Flügel:TOA_FLT_MET_4125 x 4200:8756847",
    "Railing:GEL_FÜL_BALK_GITR:11023613",
    "Floor:BBA_ASP_50:9567604",
    "Basic Wall:BSP 140 Sichtseite einseitig:1744018",
    "Atikkabrett:Atikkabrett:6717985",
    "Basic Wall:Massivholz 24mm:6301160",
    "Fertigteil-TT-Platte - Ausklinkung beidseitig - ohne Fase - asymmetrisch:2750 x 680:3647246",
    "Rechteckiger Pfosten:140 x 60 - Holz:21414725",
    "Assembled Stair:Stair:1458173 Run 1",
    "IPE Träger Kammerbeton:TRA_IPE-KAB_STA_STB_400:8222212",
    "Basic Wall:Brandschutzplatte 28mm:1935406",
    "Fenster-Pfosten Brett:VF_PFT_MET_50 x 290 x 2600:9774242",
    "Fassade - FE 1 flg:FEN_STA_50 x 60-Kippelement:8879976",
    "Parkplatz - 01 90:PAR_2400 x 5000:10260983",
    "PV-Anlage_Bauder:ELE_PVA:12550613",
    "Floor:OSB 22mm:4937655",
    "Precast Stair:Stair:10092362 Landing 1",
    "Railing:GEL_STA_40x40 3STK-handlauf unterbrochen:8881489",
    "Basic Wall:WAN_TWÄ_MW_125 - EI30:11161798",
    "Basic Wall:WAN_ASW_VKL_10:12099875",
    "TO - Brandschutztor:TOI_SIT_MET_ST - 2180 x 2200:8609379",
    "Basic Wall:Brandschutzplatte:5251017",
    "Wall Foundation:Concrete - Cast-in-Place - 1200x300:1282521",
    "Stair:Residential - 200mm Max Riser 250mm Tread:151086:1",
    "Attikabrett:Attikabrett:6718052",
    "Holz Träger - rechteckig:Alu Eurotec 40 x 60:7547868",
    "STB Stütze - rechteckig:STB 500 x 500:2623790",
    "Systemelement:Contraflam EI30:1753138",
    "Holz Träger - rechteckig:Holz 60 x 200:6746028",
    "Window Opening Circle:120:2373865",
    "Fertigteil-TT-Platte - Ausklinkung beidseitig - ohne Fase:TRA_RIP_STB_2750 x 480_ohne gabel:2623718",
    "Floor:DCH_DÄ+AB_300:6785352",
    "System Panel:PAN_DÄM_ALU_50:11227867",
    "TU DF 1 - Rahmenstock flächenbündig:TUI_ZAR_STA_MÖ - 1100 x 2200_EI 30:10129091",
    "Bleche Fassade_V6:Bleche Fassade_V6:4910201",
    "Floor:Betonauflager 15cm:3980840",
    "Basic Wall:Purenit Fusspunkt:6169888",
    "Basic Wall:FAS_ASW_DÄ_30:12313333",
    "Precast Stair:Stair:3039290 Run 1",
    "Basic Wall:WAN_BRÜ_STB_160-dachrand:8113151",
    "Floor:Bodenaufbau Hauptgeschoss:687594",
    "Beam Gluelam:90x225:1335823",
    "Basic Wall:BSP 140 - 5s:1686981",
    "M_W-Wide Flange:W310X60:W310X60:207325",
    "Floor:Fensterbank 40mm:7087153",
    "1OG-Balkon-1-1",
    "Sockel-gerade:PAN_BET_2.735 / h5.13:11944128",
    "Pfosten rechteckig:Forster 60 x 90 - Nur Pfosten:2355404",
    "Basic Wall:WAN_ASW_LB_100-gel:5059296",
    "Fertigteil-TT-Platte - Entrée:TRA_RIP_STB_2700 x 480_Entrée_4:13843837",
    "Rechteckiger Pfosten:VF_PFT T_M_60 x 125:11226193",
    "Basic Wall:WAT_KWA_STB_785:7556581",
    "1OG-I-1-1",
    "Beam HE:HEA120:2415251",
    "TO - Brandschutztor:TOI_SIT_MET_ST - 2300 x 2200:10306412",
    "1OG-Tür-1-1",
    "HEB Stütze mit Kammerbeton:STZ_HEB-KAM_STA_650 x 300:2816822",
    "Floor:Terrassenbelag Holzlattung Douglasie:7269453",
    "Holz Träger - rechteckig:Holz 60 x 160:22007091",
    "Basic Wall:WAN_ASW_DÄ_60:8977932",
    "Floor:Floor_Linoleum_5mm:21756586:2"
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
