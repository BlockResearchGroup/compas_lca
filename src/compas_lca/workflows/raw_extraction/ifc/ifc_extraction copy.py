"""
Hybrid between Agent-based extraction and hardcoding to create
LcaElement objects from IfcBuildingElement data. In order for this
workflow to work, one needs to pre-process the chosen IFC model with the
run_processing.py file (essentially run process_ifc_model from ifc_processing.py).

The arguments/parameters for the functions here refer to the directory structure
that is created by "process_ifc_model". The functions created here will be used in the
workflows/raw_extraction/ifc/run_extraction.py script.

In the "run_extraction.py" script, one needs to reference the parent directory folder, 
which will by default be stored in "temp", and is called after the IFC file name. 
The rest is handled by the ifc_extraction workflows.
"""
import json

from uuid import uuid4

from pathlib import Path

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Literal
from typing import Tuple

from compas_lca.helpers import load_json
from compas_lca.helpers import merge_llm_meta

from compas_lca.llm.ctx.element_context import DESCRIPTOR_CTX

from compas_lca.matching_core.core import MatchingCore

from compas_lca.model.lca_model import LcaModel
from compas_lca.model.descriptor import ElementDescriptor
from compas_lca.model.lca_element import LcaElement
from compas_lca.model.metadata import ModelMetadata
from compas_lca.model.quantity import Quantity
from compas_lca.model.quantity import Quantities

from compas_lca.workflows.extraction import extract_json_with_agent
from compas_lca.workflows.extraction import extract_matching_core
from compas_lca.workflows.speculation import speculate_layer_thicknesses

from compas_lca.workflows.raw_extraction.ifc.ifc_helpers import update_descriptor_ifc
from compas_lca.workflows.raw_extraction.ifc.ifc_helpers import update_matching_core_ifc
from compas_lca.workflows.raw_extraction.ifc.ifc_helpers import _get_in
from compas_lca.workflows.raw_extraction.ifc.ifc_helpers import _coerce_number
from compas_lca.workflows.raw_extraction.ifc.ifc_helpers import _first_numeric
from compas_lca.workflows.raw_extraction.ifc.ifc_helpers import _obb_dimension_range
from compas_lca.workflows.raw_extraction.ifc.ifc_helpers import _build_guid_index
from compas_lca.workflows.raw_extraction.ifc.ifc_helpers import _build_guid_dir_index
from compas_lca.workflows.raw_extraction.ifc.ifc_helpers import _save_lca_element
from compas_lca.workflows.raw_extraction.ifc.ifc_helpers import _iter_subdirs
from compas_lca.workflows.raw_extraction.ifc.ifc_helpers import _discover_multix_paths
from compas_lca.workflows.raw_extraction.ifc.ifc_helpers import _pick_multilayer_bucket
from compas_lca.workflows.raw_extraction.ifc.ifc_helpers import _pick_multimaterial_bucket



# ==============================================================================
# Extract MetaData from Model metadata and append invidiual UUID for tracability
# ==============================================================================

def extract_metadata_ifc(model_data: dict) -> ModelMetadata:
    """Extract ModelMetadata object for LcaModel"""
    return ModelMetadata(
        dataset_source="IFC",
        source_version=model_data.get("IFC Schema"),
        dataset_filename=model_data.get("File Name"),
        dataset_uuid=model_data.get("IFC Project UUID"),
        location_data=model_data.get("Site Data"),
        reference_date=model_data.get("Document Creation Time"),
        dataset_owner=model_data.get("Document Owner"),
    )

# =============================================================
# Extract the element core from a processed IfcBuildingElement
# =============================================================

"""
As defined in LcaElement, the element_core field is a list 
of MatchingCore objects. Depending on the type of element (single material
vs. multimaterial), this list will either have one entry or multiple.
"""

def extract_element_core_ifc(global_json: Dict[str,Any]) -> List[MatchingCore]:
    element_core = []
    core, llm_meta = extract_matching_core(
        input_type = "building_element", 
        input_data=global_json,
        input_format="json"
    )
    element_core.append(core)
    return element_core, llm_meta

