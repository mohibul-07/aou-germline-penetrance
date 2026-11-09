# Comparison with the supplied reconstructions

No remote analysis, reference download, or genotype query was executed during export.

| Supplied file | Difference from session evidence / repair |
|---|---|
| `analysis/00_ehr_coverage_check.py` | Used datetime instead of verified condition_start_date; large array instead of compact newline roster parameter; lacked program duplicate/missing/WGS checks and billing safeguards; printed results. Reconstructed recorded preflight using DATE, compact parameter, complete audit, external files, capped dry-run default. Original SQL is still required for literal recovery. |
| `carriers/40_extract_vat_panel.sh` | Passed BED starts directly into one-based regions, assumed fixed columns, used pipefail-sensitive head, printed counts. Replaced with streaming header-driven helper and explicit BED-convention check; actual historical command sequence unavailable. Gene filtering remains downstream, matching discovered neighboring genes. |
| `carriers/keys.py` | Could duplicate chr prefixes and only stripped one specific path format. Rightmost coordinate/allele parsing plus validation added. Neither version verifies build or left-aligns indels. |
| `analysis/penetrance/penetrance.py` | Unrun draft had case-sensitive cancer restriction and inferred noncarriers from missing carrier-list membership. CLI now requires explicit callability and opt-in; labels normalized, metadata/cohort checks added, empty noncarrier groups handled. Pure-function complete-call assumption retained only for existing synthetic tests. Firth and future-risk estimation remain unimplemented. |
| `acmg_fastvep/10_build_sa_clinvar.sh` | Floating latest ClinVar URLs cannot reproduce historical release; now require configured URLs. Early grep termination could trigger pipefail. No claim the reconstructed CLI matches the unknown historical commit. |
| `acmg_fastvep/11_build_sa_gene_level.sh` | GDV download was floating; source URL now explicit and historical date unknown. Observed small-result comment removed. GDV helper and json-key behavior still need original version verification. |
| `acmg_fastvep/12_build_sa_gnomad_region.sh` | Now checks BED convention and uses tabix header mode; sorts/deduplicates overlapping regional records. gnomAD source configured externally. |
| `acmg_fastvep/13_build_sa_spliceai_phylop.sh` | Helper existence checked; exact helper revision and whether it reuses local slices must be recovered. Score copying assumptions remain user-reported, unverified. |
| `acmg_fastvep/14_build_sa_revel.sh` | URL configured; historical source digest absent; per-chromosome workflow retained as user reconstruction. |
| `acmg_fastvep/15_build_sa_repeatmasker.sh` | URL configured; source snapshot unknown; source-key semantics still require pinned fastVEP verification. |
| `acmg_fastvep/20_verify_stack.sh` | Embedded probe removed; original pipeline swallowed annotation failure and mixed stderr with JSON. Uses external probe, separate JSON file and fails if required criteria are not evaluated. Does not prove all nine sources work; restore original full-stack checker. |
| `acmg_fastvep/30_run_acmg_per_chr.sh` | Scratch paths moved into config; command output redirected internally. Tab-output claim corrected by retaining VCF default. Historical flags and chromosome SA discovery remain unverified. |
| `phenotypes/omop_cancer_cases.py` | Original reconstruction pulled unrestricted CDR people and used wrong date field. Preserve workbook loader; disable that extraction CLI and direct users to roster/date-bounded aggregate workflow. |
| `analysis/seer/README.md` (Nov 8) | Incorrectly claimed standardized rates and full site matching. Corrected: raw matched-age prevalence, kidney mismatch, melanoma review, complete prevalence 2023 reference. |
| `analysis/00_ehr_coverage_check.py` (Nov 9) | Replaced with the recovered SQL; see the SEER section below. |

All fastVEP reconstruction scripts require explicit review opt-in. This is not a substitute for pinning the original binary/reference snapshots. Older unrelated analysis scripts retain their historical/draft status and are not authenticated by this export.

## Other code-only cleanup

Legacy analysis source contained hard-coded result narratives and printed controlled results. These were removed; legacy frequency, PC and secondary-outcome helpers now save internal artifacts instead of printing results. These are preservation/cleanup changes, not evidence that the old models were rerun or validated. The reconstructed metastasis sensitivity continues to need the original notebook for exact cohort-filter semantics. The older association and carrier helper CLIs remain caller-configured drafts.


## SEER branch: November 8 reconstruction versus recovered original (November 9, 2026)

The executed cells were found in the Codex transcript (MANIFEST).
Every SEER reconstruction was compared with them.
The recovered code replaces each reconstruction, and the historical methods are restored.
All differences found are listed below.

