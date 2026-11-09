# Provenance manifest — code export, November 8, 2026

No analyses were rerun. “Confirmed” means supplied execution output or saved session code/record, not a fresh verification of data. Unknown versions are deliberately not filled with current releases.

| Item | Version/date actually supported | Evidence and missing provenance |
|---|---|---|
| CDR | `wb-silky-artichoke-2408.C2025Q4R6`, v9 Controlled Tier | Confirmed session configuration; initial analysis reference date January 1, 2025 (not a verified official clinical cutoff). Dataset created June 26, 2026 is not a clinical cutoff. |
| Genome build | GRCh38 | Confirmed VDS metadata; no lift-over performed. |
| VDS | `gs://vwb-aou-datasets-controlled/v9/wgs/short_read/snpindel/vds/hail.vds/` | Confirmed discovery/pilot October 7, 2026. Object generation/hash not recovered. |
| Hail | `0.2.135-034ef3e08116` | Confirmed runtime banner October 7, 2026. |
| Spark | `3.5.3` | Confirmed runtime banner. |
| Python (Workbench) | 3.11 family | Traceback path; exact patch unknown. |
| ClinVar | Exact release UNKNOWN | Existing headerless P/LP list was reused. Restore VCF fileDate/header, variant_summary snapshot, hashes and download log. Filenames/latest URLs cannot establish a release. |
| gnomAD | v4.1 reported | Brief/reconstruction describes exome-region SA and constraint sources; file generations, snapshot hashes and precise build dates unknown. |
| REVEL | v1.3 reported | Reconstruction points to v1.3 ZIP; original checksum/download date unknown. |
| Ensembl | release 115 reported, GRCh38 | Reference filenames and skeleton setup; executed reference hashes/download dates unknown. |
| ClinGen GDV | Download date UNKNOWN | GDV replaced the gene-disease source under historical `omim` key; restore source snapshot and download/build log. |
| fastVEP | Version and commit UNKNOWN | Original binary --version, source git commit, ACMG_SETUP.md and helper versions needed. Reconstructed commands cannot authenticate the historical stack. |
| PheTK | Exact installed version UNKNOWN | Historical extraction used PheTK mappings, per October records. Restore package metadata/environment lock. |
| phecodeX | X1_0 label recorded in artifact directory; package/map release UNKNOWN | Directory label is not version proof. Restore exact mapping file and checksum. |
| SEER | SEER*Explorer complete prevalence ("People Alive with Cancer (U.S. Prevalence) on January 1, 2023"), by age at prevalence and sex, percent of the U.S. cohort population to one decimal | Export footers (printed for breast and colorectal, msgs 2720/2902): 2023 prevalence proportions from the SEER 12 Areas; U.S. population = average of 2022 and 2023 Census estimates; first invasive tumor diagnosed 1992-2022 (31 years); older cases by the completeness-index method; "Created by https://seer.cancer.gov/statistics-network/explorer/ on Wed Oct 21 2026". Breast, prostate and colorectal were downloaded October 21; lung, melanoma, kidney+renal pelvis, ovary, pancreas and stomach on October 22 (session timeline). The SEER data submission/release name is not in the exports: UNKNOWN. File hashes were not recorded; originals and GCS copies are in `00_reference/seer/`. Exact site titles and file names are in `analysis/seer/reference.py`. Colorectal "including Appendix" is complete; "excluding Appendix" and kidney-alone exist only as limited duration and were not used. |
| Rita mapping | Restored `01_cohort/Final_Cancer_Groups_OMOP_AoU.xlsx`, single sheet `Sheet2` | Recovered selection code (msg 2451); original explicit concepts, no replacement/descendant expansion. Workbook version/hash UNKNOWN; the frozen mapping CSV and its metadata are in Workbench `01_cohort/seer_validation_v9/`. Excluded from the repo pending Rita's permission. |
| CDR vocabulary | Same CDR; `concept`, `concept_relationship` | Vocabulary audit job 29c127ba-7add-4722-a1eb-d4991dbdccb1, replacement audit job 7e01f254-79eb-4c56-8a96-e3b53b7828f4 (October 21, 2026). OMOP vocabulary release inside the CDR not recorded: UNKNOWN. |
| Death data | CDR `aou_death`, `primary_death_record = TRUE` | Used by all 2023/2025 prevalence, cancer-date and ovarian queries. The Parquet `wgs_primary_death_records.parquet` was only schema-inspected for SEER work. |