def extract_multilayer_core_ifc(
    global_json: Dict[str,Any], # added as an argument, if later additional data is needed for more precise inference
    part_jsons: List[Dict[str,Any]],
) -> List[MatchingCore]:
    element_core = []
    aggregated_meta: dict = {}
    for layer in part_jsons:
        core, layer_meta = extract_matching_core(
            input_type = "building_element", 
            input_data=layer,
            input_format="json",
            force_entry_type="material" # a layer MUST be a material
        )
        element_core.append(core)
        aggregated_meta = merge_llm_meta(aggregated_meta, layer_meta)
    return element_core, aggregated_meta

def extract_multimat_core_ifc(
    global_json: Dict[str, Any],
    materials: List[Dict[str, Any]],
    is_multilayer: bool
) -> Tuple[List[MatchingCore], dict]:
    """
    Extract MatchingCore objects for multilayer or single-material IFC elements,
    injecting speculated layer thicknesses where available.
    Returns both the list of MatchingCore objects and an aggregated LLM meta summary.
    """

    element_core: List[MatchingCore] = []
    aggregated_meta: dict = {}

    # normalize helper for robust matching
    def _norm(s: str) -> str:
        return " ".join(s.split()).casefold()

    if is_multilayer:

        # Speculate thicknesses once
        thickness_result, llm_meta = speculate_layer_thicknesses(input_data=global_json)
        aggregated_meta = merge_llm_meta(aggregated_meta, llm_meta)

        # Build normalized map: layer_name -> list of thicknesses
        thicknesses: Dict[str, List[float]] = {}
        for layer in thickness_result.layers:
            key = _norm(layer.layer_name)
            thicknesses.setdefault(key, []).append(layer.inferred_thickness_mm)

        # Extract each material layer and inject speculated thickness
        for material in materials:
            core, layer_meta = extract_matching_core(
                input_type="building_element",
                input_data=material,
                input_format="json",
                force_entry_type="material",
            )
            aggregated_meta = merge_llm_meta(aggregated_meta, layer_meta)

            layer_name = core.name
            key = _norm(layer_name)

            if key in thicknesses and thicknesses[key]:
                inferred_thickness = thicknesses[key].pop(0)  # take first available
                core= core.model_copy(update={
                    "thickness": inferred_thickness,
                    "thickness_source": "speculated",
                })

            element_core.append(core)

    else:

        # Single IfcMaterialList (no separable layers) → component
        core, llm_meta = extract_matching_core(
            input_type="building_element",
            input_data=global_json,
            input_format="json",
            force_entry_type="component",
        )
        element_core.append(core)
        aggregated_meta = merge_llm_meta(aggregated_meta, llm_meta)

    return element_core, aggregated_meta


# =======================================================
# Extract an ElementDescriptor object from processed IBE
# =======================================================

def extract_descriptor_ifc(
    input_json: dict,
    output_dir: Optional[Path | str] = None
) -> Tuple[ElementDescriptor, dict]:
    """
    Extract a structured ElementDescriptor from IFC JSON data using the LLM agent.
    The outputs (structured JSON and meta) are stored under a 'descriptor' subfolder
    within the specified output directory.

    Args:
        input_json: The IFC element data as a dictionary or JSON string.
        output_dir: Parent directory where the results should be stored.
                    A subfolder 'descriptor' will automatically be created inside it.

    Returns:
        ElementDescriptor: The structured LLM-extracted descriptor object.
    """
    # Derive base name automatically
    base_name =  input_json.get("metadata", {}).get("global_id")
    descriptor_dir = None
    if output_dir is not None:
        descriptor_dir = Path(output_dir) / "parts" / "descriptor"
        descriptor_dir.mkdir(parents=True, exist_ok=True)

    llm_output, llm_meta = extract_json_with_agent(
        input_json=input_json,
        context=DESCRIPTOR_CTX,
        output_dir=descriptor_dir,
        write_meta=True,
        base_name=base_name,
    )

    descriptor = ElementDescriptor.model_validate(llm_output)

    return descriptor, llm_meta

# ==============================================================================
# Extract only relevant Quantities for to LcaElement / Quantities
# ==============================================================================

