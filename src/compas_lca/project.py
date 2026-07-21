import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import Dict

from dotenv import load_dotenv

from compas_lca.helpers import Spinner
from compas_lca.helpers import load_config
from compas_lca.helpers import merge_llm_meta
from compas_lca.workflows.calculation import calculate_impacts
from compas_lca.workflows.calculation import summarize_elements
from compas_lca.workflows.calculation import summarize_impacts
from compas_lca.workflows.enrich import create_boq_enriched
from compas_lca.workflows.enrich import enrich_concrete_strength
from compas_lca.workflows.enrich import enrich_stud_ratio
from compas_lca.workflows.matching import match_lca_model
from compas_lca.workflows.plots import create_plots
from compas_lca.workflows.plots import sankey_classification
from compas_lca.workflows.raw_extraction.ifc.ifc_boq import extract_lca_model_boq
from compas_lca.workflows.raw_extraction.ifc.ifc_boq import process_ifc_model_boq
from compas_lca.workflows.raw_extraction.ifc.ifc_extraction import extract_lca_model_ifc
from compas_lca.workflows.raw_extraction.ifc.ifc_processing import process_ifc_model
from compas_lca.workflows.raw_extraction.ifc.ifc_representatives import create_representatives
from compas_lca.workflows.reporting import run_flag_report

load_dotenv()