## SEER code source and executed jobs (recovered November 9, 2026)

Source: Codex session `~/.codex/sessions/2026/10/02/rollout-2026-10-02T09-55-08-01a0fce5-b7e8-74c0-a96d-57d38491619c.jsonl` on Md's Mac, October 20-22, 2026 messages (not a Claude Code session).
Job IDs come from Md's pasted outputs; the dry-run estimates come from the same outputs.

| Step | Job ID | Cap | Dry-run estimate |
|---|---|---|---|
| Coverage preflight | 6d2f1f73-8090-4820-9689-fa7ad7edc1eb | 5 GiB | 3.98 GiB |
| Vocabulary audit | 29c127ba-7add-4722-a1eb-d4991dbdccb1 | 2 GiB | 0.956 GiB |
| Replacement audit | 7e01f254-79eb-4c56-8a96-e3b53b7828f4 | 4 GiB | 2.714 GiB |
| Replacement impact | never executed (dry run only) | - | not recorded |
| Birth-year baseline | 46c494d2-bb61-4583-8b39-04ab5096fc5b | 6 GiB | 4.41 GiB |
| 2025 v9-cutoff prevalence | b51b114b-9c6c-43d6-94c1-650ab3c6f305 | 6 GiB | 4.41 GiB |
| 2023 SEER-aligned prevalence | 7645e039-e2c5-4190-baf5-51c37f82283d | 6 GiB | 4.41 GiB |
| Cancer-date sensitivity | 4ee8fb8a-5f8e-4ccd-aceb-de3a4da5a1e2 | 6 GiB | 4.41 GiB |
| Ovarian scope audit | 6b7200ee-b1b9-4b97-8d01-817df0d4e6fd | 6 GiB | 4.41 GiB |

Figure: the canonical PNG is Md's Workbench download, kept locally as `~/Agents/research_report/assets/seer_all_nine_prevalence_comparison_2023.png`, SHA-256 `1a46aea5241a041ee666944eeae5703a6ebacf074c6c6e9bacfd44b8453b54c8` (from `seer_graph_provenance.json`).
Report: `~/Agents/research_report/build_seer_report_2026-10-21.py` and its October 22 backup `~/Agents/backups/seer_visual_report_2026-10-22_105442.zip`.
Notebook-side package versions for these cells (google-cloud-bigquery, matplotlib, openpyxl, pyarrow) were not recorded: UNKNOWN.

## Recovered membership summary
Target-panel source support was 2,182 unique variant keys: 694 concordant, 140 ClinVar-only, 1,348 fastVEP-only. These are variant-set provenance totals, not participant counts. Unsupported keys and per-variant carrier counts are not bundled. Exact manifests remain in Workbench.

## Evidence tiers for this export
- **Recovered code:** report layout/chart builder; survey preparation query (adapted for paths, outputs and execution control); the full SEER branch (coverage preflight, Rita mapping freeze, vocabulary/replacement audits, baseline/2025/2023 prevalence, nine comparisons, both sensitivities, ovarian scope, figure, SEER report builder), recovered November 9, 2026 from the Codex transcript.
- **Reconstructed from recorded decisions:** date/tier flags, FH grouping, personal-survey screen, reconciliation, VDS pilot.
- **User reconstructions reviewed but historical execution unverified:** fastVEP builders, VAT extraction, draft penetrance and older analyses. See RECONSTRUCTION_DIFFS.md.

A runtime version-capture script can document a future environment; it cannot fill historical gaps. Do not claim byte-identical reproduction until original notebook cells, SQL artifacts, reference snapshots and package metadata are restored inside Workbench.