def extract_quantities_ifc(input_json: dict) -> Quantities:
    """
    Extract a few key quantities from IFC-derived JSON with priority rules.
    Quantities handled: thickness, length, area, volume.
    Extend by adding paths or new blocks below.
    """
    # get type for accurate area extraction
    entity = input_json.get("metadata", {}).get("entity", None)

    # Units (fallbacks are conservative; tweak as needed)
    q = input_json.get("quantities") or {}
    length_unit = q.get("LENGTHUNIT", "MILLIMETRE")
    area_unit   = q.get("AREAUNIT",   "SQUARE_METRE")
    vol_unit    = q.get("VOLUMEUNIT", "CUBIC_METRE")
    quantities: List[Quantity] = []

    # -------- thickness (priority order) --------
    thickness_paths = [
        ["properties", "psets_element", "Thickness"],
        ["properties", "psets_element", "Core Thickness"],
        ["properties", "psets_type", "Construction.Default Thickness"],
        ["properties", "psets_type", "Construction.Default Thickness"],
    ]
    th = _first_numeric(input_json, thickness_paths)
    if th is None:
        # fallback 1: smallest 1-d IFC Qto value
        qto_vals = [q.get("width"),q.get("height"),q.get("depth")]
        qto_clean = [v for v in qto_vals if v is not None]
        if qto_clean:
            th = min(qto_clean)
    if th is None:
        # fallback 2: smallest compas_obb_*dim
        obb_range = _obb_dimension_range(input_json)
        if obb_range:
            th = obb_range[0]  # smallest
    if th is not None:
        quantities.append(Quantity(name="thickness", value=th, unit=length_unit))

    # -------- length (priority order) --------
    length_paths = [
        ["quantities", "length"],
        ["properties", "psets_element", "Length"],
        # add other sources if present in your schema
    ]
    l = _first_numeric(input_json, length_paths)
    if l is None:
        # fallback: largest compas_obb_*dim
        obb_range = _obb_dimension_range(input_json)
        if obb_range:
            l = obb_range[1]  # largest
    if l is not None:
        quantities.append(Quantity(name="length", value=l, unit=length_unit))

    # -------- area (priority order) --------
    # Retrieve corresponding value for accurate LCA calculation in case reference unit
    # of EPD is sqm

    av = None # initialize area value
    if entity in ["IfcWindow", "IfcDoor"]:
        av = q.get("area")
    elif entity in ["IfcSlab", "IfcPlate", "IfcRoof"]:
        av = q.get("net_area")
    elif entity in ["IfcWall", "IfcWallStandardCase"]:
        av = q.get("net_side_area")
    elif entity in ["IfcMember", "IfcBeam", "IfcColumn"]:
        av = q.get("net_surface_area")

    if av is None:
        area_paths = [
            ["properties", "psets_element", "Area"],
            ["properties", "psets_element", "Fläche"],   # umlaut
            ["properties", "psets_element", "Flaeche"],  # ASCII fallback
        ]
        av = _first_numeric(input_json, area_paths)  # this is where coercion happens
    if av is None:
        av = q.get("compas_obb_largest_area")
    if av is not None:
        quantities.append(Quantity(name="area", value=av, unit=area_unit))

    # -------- volume (priority order) --------
    vol = None
    vol = q.get("compas_brep_volume")
    if vol is None:
        volume_paths = [
            ["quantities", "net_volume"],
            ["quantities", "gross_volume"],
            ["quantities", "volume_fallback"],
        ]
        vol = _first_numeric(input_json, volume_paths)
    if vol is not None:
        quantities.append(Quantity(name="volume", value=vol, unit=vol_unit))

    return Quantities(quantities=quantities)


# ======================================================================================================
# Extract different types of LcaElement that addresses predefined directory structure from pre-processing
# ======================================================================================================

MODES = ["single_material", "layered"]

