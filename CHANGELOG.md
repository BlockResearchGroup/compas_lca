# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Added

* Missing plotting dependencies in `requirements.txt` (`numpy`, `matplotlib`, `plotly`, `seaborn`) — previously only present implicitly in local environments.

### Changed

* `obd_simplify.py` no longer executes at import time; its pipeline is wrapped in `main()` behind an `if __name__ == "__main__"` guard.
* `BaseAgent` docstring usage example converted from doctest prompts to a plain code block so `invoke testdocs` does not execute it.

### Removed

## [1.0.1] 2026-07-21

### Added

* CI workflows aligned with `compas_ifc`: build (3 OS x Python 3.11/3.12), PR changelog check, and tag-triggered release.

### Changed

* `requires-python` corrected to `>=3.11` (the `llm` subpackage uses `typing.Self`); dropped the Python 3.10 classifier.
* Docs and publish CI actions pinned to Python 3.11 (their 3.10 default cannot install the package anymore).

### Removed

## [1.0.0] 2026-07-21

### Added

* Thesis evaluation suite under `thesis/evaluation/`: parameterized multi-LLM benchmark scripts (metrics, aggregation, plotting) that run against a separately distributed data package.
* HiLo case-study configuration profile.
* `CITATION.cff` for citation and archival (DOI) metadata.

### Changed

* Migrated the IFC reader to `compas_ifc` 2.0.0 (with `ifcopenshell` 0.8.4.post1); dependencies pinned in `requirements.txt`.
* IFC relationship extraction (classification, hierarchy, materials) now reads `compas_ifc` 2.0 inverse attributes; output verified byte-identical on both reference models.
* Data paths resolved relative to the repository root, making scripts CWD-independent.
* Console output made Windows-safe (ASCII spinner frames, no non-ASCII glyphs).
* README: install from source (package not yet on PyPI), corrected `epd_parser.yaml` filename, replaced dead documentation link with thesis evaluation and data-availability section.

### Removed

* Empty, unused KBOB extraction stub (`workflows/raw_extraction/kbob`).
* Generated pipeline run output is no longer tracked (gitignored; case-study artifacts live in the external data package).

