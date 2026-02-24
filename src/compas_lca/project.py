from dataclasses import dataclass

from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from typing import Any
from typing import Dict

from compas_lca.helpers import load_config

from compas_lca.workflows.raw_extraction.ifc.ifc_processing import process_ifc_model

from compas_lca.workflows.raw_extraction.ifc.ifc_representatives import create_representatives

from compas_lca.workflows.raw_extraction.ifc.ifc_extraction import extract_lca_model_ifc

from compas_lca.workflows.raw_extraction.ifc.ifc_boq import process_ifc_model_boq
from compas_lca.workflows.raw_extraction.ifc.ifc_boq import extract_lca_model_boq

from compas_lca.workflows.enrich import enrich_lca_model
class ProjectError(RuntimeError):
    """Base error for project/pipeline failures."""

class MissingInput(ProjectError):
    pass

@dataclass(frozen=True)
class Project:
    """
    Represents exactly one LCA project rooted at `path`.

    Folder structure is created by the pipeline functions themselves.
    """
    path: Path
    config: Dict[str, Any]

    @classmethod
    def from_config_yaml(cls, config_path: Path = Path("config.yaml")) -> "Project":
        try:
            cfg = load_config(config_path)
        except TypeError:
            cfg = load_config()

        required_keys = ("project_folder", "model")
        missing = [k for k in required_keys if k not in cfg]
        if missing:
            raise KeyError(
                f"config.yaml must define required keys: {', '.join(missing)}."
            )

        root = Path(cfg["project_folder"]).expanduser().resolve()
        return cls(path=root, config=cfg)


    @property
    def name(self) -> str:
        return self.path.name

    # ---------- project pipeline steps ----------

    def preprocess_ifc(
        self,
        *,
        ifc_dir: Path = Path("data/building_model"),
        exclude_none: bool = True,
    ) -> "Project":
        """
        Step 01: preprocess IFC and write into the project root folder.
        """
        process_ifc_model(ifc_dir, self.path / "01_processed", exclude_none)
        process_ifc_model_boq(self.path / "01_processed")
        return self

    def select_representatives(self) -> "Project":
        """
        Step 02: select and copy unique representative elements for AI-based extraction.
        """
        try:
            create_representatives(
                input_dir=self.path / "01_processed",
                output_dir=self.path / "02_representatives", 
                cfg=self.config
                )
        except FileNotFoundError as e:
            raise MissingInput(str(e)) from e
        return self
    
    def extract_building_data(self) -> "Project":
        """
        Step 03: AI-based extraction of representative data & updated BoQ
        """
        try:
            extract_lca_model_ifc(
                input_dir_all=self.path / "01_processed",
                input_dir_repr=self.path / "02_representatives",
                output_dir=self.path / "03_extracted",
            )
            extract_lca_model_boq(
                input_csv_path = self.path / "01_processed/BoQ_01_dissected.csv", 
                output_dir = self.path / "03_extracted"
            )
        except FileNotFoundError as e:
            raise MissingInput(str(e)) from e
        return self
    
    def enrich_building_data(self) -> "Project":
        """
        Step 04: (Optional) Enrich extracted data with additional sources (e.g. material properties, quantities).
        """
        try:
            enrich_lca_model()
        except FileNotFoundError as e:
            raise MissingInput(str(e)) from e
        return self

    # ---------- run entire ---------- 

    def run_all(
        self,
        *,
        ifc_dir: Path = Path("data/building_model"),
        exclude_none: bool = True,
    ) -> "Project":
        return (
            self.preprocess_ifc(ifc_dir=ifc_dir, exclude_none=exclude_none)
            .select_representatives()
            .extract_building_data()
        )
