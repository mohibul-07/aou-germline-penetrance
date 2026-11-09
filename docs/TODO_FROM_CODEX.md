# Code export checklist — November 8, 2026

Completed means code exported/reviewed, not an analysis rerun or exact notebook recovery.

- [x] Read repository README, decisions, data policy and original TODO first.
- [x] Reconstruct dated PheTK mapping, malignant tiers and distinct-date flags in `phenotypes/phecode/`.
- [x] Recover/adapt exact survey-pair query; reconstruct four-group precedence and personal-control screen.
- [ ] Recover original EHR FH raw extraction, full review-map and fine-grained phecode evidence labels. See RECOVERY_GAPS.
- [x] Reconstruct vocabulary/replacement audit without changing concepts. Superseded Nov 9 by the recovered executed queries.
- [x] Correct the coverage preflight reconstruction against session decisions. Superseded Nov 9 by the recovered SQL.
- [x] Export source-supported variant reconciliation, with unresolved keys separate.
- [x] Reconstruct VDS roster/access/sparse/dense pilot; keep final QC unresolved.
- [x] Reconstruct SEER counts, comparison, coverage/cancer-date/ovarian sensitivities and figure. Superseded Nov 9 by recovered originals.
- [x] Recover byte-identical historical SQL/plot cells (SEER branch, Nov 9; the Codex transcript, see MANIFEST). No standardization was run.
- [x] Recover report chart/layout code with narrative/results externalized.
- [x] Review VAT, key, penetrance and fastVEP reconstructions; document repairs and remaining uncertainty.
- [x] Add MANIFEST with confirmed/reported/unknown versions; do not invent exact releases.
- [ ] Recover unknown ClinVar/ClinGen dates, fastVEP commit and exact PheTK/phecodeX versions.
- [x] Update README, decisions, data policy and input contracts.
- [x] Final synthetic tests, syntax and code-only inspection (results in EXPORT_REVIEW).

## SEER recovery follow-up, November 9, 2026

- [x] Recover coverage preflight, Rita mapping freeze, vocabulary/replacement audits, baseline/2025/2023 prevalence, SEER parsing, nine comparisons, both sensitivities, ovarian scope, figure and SEER report builder.
- [x] Show equivalence with the original cells on synthetic inputs (tables byte-identical, figure pixel-identical, report byte-identical with historical inputs).
- [ ] Restore `OVARY_SCOPE_MAPPING` in Workbench from the historical ovarian-scope metadata.
- [ ] Hash the nine SEER exports in Workbench and record the SEER data release if identifiable.
- [ ] Review the October 2-15 cells in the same Codex transcript for the phecode, family-history and VDS reconstructions.
- [ ] Get Rita's permission before publishing anything derived from her mapping.