def extract_lca_element_ifc(
    input_json: Optional[dict],         # for mode="single" only
    input_dir: Optional[Path],          # for mode in {"multilayer","multimaterial"} only
    mode: Literal["single", "multilayer", "multimaterial"],
    output_dir: Optional[Path | str] = None
) -> Tuple[LcaElement, dict]:
    """
    Extract an LCA element with strict control over input sources.

    - single:      input_json must be provided, input_dir must be None
    - multilayer:  input_dir must be provided, input_json must be None
    - multimaterial: same as multilayer, but parts are M{n}.json
    """

    # Validate mutually exclusive inputs & load data
    provided = (input_json is not None) + (input_dir is not None)
    if provided != 1:
        raise ValueError("Exactly one of input_json or input_dir must be provided.")

    if mode == "single":
        if input_json is None or input_dir is not None:
            raise ValueError('For mode="single", provide input_json and no input_dir.')
        global_json = input_json # The single object is the element's global json
        part_jsons: list[dict] = []

    elif mode in {"multilayer", "multimaterial"}:
        if input_dir is None or input_json is not None:
            raise ValueError(f'For mode="{mode}", provide input_dir and no input_json.')
        global_path, part_paths = _discover_multix_paths(input_dir, mode)
        global_json = load_json(global_path)
        part_jsons = [load_json(p) for p in part_paths]
        if not part_jsons:
            raise ValueError(
                f"No {'L' if mode=='multilayer' else 'M'}{{n}}.json files found in {input_dir}."
            )
    else:
        raise ValueError(f"Unsupported mode: {mode}")

    # Extract descriptor
    descriptor, llm_meta_desc = extract_descriptor_ifc(global_json)

    # Extract element core (list of matching core(s))
    if mode == "multilayer":
        element_core, llm_meta_core = extract_multilayer_core_ifc(
            global_json,
            part_jsons,
        )
    elif mode == "multimaterial":
        element_core, llm_meta_core = extract_multimat_core_ifc(
            global_json,
            part_jsons,
            descriptor.is_multilayer, # pass descriptor info for possible inference
        )
    else:  # "single"
        element_core, llm_meta_core = extract_element_core_ifc(global_json)

    # Extract quantities
    quantities = extract_quantities_ifc(global_json)

    # Build LcaElement
    lca_element = LcaElement(
        descriptor=descriptor,
        element_core=element_core,
        quantities=quantities,
    )

    # Serialize LcaElement (optional)
    if output_dir is not None:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        stem = getattr(lca_element, "id", None)
        output_path = output_dir / f"{stem}.json"

        json_str = lca_element.model_dump_json(indent=2)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(json_str)
        print(f"LCA element saved to: {output_path}")

    # return combined meta:
    llm_meta = merge_llm_meta(llm_meta_desc, llm_meta_core)

    return lca_element, llm_meta

# ======================================================================================================
# Extract an LcaModel (list of LcaElements) from a pre-processed IFC file
# ======================================================================================================