| File | November 8 reconstruction | Recovered original (now in the file) |
|---|---|---|
| `analysis/00_ehr_coverage_check.py` | Rewritten SQL. `program_wgs_flag_total` counted raw `cb_search_person` rows, while the original counts per-person flags after `GROUP BY person_id`, so the totals differ if program rows are duplicated. Other columns were logic-equivalent. No schema check. | Literal SQL (`sql.coverage_preflight`), schema-check step, original identities, 5 GiB cap. |
| `analysis/seer/00_rita_mapping.py` (new) | Mapping assumed to be a ready-made CSV of cancer,concept_id. | Recovered workbook freeze: label strip, melanoma rule, integer checks, review flags, cross-cancer check, original CSV columns. |
| `phenotypes/concept_audit.py` | One combined query that joined relationships only for invalid concepts, with different output columns. | The two executed queries (vocabulary, replacements) with original columns and caps, plus the never-executed impact query, refused unless explicitly enabled. |
| `analysis/seer/01_prevalence_counts.py` | One new combined query. Deaths came from an uploaded Parquet file instead of CDR `aou_death`. Sex came from hard-coded concept IDs instead of concept names. Death was checked before age. It added a `>=2 cancer dates` column, which the original 2023 query never had. It had no birth-year baseline and no 2025 run. Long table schema. | Literal baseline, 2025 and 2023 queries. The 2023 query is derived from the 2025 one by the original asserted replacements. Wide output schema (`<cancer>`, `<cancer>_ge2_dates`, coverage denominators). |
| `analysis/seer/reference.py` | Sex check by substring over the first rows, so a Female export passed a `Male` check. Required "completeness" anywhere, allowed bounds for every site, and needed an external index CSV. | Union of the per-site cell checks: first-cell title, date in the first cell, `Age at Prevalence` with a word-boundary sex match, completeness-index footnote, exact band labels, duplicate check. Per-site historical bound handling. The public site/file table is built in, so no index file is needed. |
| `analysis/seer/02_compare.py` | New long schema with coverage labels `primary`/`coverage_ge2` and different column names. | Per-site template plus consolidation: `ge1_dated_condition`/`ge2_condition_dates`, `aou_cases`, `aou_denominator`, `seer_percent_as_published`, `site_scope_status`, `source_file`. Byte-identical to the historical consolidated table on synthetic inputs. |
| `analysis/seer/03_cancer_date_sensitivity.py` | Derived the >=2-cancer-date counts from the reconstructed combined query, and had no summary. | The executed separate query (age >= 40, sex rules in SQL), exact baseline reproduction, fixed denominator, the recovery-path `compare`, and the msg 3245 summary. |
| `analysis/seer/04_ovarian_scope.py` | Reran the whole prevalence query with an "ovary-specific" mapping. | The executed ovarian query: evidence on original concepts, ovary-only dates, hierarchical fallopian/adnexal/lesion breakdown. The concept classes come from a validated external file. |
| `analysis/seer/05_coverage_sensitivity.py` | Outer-merge on reconstructed columns. | The msg 3149 pairing and checks; original output columns. |
| `analysis/seer/06_plot.py` | Suppressed whole sex series when any point failed the small-cell check, used different titles, legend, footnote, dpi and constrained layout, and plotted SEER bounds with pandas indexing. | The literal msg 3161 figure, with point-level masking. Pixel-identical to the original cell on synthetic inputs. |
| `analysis/seer/07_ovarian_scope_comparison.py` | Compared reconstructed parquet columns; missing the hierarchy and the >=2-date reproduction checks. | The msg 3317 comparison and every check. |
| `reports/build_seer_report.py`, `reports/seer_template.py` (new) | Not exported. | Recovered Mac builder, with result values moved to external slots. Byte-identical output with the historical inputs. |
| `workflow/runtime.py` | Global billing cap only. | Optional per-step historical cap (never above `MAXIMUM_BYTES_BILLED`). `run_query` now returns whether it executed and records the bytes actually processed and billed, and `update_json`/`read_json` helpers were added. Existing callers are unaffected. |
| `tests/test_export.py` | The SEER fixture wrote the sex line unquoted, so it split into two CSV cells, unlike real exports. The query test asserted reconstruction-only SQL. | Fixture quoted as in the real export; query test asserts the recovered SQL. New `tests/test_seer_recovered.py`. |

New repairs that are not historical behavior, all listed in docstrings: config paths; no printing; literal expected totals replaced by checks against saved inputs or by metadata; a non-interactive plot backend; GCS copying left to `setup/99_backup.sh`; the ovarian concept IDs moved from code literals to an external file.
`phenotypes/omop_cancer_cases.py` was left as is: it yields the same concept sets for the restored workbook, but the recovered `00_rita_mapping` is the module to use.
