# Code export review — November 8, 2026

## Scope and result

Code and documentation were exported into this folder. No participant dataset, notebook output, genotype file or results table was read, copied or included. No cloud query, analysis, download, carrier extraction, model fitting, report rendering or Git publication was run. Only source inspection, local code edits and synthetic verification were performed.

Recovered report/layout and survey-query code were adapted to external inputs. Most other requested steps are explicitly labeled reconstructions from session records and supplied code. They are not claimed to be byte-identical original notebook cells. No missing version was invented. See MANIFEST, RECONSTRUCTION_DIFFS, RECOVERY_GAPS and INPUTS.

## Verification

- `python -m pytest tests -q`: **14 passed** (synthetic fixtures only).
- `python -m py_compile` on every Python source: **50 files passed**.
- `bash -n` on every `.sh`: **15 files passed**; config and pre-commit hook also passed.
- Plain `python` was absent on this Mac. An isolated temporary environment with existing system packages supplied the command. No package installation or Workbench environment change was made.
- Every literal exported runtime environment variable resolves to a declaration in config/params.env; Python scripts contain no print calls.
- Source inspection found no embedded actual participant IDs or observed small-cell results. Any small numbers in synthetic tests, thresholds, concept codes and layout code are not observed participant counts.
- No CSV/TSV/Parquet, notebook, JSON payload, rendered HTML, image, spreadsheet, genotype file, log, database or result table is present. Generated caches and Finder metadata were removed. The existing public panel BED and gene-symbol text remain configuration; their coordinate convention must be confirmed before extraction.
- Hail, BigQuery, fastVEP, full plotting/report rendering and analysis behavior were **not** executed or end-to-end verified. Syntax/tests do not establish reproduction of historical results or policy clearance.

## Every added file

- `analysis/__init__.py`
- `analysis/seer/01_prevalence_counts.py`
- `analysis/seer/02_compare.py`
- `analysis/seer/03_cancer_date_sensitivity.py`
- `analysis/seer/04_ovarian_scope.py`
- `analysis/seer/05_coverage_sensitivity.py`
- `analysis/seer/06_plot.py`
- `analysis/seer/07_ovarian_scope_comparison.py`
- `analysis/seer/__init__.py`
- `analysis/seer/reference.py`
- `carriers/__init__.py`
- `carriers/extract_vat_panel.py`
- `carriers/reconcile_variants.py`
- `carriers/vds/01_roster_check.py`
- `carriers/vds/02_variant_access.py`
- `carriers/vds/03_sparse_carrier_qc.py`
- `carriers/vds/04_reference_call_pilot.py`
- `carriers/vds/__init__.py`
- `carriers/vds/common.py`
- `docs/EXPORT_REVIEW.md`
- `docs/INPUTS.md`
- `docs/MANIFEST.md`
- `docs/RECONSTRUCTION_DIFFS.md`
- `docs/RECOVERY_GAPS.md`
- `phenotypes/__init__.py`
- `phenotypes/concept_audit.py`
- `phenotypes/extract_clinical_family_history.py`
- `phenotypes/extract_family_survey.py`
- `phenotypes/family_history.py`
- `phenotypes/phecode/01_extract_dates.py`
- `phenotypes/phecode/02_evidence_tiers.py`
- `phenotypes/phecode/03_distinct_date_flags.py`
- `phenotypes/phecode/__init__.py`
- `phenotypes/survey_control_screen.py`
- `reports/README.md`
- `reports/__init__.py`
- `reports/build_pan_cancer_report.py`
- `reports/disclosure.py`
- `reports/pan_cancer_template.py`
- `requirements.txt`
- `tests/test_export.py`
- `workflow/__init__.py`
- `workflow/runtime.py`

## Every changed file

- `.gitignore`
- `README.md`
- `acmg_fastvep/10_build_sa_clinvar.sh`
- `acmg_fastvep/11_build_sa_gene_level.sh`
- `acmg_fastvep/12_build_sa_gnomad_region.sh`
- `acmg_fastvep/13_build_sa_spliceai_phylop.sh`
- `acmg_fastvep/14_build_sa_revel.sh`
- `acmg_fastvep/15_build_sa_repeatmasker.sh`
- `acmg_fastvep/20_verify_stack.sh`
- `acmg_fastvep/30_run_acmg_per_chr.sh`
- `analysis/00_ehr_coverage_check.py`
- `analysis/01_clinvar_plp_carrier_freq.py`
- `analysis/02_spliceai_candidates.py`
- `analysis/03_association.py`
- `analysis/legacy_v8/cohort_expansion_v9.py`
- `analysis/legacy_v8/mutyh_second_primary_contamination.py`
- `analysis/legacy_v8/secondary_cancer_full_cohort.py`
- `analysis/penetrance/README.md`
- `analysis/penetrance/penetrance.py`
- `analysis/seer/README.md`
- `carriers/40_extract_vat_panel.sh`
- `carriers/41_concordance_by_carrier_count.py`
- `carriers/42_v8_carriers_from_variants.py`
- `carriers/keys.py`
- `carriers/vds/README.md`
- `config/params.env`
- `docs/DATA_POLICY.md`
- `docs/DECISIONS.md`
- `docs/TODO_FROM_CODEX.md`
- `phenotypes/README.md`
- `phenotypes/omop_cancer_cases.py`
- `tests/test_keys.py`

