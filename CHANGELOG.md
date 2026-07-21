# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

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