def extract_lca_model_ifc(
    input_dir: Path,
    output_dir: Optional[Path] = None
) -> LcaModel:
    """
    Extract pre-processed IFC file and create an LcaModel object.
    Runs LLM once per representative element; members reuse descriptor/element_core
    from the representative and override their own quantities & metadata.
    Before extracting an LcaModel object from an IFC file, you need to pre-process
    the IFC file with compas_lca/workflows/raw_extraction/ifc/run_processing.py

    Args:
        input_dir: The root directory of the preprocessed IFC file (found in "temp")
        output_dir: Optional output directory with serialized JSON files for each elemnet
            mirroring the LcaModel fields
            /single_materials
            /layered_elements
            /abstract_components
            /undefined_elements
            /llm_metadata.json # New file, aggregated costs, token usage for whole extraction with chosen model from config.yaml

    Returns:
        - An LcaModel object
        - An optional output directory with serialized LcaElement instances & LLM-metadata
    """

    print(f"\nStarting LCA model extraction from: {input_dir}")

    # directories with representatives for agent-based extraction
    repr_dir_elements = input_dir / "representatives" / "elements"
    repr_dir_multilay = input_dir / "representatives" / "multilayers"    # with multiple layers
    repr_dir_multimat = input_dir / "representatives" / "multimaterials" # with IfcMaterialList
    repr_index_path = input_dir / "metadata" / "representatives.json"
    repr_index = load_json(repr_index_path) # load representatives index (object_type -> {representative, members})

    # rest of elements (members of typed elements) for hardcoded extraction
    all_dir_elements = input_dir / "all" / "elements"       # directly stored json files for each element
    all_dir_multilay = input_dir / "all" / "multilayers"    # directory (with all info and each layer) for each element
    all_dir_multimat = input_dir / "all" / "multimaterials" # with IfcMaterialList (all separate materials for each element)
    
    # build GUID -> path index for "all/"
    index_elements = _build_guid_index(all_dir_elements)
    index_multilay = _build_guid_dir_index(all_dir_multilay, "multilayer")
    index_multimat = _build_guid_dir_index(all_dir_multimat, "multimaterial")

    # initialize outputs
    model_metadata: Optional[ModelMetadata] = None
    single_materials: list[LcaElement] = []
    layered_elements: list[LcaElement] = []
    abstract_components: list[LcaElement] = []
    undefined_elements: list[LcaElement] = []
    all_llm_meta: dict[str, Any] = {}

    # where to write output (optional)
    out_dir_elem     = (Path(output_dir) / "single_materials") if output_dir else None
    out_dir_multilay = (Path(output_dir) / "layered_elements") if output_dir else None
    out_dir_comp     = (Path(output_dir) / "abstract_components") if output_dir else None
    out_dir_undef    = (Path(output_dir) / "undefined_elements") if output_dir else None
    if output_dir:
        for d in [out_dir_elem, out_dir_multilay, out_dir_comp, out_dir_undef]:
            if d is not None:
                d.mkdir(parents=True, exist_ok=True)

    # extract metadata
    model_json_path = input_dir / "metadata" / "model.json"
    model_data = load_json(model_json_path)
    model_metadata = extract_metadata_ifc(model_data)

    # ====================================================
    # iterate representative elements (run LLM once each)
    # ====================================================
    print("Extracting single material elements...")
    for rep_path_elem in repr_dir_elements.glob("*.json"):
        rep_data = load_json(rep_path_elem)
        rep_guid = rep_data.get("metadata", {}).get("global_id")
        object_type = rep_data.get("metadata", {}).get("object_type")

        # Run Agent-based extraction once for representative
        rep_elem, llm_meta = extract_lca_element_ifc(
            input_json=rep_data,
            input_dir=None,
            mode="single",
            output_dir=None,  # serialize representative if requested
        )
        all_llm_meta = merge_llm_meta(all_llm_meta, llm_meta)  # append individual llm metadata to all_llm_meta

        # Get entry type for allocation
        if rep_elem.element_core and hasattr(rep_elem.element_core[0], "entry_type"):
            entry_type = rep_elem.element_core[0].entry_type
        else:
            entry_type = None

        # map entry_type -> (list, output_dir)
        list_and_dir = {
            "material":  (single_materials, out_dir_elem),
            "component": (abstract_components, out_dir_comp),
            "unknown":   (undefined_elements, out_dir_undef),
            None:        (undefined_elements, out_dir_undef),
        }
        # Look up entry_type in the dictionary list_and_dir. If that key doesn’t exist, return the fallback tuple
        rep_list, rep_out_dir = list_and_dir.get(entry_type, (undefined_elements, out_dir_undef))

        # bucket + save representative
        rep_list.append(rep_elem)
        _save_lca_element(rep_elem, rep_out_dir)

        # find its members via representatives.json entry
        entry = repr_index.get(object_type)
        if not entry:
            continue  # no members mapping for this object type. proceed to next rep

        members = entry.get("members", []) or []
        for member in members:
            member_guid = member.get("global_id")
            if not member_guid or member_guid == rep_guid:
                continue  # skip missing guid or the representative itself
            member_path = index_elements.get(member_guid)
            if not member_path:
                continue  # member not present in the "all/elements" index. skip

            # load member and create LcaElement objects without Agent
            member_data = load_json(member_path)

            # update / extract member-specific quantities & metadata without LLM (save API calls)
            m_desc = update_descriptor_ifc(member_data, rep_elem.descriptor)
            m_core = update_matching_core_ifc(member_data, rep_elem.element_core, entry_type)
            m_quant = extract_quantities_ifc(member_data)
            m_elem = rep_elem.model_copy(update={
                "id": uuid4(),
                "descriptor": m_desc,
                "element_core": m_core,
                "quantities": m_quant
            })

            # bucket + save member using the SAME entry_type as the representative
            mem_list, mem_out_dir = list_and_dir.get(entry_type, (undefined_elements, out_dir_undef))
            mem_list.append(m_elem)
            _save_lca_element(m_elem, mem_out_dir)

    # ====================================================
    # iterate representative multilayers (run LLM once each)
    # ====================================================
    print("Extracting multilayer elements...")
    for rep_dir_multilay in _iter_subdirs(repr_dir_multilay):
        # Run Agent-based extraction once for representative
        rep_elem, llm_meta = extract_lca_element_ifc(
            input_json=None,
            input_dir=rep_dir_multilay,
            mode="multilayer",
            output_dir=None,
        )
        all_llm_meta = merge_llm_meta(all_llm_meta, llm_meta)

        # Decide bucket based on ALL MatchingCore.entry_type values
        rep_list, rep_out_dir, routing_entry_type = _pick_multilayer_bucket(
            rep_elem,
            layered_elements, out_dir_multilay,     # layered bucket
            undefined_elements, out_dir_undef       # undefined bucket
        )

        # Bucket + save representative
        rep_list.append(rep_elem)
        _save_lca_element(rep_elem, rep_out_dir)

        # find its members via representatives.json entry
        entry = (
            repr_index.get(rep_elem.descriptor.object_type)
            if (rep_elem and getattr(rep_elem, "descriptor", None) and hasattr(rep_elem.descriptor, "object_type"))
            else None
        )
        if not entry:
            continue

        members = entry.get("members") or []
        for member in members:
            guid = member.get("global_id")
            if not guid:
                continue

            # Use GUID→dir index built for all/multilayers
            member_dir = index_multilay.get(guid) if isinstance(index_multilay, dict) else None
            if not member_dir:
                continue

            # Create member element without re-running LLM (copy/override quantities)
            member_global, _ = _discover_multix_paths(member_dir, "multilayer")
            member_data = load_json(member_global)

            m_desc = update_descriptor_ifc(member_data, rep_elem.descriptor)
            m_core = update_matching_core_ifc(member_data, rep_elem.element_core, routing_entry_type)
            m_quant = extract_quantities_ifc(member_data)

            m_elem = rep_elem.model_copy(update={
                "id": uuid4(),
                "descriptor": m_desc,
                "element_core": m_core,
                "quantities": m_quant,
            })

            # Members follow the SAME bucket as the representative
            mem_list = rep_list
            mem_list.append(m_elem)
            _save_lca_element(m_elem, rep_out_dir)


    # ====================================================
    # iterate representative multimaterials (run LLM once each)
    # ====================================================
    print("Extracting multi-material elements...")
    for rep_dir_multimat in _iter_subdirs(repr_dir_multimat):
        rep_elem, llm_meta = extract_lca_element_ifc(
            input_json=None,
            input_dir=rep_dir_multimat,
            mode="multimaterial",
            output_dir=None,
        )
        all_llm_meta = merge_llm_meta(all_llm_meta, llm_meta)

        rep_list, rep_out_dir, routing_entry_type = _pick_multimaterial_bucket(
            rep_elem,
            abstract_components, out_dir_comp,     # components
            layered_elements,    out_dir_multilay, # multilayer-by-material
            undefined_elements,  out_dir_undef     # undefined
        )

        # save representative
        rep_list.append(rep_elem)
        _save_lca_element(rep_elem, rep_out_dir)

        # Members (if applicable)
        entry = (
            repr_index.get(rep_elem.descriptor.object_type)
            if (rep_elem and getattr(rep_elem, "descriptor", None) and hasattr(rep_elem.descriptor, "object_type"))
            else None
        )
        if not entry:
            continue

        for member in (entry.get("members") or []):
            guid = member.get("global_id")
            if not guid:
                continue

            member_dir = index_multimat.get(guid) if isinstance(index_multimat, dict) else None
            if not member_dir:
                continue

            member_global, _ = _discover_multix_paths(member_dir, "multimaterial")
            member_data = load_json(member_global)

            m_desc = update_descriptor_ifc(member_data, rep_elem.descriptor)
            m_core = update_matching_core_ifc(member_data, rep_elem.element_core, routing_entry_type)
            m_quant = extract_quantities_ifc(member_data)

            m_elem = rep_elem.model_copy(update={
                "id": uuid4(),
                "descriptor": m_desc,
                "element_core": m_core,
                "quantities": m_quant,
            })

            rep_list.append(m_elem)
            _save_lca_element(m_elem, rep_out_dir)
    # =========================
    # aggregated LLM meta
    # =========================
    if output_dir is not None:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        meta_path = output_dir / "llm_metadata.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(all_llm_meta, f, indent=2)
        print(f"Aggregated LLM metadata saved to: {meta_path}")

    # =========================
    # assemble LcaModel
    # =========================
    print("✅ IFC extraction complete — assembling final LCA model.\n")
    lca_model = LcaModel(
        metadata = model_metadata,
        single_materials=single_materials,
        layered_elements=layered_elements,
        abstract_components=abstract_components,
        undefined_elements=undefined_elements,
    )
    return lca_model