## Recovery gaps and sharing

`docs/RECOVERY_GAPS.md` lists missing notebook cells, approved maps, source/helper versions, timestamps and internal report payloads, along with what is needed to restore them. Full carrier extraction and final genotype QC/penetrance were not completed historically and are not represented as completed exports.

Candidate aggregate filenames are listed there for later Workbench disclosure review; no contents are included and no table is certified safe. The stated policy excludes **1–20 inclusive**, so a count of exactly 20 cannot be released under that rule. Review derived differences, complements and overlapping tables too.


## SEER code recovery review - November 9, 2026

### Scope and result

This was code and documentation recovery only.
No analysis, BigQuery query, genotype read, download, publication, commit or push was performed.
No participant data, notebook output, participant ID, observed small count or private concept list was copied into the repository.

The original October 20-22 SEER cells were found in the Codex session transcript on this Mac (MANIFEST).
The user's brief said Claude Code sessions, but those hold no SEER code.
They replace the November 8 SEER reconstructions.
Every recovered script names its source message, states its purpose, inputs, outputs and decisions, and lists any recovery change.

### Equivalence evidence (local, scratch directory outside the repo, synthetic data only)

- Every recovered BigQuery query in `analysis/seer/sql.py` is character-identical to the executed cell. The fully rendered 2025 and 2023 prevalence queries are identical too.
- The original cells (BigQuery client stubbed, synthetic aggregates and SEER-format files) and the recovered scripts were run on the same inputs:
  - the consolidated comparisons, coverage sensitivity, cancer-date sensitivity, cancer-date summary and ovarian-scope tables were byte-identical;
  - the figure PNG was pixel-identical (3496 x 2852), with the same masked-point count;
  - the mapping CSV from a synthetic workbook was byte-identical.
- With the historical local inputs, `reports.build_seer_report` rendered a page byte-identical to `~/Agents/research_report/seer_validation_session_2026-10-21.html`.
  Those inputs were read in place and not copied.
- A temporary Python 3.9 virtual environment in the scratch directory supplied matplotlib, pyarrow and openpyxl for these checks.
  No Workbench environment was touched.

### Verification

- `python -m pytest tests -q`: **24 passed** (14 existing and 10 new, synthetic only). Run with the system `python3` (plain `python` is absent on this Mac) and again in the scratch virtual environment.
- `python -m py_compile` on every Python file: **56 files passed** (bytecode written outside the repo).
- `bash -n` on every `.sh` file: **15 passed**; `config/params.env` and `hooks/pre-commit` also passed.
- Every environment variable read by the code is declared in `config/params.env`.
- No CSV/TSV/Parquet/JSON/notebook/HTML/image/PDF/spreadsheet/SQLite/log/archive file is in the folder.
  No `__pycache__`, `.pytest_cache` or `.DS_Store` is present.
- No ovarian-scope concept IDs appear in code.
  Historical totals (roster, coverage, EHR flag) are not hard-coded in Python.
  The only 7-digit number in changed source is a JAMA article ID in a link.
- BigQuery, Hail and Workbench execution were **not** run. Equivalence on synthetic data does not prove the same results on All of Us data.

### Added files

- `analysis/seer/00_rita_mapping.py`
- `analysis/seer/common.py`
- `analysis/seer/sql.py`
- `reports/build_seer_report.py`
- `reports/seer_template.py`
- `tests/test_seer_recovered.py`

### Changed files

- `README.md`
- `analysis/00_ehr_coverage_check.py`
- `analysis/seer/01_prevalence_counts.py`
- `analysis/seer/02_compare.py`
- `analysis/seer/03_cancer_date_sensitivity.py`
- `analysis/seer/04_ovarian_scope.py`
- `analysis/seer/05_coverage_sensitivity.py`
- `analysis/seer/06_plot.py`
- `analysis/seer/07_ovarian_scope_comparison.py`
- `analysis/seer/README.md`
- `analysis/seer/reference.py`
- `config/params.env`
- `docs/DECISIONS.md`
- `docs/EXPORT_REVIEW.md`
- `docs/INPUTS.md`
- `docs/MANIFEST.md`
- `docs/RECONSTRUCTION_DIFFS.md`
- `docs/RECOVERY_GAPS.md`
- `docs/TODO_FROM_CODEX.md`
- `phenotypes/README.md`
- `phenotypes/concept_audit.py`
- `reports/README.md`
- `requirements.txt`
- `tests/test_export.py`
- `workflow/runtime.py`
