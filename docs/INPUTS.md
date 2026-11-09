# Input contracts and safe execution

Source `config/params.env` from Bash. Run steps as `python -m package.module` (numeric module names work with `-m`). No script was run on data during export. Dependencies are listed separately; Hail belongs in Workbench.

The external filenames are adapters, not claims about original schemas. Confirm/rename columns inside Workbench using original source cells. Do not download data to satisfy these contracts. Every exported Python analysis output goes through workflow.runtime.external and is rejected if placed inside this code folder. Legacy unrelated scripts are not covered by that guard; they must never write into the repo.

| Configuration | Required schema |
|---|---|
| WGS_ROSTER | Parquet with unique non-null person_id |
| RITA_WORKBOOK | Rita Lu's Final_Cancer_Groups_OMOP_AoU.xlsx, sheet Sheet2 (Group, Name of Condition, OMOP Concept ID, Source Code); private, never copied here |
| CANCER_MAPPING | CSV written by analysis.seer.00_rita_mapping (cancer, concept_id plus workbook columns); SEER steps use its unique cancer/concept pairs |
| OVARY_SCOPE_MAPPING | CSV concept_id,scope_class (ovary, fallopian_cancer, adnexal, lesion); must partition the original ovarian concepts; restore from the historical ovarian-scope metadata |
| SEER_REFERENCE_DIR | Public SEER*Explorer complete-prevalence exports with the historical file names listed in analysis/seer/reference.py |
| COVERAGE_OUTPUT | One-row preflight Parquet; later steps cross-check coverage totals against it |
| REPORT_SEER_REVIEW_DATA / REPORT_SEER_TEXT / REPORT_SEER_FIGURE | Reviewed aggregate payloads for the SEER report; schemas in reports/build_seer_report.py |
| PHECODE_MAPPING | CSV vocabulary_id,code,phecode,cancer; exact installed map subset, cancer labels lowercase |
| SURVEY_PAIR_MAPPING | CSV question_concept_id,answer_concept_id,evidence_class,relative; exact approved pairs |
| CLINICAL_FH_MAPPING | CSV concept_id,evidence_class; reviewed positive/negative/uncertain labels |
| FH_SIGNALS | Full-roster Parquet person_id,relative_history,clinical_positive,reported_none,additional_review; all flags non-null booleans |
| CANDIDATE_CONTROLS | Parquet person_id,cancer,candidate_control,eligible_case; original eligibility and lowercase cancers |
| PERSONAL_SURVEY | Parquet person_id,site; only reviewed positive Self reports; melanoma source site skin_unspecified |
| COMPARISON_TSV | TSV key,gene,group; may contain source file prefixes |
| CLINVAR_KEYS / FASTVEP_KEYS | Headerless TSV, variant key in first column |
| HAIL_SAMPLE_ROSTER_GCS | GCS TSV header s; sample IDs as strings, uploaded in Workbench |
| PILOT_TARGETS | TSV target_key,gene,group; restore historical reviewed targets, no keys bundled |
| REPORT_DATA / REPORT_TEXT / REPORT_OCT7_FRAGMENT | Original reviewed external report payloads; see reports/README.md |
| PEN_CALLABILITY | CSV vid,person_id, only calls passing the agreed per-variant policy; that policy is still pending |

Examples of module commands (do not execute as part of code export):

```bash
source config/params.env
python -m analysis.00_ehr_coverage_check   # dry run only by default; metadata written outside repo
python -m carriers.reconcile_variants    # reads external controlled derivative lists
python -m analysis.seer.02_compare       # reuses existing aggregate counts
# Full recovered SEER order: analysis/seer/README.md
```

RUN_QUERIES defaults to zero. An explicit one permits the query only if the new dry-run estimate fits MAXIMUM_BYTES_BILLED. Query results stream to Parquet and are never printed. Hail scripts are separate manual steps and do not start merely by sourcing config. External output files are internal research artifacts, not pre-approved exports.
