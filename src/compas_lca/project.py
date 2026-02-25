import json

from dataclasses import dataclass

from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from typing import Any
from typing import Dict

from compas_lca.helpers import load_config
from compas_lca.helpers import merge_llm_meta

from compas_lca.workflows.matching import match_lca_model

from compas_lca.workflows.calculation import calculate_impacts
from compas_lca.workflows.calculation import summarize_impacts

from compas_lca.workflows.raw_extraction.ifc.ifc_processing import process_ifc_model

from compas_lca.workflows.raw_extraction.ifc.ifc_representatives import create_representatives

from compas_lca.workflows.raw_extraction.ifc.ifc_extraction import extract_lca_model_ifc

from compas_lca.workflows.raw_extraction.ifc.ifc_boq import process_ifc_model_boq
from compas_lca.workflows.raw_extraction.ifc.ifc_boq import extract_lca_model_boq

from compas_lca.workflows.enrich import create_boq_enriched
from compas_lca.workflows.enrich import enrich_concrete_strength
from compas_lca.workflows.enrich import enrich_stud_ratio

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

    # ---------- internal helper ----------

    def _cfg_get(self, key: str, default: Any) -> Any:
        return self.config.get(key, default)

    def _has_any_json(self, root: Path) -> bool:
        if not root.exists() or not root.is_dir():
            return False
        return any(root.rglob("*.json"))

    def _matching_input_root(self) -> Path:
        enriched = self.path / "04_enriched"
        extracted = self.path / "03_extracted"
        if self._has_any_json(enriched):
            return enriched
        return extracted

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
        ifc_cfg = None
        if "ifc_extraction" in self.config and isinstance(self.config["ifc_extraction"], dict):
            ifc_cfg = self.config["ifc_extraction"]
        else:
            tmp = {k: v for k, v in self.config.items() if isinstance(k, str) and k.startswith("Ifc")}
            if tmp:
                ifc_cfg = tmp
        process_ifc_model(ifc_dir, self.path / "01_processed", exclude_none, config=ifc_cfg)
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
                input_csv_path = self.path / "01_processed/BoQ_processed_dissected.csv", 
                output_dir = self.path / "03_extracted"
            )
        except FileNotFoundError as e:
            raise MissingInput(str(e)) from e
        return self
    
    def enrich_building_data(self) -> "Project":
        """
        Step 04: (Optional) Enrich extracted data with LLM inferences.
        Controlled via config.yaml flags.
        """
        try:
            all_llm_meta: Dict[str, Any] = {}

            create_boq_enriched(
                input_dir=self.path / "03_extracted",
                enriched_dir=self.path / "04_enriched",
                )
            
            concrete_strength_enabled = bool(
                self.config.get("concrete_strength_class", False)
            )
            if concrete_strength_enabled:
                print("")
                print("Enriching concrete strength classes...")
                meta = enrich_concrete_strength(
                    preprocessed_all_dir=self.path / "01_processed",
                    extracted_dir=self.path / "03_extracted",
                    enriched_dir=self.path / "04_enriched",
                )
                all_llm_meta = merge_llm_meta(all_llm_meta, meta)

            stud_ratio_enabled = bool(
                self.config.get("stud_ratio", False)
            )
            if stud_ratio_enabled:
                print("")
                print("Enriching stud ratios...")
                meta = enrich_stud_ratio(
                    preprocessed_all_dir=self.path / "01_processed",
                    extracted_dir=self.path / "03_extracted",
                    enriched_dir=self.path / "04_enriched",
                )
                all_llm_meta = merge_llm_meta(all_llm_meta, meta)

            meta_dir = self.path / "04_enriched" / "metadata"
            meta_dir.mkdir(parents=True, exist_ok=True)

            llm_meta_path = meta_dir / "llm_metadata_enrichment.json"
            llm_meta_path.write_text(json.dumps(all_llm_meta, indent=2), encoding="utf-8")
            
        except FileNotFoundError as e:
            raise MissingInput(str(e)) from e

        return self
    
    def match_with_inventory(self) -> "Project":
        """
        Step 05: Match LcaElements with inventory items.
        Uses 04_enriched if populated, otherwise 03_extracted.
        Matching settings are read from config.yaml (with defaults).
        """
        try:
            input_root = self._matching_input_root()

            # ---- pull settings from config.yaml (top-level keys) ----
            score_threshold = float(self.config.get("score_threshold", 0.5))
            top_k = int(self.config.get("top_k_matches", 10))
            include_explain = bool(self.config.get("include_explain", False))

            # (optional) inventory dir in config later if other inventories are added
            inventory_dir = Path("data/lca_database/oekobaudat_2024-I")

            match_lca_model(
                inventory_dir=inventory_dir,
                input_root=input_root,
                output_root=self.path / "05_matched",
                top_k=top_k,
                include_explain=include_explain,
                score_threshold=score_threshold,
            )

        except FileNotFoundError as e:
            raise MissingInput(str(e)) from e

        return self

    def generate_report(self) -> "Project":
        """
        Step 06: Generate impact reports based on matched results.
        Reads indicators + net stages from config.yaml -> impact_report.

        Additionally:
        - For each impacts_*.csv in <project_root>/06_report,
          generate a summary_*.csv in the SAME directory.
        """
        try:
            report_cfg = self.config.get("impact_report", {}) or {}

            indicators = report_cfg.get("indicators") or ["GWPtotal", "GWPbiogenic"]
            net_stages = report_cfg.get("net_stages") or ["A1-A3", "A4", "C1", "C2", "C3", "D"]

            epd_root = Path(self.config.get("inventory_dir", "data/lca_database/oekobaudat_2024-I"))

            calculate_impacts(
                project_root=self.path,
                epd_root=epd_root,
                indicators=list(indicators),
                net_stages=list(net_stages),
            )

            report_dir = self.path / "06_report"
            if not report_dir.exists():
                raise FileNotFoundError(f"Expected report directory not found: {report_dir}")

            for csv_path in sorted(report_dir.glob("all_impacts_*.csv")):
                summarize_impacts(csv_path, report_dir)
            for csv_path in sorted(report_dir.glob("agg_impacts_*.csv")):
                summarize_impacts(csv_path, report_dir)

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
            .enrich_building_data()
            .match_with_inventory()
            .generate_report()
        )
