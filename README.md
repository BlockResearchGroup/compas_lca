# compas_lca

bim-lca integration

AI-based Life Cycle Assessment (LCA) report generator for IFC building models.

`compas_lca` normalizes building data (from IFC) and environmental data (EPDs) into a unified schema that enables precise, customizable, and deterministic matching based on semantic and functional constraints.

In conventional BIM and environmental data schemas, critical classification and attribute information is often distributed across semi-structured and highly variable representations. `compas_lca` extracts and consolidates relevant attributes into an overlapping normalized format, enabling deterministic building-element to EPD matching and reproducible LCA report generation.

## Installation

Stable releases can be installed from PyPI.

```bash
pip install compas_lca
```

To install the latest version for development, do:

```bash
git clone https://github.com/BlockResearchGroup/compas_lca.git
cd compas_lca
pip install -e ".[dev]"
```
# Setup

# 1. Download Dependencies

Download the [LCA database](https://drive.google.com/file/d/1f3A3flhQXG1KYwYv7hetk_ZY7b31kBg0/view?usp=drive_link)

Unzip the archive and move the extracted folder into the `data` directory such that the following path exists:
```bash
data/lca_database
```
# 2. Environment Configuration
* Add your API key to a `.env` file in the project root
* Specify project configurations in `config.yaml`
* Supported indicator values in `config.yaml` can be found in `src/compas_lca/inventory/constants.py` under the `OBD_INDICATOR_NAME` list.

# 3. Entry Point
All workflows are executed via:
```bash
python scripts/0_menu.py
```
## Building Model Extraction Workflow
* Drag and drop your IFC file into: `data/building_model`
* Configure relevant parameters in `config.yaml`
* Run `scripts/0_menu.py`
* Execute action points **01a to 01f** sequentially.

This workflow extracts, normalizes building model data for deterministic EPD matching and generates a report per configured emissions indicator.

NOTE: The matching parameters (score threshold and top_k matches) can be retroactively changed. Exit the menu, adjust the parameters, relaunch the menu and run action steps **01e and 01f**. This requires no API usage. Create a backup of initial files (if you want to compare results), as previous files will be overwritten!

## Environmental Data Extraction Workflow
* Review `oekobaudat_remaining.csv`
* Add UUIDs of selected elements to `epd_parser.json`
* Run `scripts/0_menu.py`
* Execute action points **02a to 02c** sequentially.

This workflow parses and integrates additional Environmental Product Declarations (EPDs) into the existing LCA database.

## Documentation

For further "getting started" instructions, a tutorial, examples, and an API reference,
please check out the online documentation here: [compas_lca docs](https://BlockResearchGroup.github.io/compas_lca)

## Issue Tracker

If you find a bug or if you have a problem with running the code, please file an issue on the [Issue Tracker](https://github.com/BlockResearchGroup/compas_lca/issues).
