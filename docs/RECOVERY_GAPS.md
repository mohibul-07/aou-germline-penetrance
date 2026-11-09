# What could not be recovered

| Missing item | What is needed inside Workbench |
|---|---|
| Exact historical notebook cells (non-SEER) | SEER cells are recovered from the Codex transcript. For other branches, restore `notebook/a_phenotype_extraction.ipynb` and clear all outputs before code review; the October 22 record says its final save/copy was never confirmed. No notebook was read or copied. |
| Lead for the non-SEER gaps | The same Codex transcript holds 133 Python/Bash cells from October 2-15 (PheTK/phecode, family-history and survey, VDS/Hail, ClinVar/fastVEP checks). They were not reviewed in this SEER-only task and could replace several reconstructions below. |
| Exact PheTK extraction/map version | Installed package metadata, original ICD→phecodeX map and saved selected-code tiers. Reconstructed malignant rules are available; fine-grained history/in-situ/other labels need the approved map. |
| Raw EHR family-history extraction and review flags | Original reviewed concept/value mapping, PPI/survey exclusion query, and flag-building cell. Final full-roster grouping code is provided; raw text negation and additional-review membership are not guessed. |
| Historical schema adapters | Original Parquet schemas and cell source to map them to documented reconstruction inputs. No local participant data was opened for schema discovery. |
| ~~Literal SEER SQL and plot builder~~ | **Recovered November 9, 2026** from the Codex transcript; see `analysis/seer/README.md`. Standardization and confidence intervals were never run, so there is no code to recover for them. |
| Ovarian scope concept classes | The historical cell embedded the 8/3/1/1 concept-ID lists. They are deliberately not copied here because they are part of Rita's private mapping. Restore `OVARY_SCOPE_MAPPING` from Workbench `rita_ovarian_scope_audit_2023_metadata.json`. |
| SEER export hashes and data release | No checksum was recorded for the nine SEER exports. The SEER submission/release name is not printed in them. Hash the originals in `00_reference/seer/` and record the SEER*Explorer data release if it can still be identified. |
| Per-site SEER comparison CSVs | Recovered `02_compare` writes the consolidated table directly. The nine per-site intermediate CSVs (and their extra `difference_percentage_points` and kidney/melanoma flag columns) are not regenerated; the historical files remain in Workbench. |
| Superseded SEER report builders and data writers | The first October 21 builder (msg 2952), the separate October 22 review builder (msg 3342, written to `/private/tmp` and no longer on disk) and the session-data writer (msg 2945) exist only in the transcript. They are superseded and full of result values, so they were not exported. |
| SEER report payloads | `seer_review_data_2026-10-22.json`, the result-text slots and the Workbench PNG stay outside the repo; the builder needs them to render. |
| Cancer-date cell stall | The original cell finished the query but stopped while printing; the cause was never established. The recovery cell called builtins explicitly. Not reproducible from the transcript. |
| Notebook-side package versions for SEER cells | google-cloud-bigquery, pyarrow, openpyxl and matplotlib versions were not recorded. |
| Exact VDS pilot target list and interval code | Restore the saved pilot metadata/keys inside Workbench. Keys and allele-match metadata remain external. New interval code uses Hail reference-block slicing; synthetic/static checks do not validate it on the VDS. |
| Raw report narratives and October fragment | Original external report-data JSON, the static text from original report code, and reviewed October fragment. Code-only template has sequential __TEXT_n__ placeholders in original DOM text order. Values intentionally withheld. Restore inside Workbench or approved review environment, not this repo. |
| Historical fastVEP/reference provenance | Binary version/commit, matching ACMG_SETUP.md/helper scripts, immutable downloads, timestamps and hashes. Exact unknowns listed in MANIFEST. |
| Full carrier extraction / final QC / penetrance | These were not completed in the recorded sessions. No final GQ threshold, FT semantics, age-specific model, Firth implementation or confidence intervals can be exported as completed work. |

## Potential aggregate tables for later disclosure review (contents not included)
- `wgs_ehr_coverage_preflight.csv`: inspect every metric; zeros can be allowed, but check all nonzero counts and implied differences.
- `seer_all_nine_comparisons_2023.csv`: only a reviewed projection with all case, denominator and complement counts above 20; remove fields enabling small-cell reconstruction.
- `seer_all_nine_coverage_sensitivity_2023.csv`: paired counts/differences and overlaps must also pass review.
- `seer_all_nine_cancer_date_sensitivity_2023.csv`: review single-date differences as well as both case totals.
- `seer_cancer_date_sensitivity_summary_2023.csv`: rate/range summaries need denominator and source-cell review.

No table is certified safe in this export: data was not inspected. Inclusive 1–20 is prohibited, so “all cells >=20” is insufficient at exactly 20. The ovarian difference tables and per-variant pilot outputs especially require review and are not proposed for direct sharing.