# Resolve repo root so data/ paths work regardless of CWD.
# Assumes: <repo>/src/compas_lca/project.py  ->  repo = 3 parents up
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


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
            raise KeyError(f"config.yaml must define required keys: {', '.join(missing)}.")

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
        ifc_dir: Path = _REPO_ROOT / "data" / "building_model",
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
            create_representatives(input_dir=self.path / "01_processed", output_dir=self.path / "02_representatives", cfg=self.config)
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
            extract_lca_model_boq(input_csv_path=self.path / "01_processed/BoQ_processed_dissected.csv", output_dir=self.path / "03_extracted")
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
            concrete_strength_enabled = bool(self.config.get("concrete_strength_class", False))
            if concrete_strength_enabled:
                print("")
                print("Enriching concrete strength classes...")
                meta = enrich_concrete_strength(
                    preprocessed_all_dir=self.path / "01_processed",
                    extracted_dir=self.path / "03_extracted",
                    enriched_dir=self.path / "04_enriched",
                )
                all_llm_meta = merge_llm_meta(all_llm_meta, meta)

            stud_ratio_enabled = bool(self.config.get("stud_ratio", False))
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
            # ---- ensure BoQ_enriched.csv exists (mandatory artifact) ----
            boq_enriched_path = self.path / "04_enriched" / "BoQ_enriched.csv"
            if not boq_enriched_path.exists():
                (self.path / "04_enriched").mkdir(parents=True, exist_ok=True)
                create_boq_enriched(
                    input_dir=self.path / "03_extracted",
                    enriched_dir=self.path / "04_enriched",
                )

            # Pick LcaElement input root
            input_root = self._matching_input_root()

            # ---- pull settings from config.yaml (top-level keys) ----
            score_threshold = float(self.config.get("score_threshold", 0.5))
            top_k = int(self.config.get("top_k_matches", 10))
            include_explain = bool(self.config.get("include_explain", False))

            # (optional) inventory dir in config later if other inventories are added
            inventory_dir = _REPO_ROOT / "data" / "lca_database" / "oekobaudat_2024-I"

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
            spinner = Spinner("Creating impact reports... ")
            spinner.start()

            report_cfg = self.config.get("impact_report", {}) or {}
            indicators = report_cfg.get("indicators") or ["GWPtotal", "GWPbiogenic"]
            net_stages = report_cfg.get("net_stages") or ["A1-A3", "A4", "C1", "C2", "C3", "D"]

            _default_inv = _REPO_ROOT / "data" / "lca_database" / "oekobaudat_2024-I"
            epd_root = Path(self.config.get("inventory_dir", str(_default_inv)))

            # Define report root
            report_root = self.path / "06_report"
            report_root.mkdir(parents=True, exist_ok=True)

            # Calculate (will create per-indicator subfolders)
            calculate_impacts(
                project_root=self.path,
                epd_root=epd_root,
                indicators=list(indicators),
                net_stages=list(net_stages),
                out_dir=report_root,
            )

            # Summaries + collect produced directories
            produced_dirs: dict[str, Path] = {}

            for ind_name in indicators:
                safe_ind = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in str(ind_name))
                ind_dir = report_root / safe_ind

                if not ind_dir.exists():
                    continue

                # write summaries and aggregate layers to elements
                for csv_path in sorted(ind_dir.glob("all_impacts_*.csv")):
                    summarize_impacts(csv_path, ind_dir)
                for csv_path in sorted(ind_dir.glob("object_type_impacts_*.csv")):
                    summarize_impacts(csv_path, ind_dir)
                for csv_path in sorted(ind_dir.glob("all_summary_dissected_*.csv")):
                    summarize_elements(csv_path)

                # Mark as produced only if there is at least one impacts file
                if any(ind_dir.glob("*_impacts_*.csv")):
                    produced_dirs[str(ind_name)] = ind_dir.resolve()

                # Plots per indicator
                try:
                    create_plots(ind_dir)
                except Exception as e:
                    print(f"[!]  Plotting failed for {ind_name} in {ind_dir}: {e}")

            # Create sankey diagram and flag report
            try:
                gwp_dir = report_root / "GWPtotal"

                sankey_csv = gwp_dir / "all_summary_dissected_GWPtotal.csv"
                flag_csv_1 = gwp_dir / "object_type_summary_dissected_GWPtotal.csv"
                flag_csv_2 = gwp_dir / "all_impacts_GWPtotal.csv"

                missing = []
                if not sankey_csv.exists():
                    missing.append(f"Expected mandatory Sankey input not found: {sankey_csv}")
                if not flag_csv_1.exists():
                    missing.append(f"Expected mandatory flag input not found: {flag_csv_1}")
                if not flag_csv_2.exists():
                    missing.append(f"Expected mandatory flag input not found: {flag_csv_2}")

                if missing:
                    raise FileNotFoundError(" | ".join(missing))

                sankey_classification(
                    csv_path=sankey_csv,
                    output_dir=report_root,  # write to 06_report root
                )
                run_flag_report(
                    input_csv_objecttype=flag_csv_1,
                    input_csv_elements=flag_csv_2,
                    output_dir=report_root,  # write to 06_report root
                )

            except Exception as e:
                print(f"[!]  Sankey classification / flag report generation failed: {e}")

            # --- NEW: copy metadata into 06_report/metadata (last action) ---
            report_root = self.path / "06_report"  # already created above, safe to re-reference
            dst_meta = report_root / "metadata"
            dst_meta.mkdir(parents=True, exist_ok=True)

            src_meta_enriched = self.path / "04_enriched" / "metadata"
            src_meta_extracted = self.path / "03_extracted" / "metadata"

            # Priority: 04_enriched/metadata if it exists, else 03_extracted/metadata
            src_meta = src_meta_enriched if src_meta_enriched.is_dir() else src_meta_extracted

            if src_meta.is_dir():
                for p in src_meta.iterdir():
                    if p.name == "model_metadata.json":
                        continue
                    target = dst_meta / p.name
                    if p.is_dir():
                        shutil.copytree(p, target, dirs_exist_ok=True)
                    else:
                        shutil.copy2(p, target)

            # Always copy 01_processed/metadata/model.json into 06_report/metadata
            model_src = self.path / "01_processed" / "metadata" / "model.json"
            if model_src.exists():
                shutil.copy2(model_src, dst_meta / "model.json")
            else:
                print(f"[!]  model.json not found at: {model_src}")

            spinner.stop()

            # Single consolidated print at the end
            if produced_dirs:
                print("")
                for name, p in produced_dirs.items():
                    print(f"Created indicator reports for {name} in: {p}")
                print("")
            else:
                print(f"No indicator reports created in: {report_root.resolve()}")

        except FileNotFoundError as e:
            raise MissingInput(str(e)) from e

        return self

    # ---------- run entire ----------

    def run_all(
        self,
        *,
        ifc_dir: Path = _REPO_ROOT / "data" / "building_model",
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
