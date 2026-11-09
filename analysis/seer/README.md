# SEER comparison - recovered original code

The October 20-22, 2026 SEER work was done in a Codex session on Md's Mac, not in Claude Code.
Md ran each cell in the All of Us Workbench and pasted the outputs back.
That transcript (`~/.codex/sessions/2026/10/02/rollout-2026-10-02T09-55-08-01a0fce5-....jsonl`) holds every executed cell, so the code here is recovered, not reconstructed.
Each script names its source message and timestamp.

## What "recovered" means here

- All BigQuery SQL in `sql.py` is character-for-character identical to the executed cells, with only the CDR name passed in.
  The 2023 query is still built from the 2025 query by the same two asserted string replacements.
- Python comparison, sensitivity, summary, plotting and report logic keeps the original checks, columns, labels and ordering.
- On identical synthetic inputs, the original cells and these scripts produce byte-identical CSVs, a pixel-identical figure and the same masked-point count.
  The report builder reproduces the October 22 HTML byte for byte from the original inputs.
  See `docs/EXPORT_REVIEW.md`.
- Recovery changes, applied everywhere: paths come from `config/params.env`; results go to metadata files instead of being printed; expected totals that were hard-coded literals (roster size, coverage totals, concept counts) are checked against saved inputs or recorded in metadata; GCS copies are left to `setup/99_backup.sh`.
  Per-script exceptions are listed in each docstring and in `docs/RECONSTRUCTION_DIFFS.md`.

## Order

| Step | Module | Historical cells | Queries? |
|---|---|---|---|
| Coverage preflight | `analysis.00_ehr_coverage_check schema`, then `run` | msgs 2397, 2409, 2419 | yes, 5 GiB cap |
| Freeze Rita's mapping | `analysis.seer.00_rita_mapping` | msgs 2439, 2451 | no |
| Vocabulary audit | `phenotypes.concept_audit vocabulary` | msgs 2472, 2482 | yes, 2 GiB |
| Replacement audit | `phenotypes.concept_audit replacements` | msgs 2494, 2514 | yes, 4 GiB |
| Replacement impact | `phenotypes.concept_audit impact` | msg 2524, dry run only, never executed | refused by default |
| Birth-year baseline | `analysis.seer.01_prevalence_counts baseline` | msgs 2554, 2564 | yes, 6 GiB |
| 2025 v9-cutoff prevalence | `analysis.seer.01_prevalence_counts v9cutoff` | msgs 2594, 2604 | yes, 6 GiB |
| 2023 SEER-aligned prevalence | `analysis.seer.01_prevalence_counts seer2023` | msgs 2725, 2735 | yes, 6 GiB |
| Nine comparisons | `analysis.seer.02_compare` | msgs 2735-3137, 3149 | no |
| Coverage sensitivity | `analysis.seer.05_coverage_sensitivity` | msg 3149 | no |
| Figure | `analysis.seer.06_plot` | msg 3161 | no |
| Cancer-date sensitivity | `analysis.seer.03_cancer_date_sensitivity run`, then `summary` | msgs 3187, 3199, 3233, 3245 | yes, 6 GiB |
| Ovarian scope query | `analysis.seer.04_ovarian_scope` | msgs 3267, 3305, 3317 | yes, 6 GiB |
| Ovarian scope comparison | `analysis.seer.07_ovarian_scope_comparison` | msg 3317 | no |
| Report | `reports.build_seer_report` | Mac builder, msg 3394 | no |

`RUN_QUERIES=0` (the default) writes SQL and dry-run metadata only.
The step numbers are file names, not the historical order: the figure (06) was drawn before the cancer-date sensitivity (03) was run.

## Two different sensitivity analyses

- **Coverage sensitivity (step 05, dashed lines in the figure):** at least two distinct dates of ANY diagnosis.
  This changes the denominator and the cases within it.
- **Cancer-date sensitivity (step 03):** at least two distinct dates within the SAME cancer group.
  The denominator stays the primary population with at least one dated condition.
- The figure shows only the coverage sensitivity.

## Fixed rules

- January 1, 2023 complete prevalence, with diagnosis dates strictly before it.
  The January 1, 2025 run is a separate initial baseline.
- Completed age from `birth_datetime`, adults aged 20 and over.
  Only 40-64, 65-74 and 75+ are compared, because SEER under-40 includes children.
- Death comes from CDR `aou_death`, using the earliest primary record.
  A death on or before the reference date is excluded.
  No death record does not prove survival.
- Sex at birth is the CDR concept name.
  Breast and ovary are Female only, prostate is Male only, and other sites are compared for both sexes.
- Colorectal SEER includes the appendix.
  Kidney is a flagged mismatch: SEER adds the renal pelvis.
  Melanoma scope review is pending.
- `<` SEER values are upper bounds with no point ratio, and every ratio is approximate.
- No age standardization, confidence intervals or final phenotype validation was done.
