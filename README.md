# aou-germline-penetrance

Germline cancer-predisposition variant classification, carrier identification, phenotype validation,
and population-based penetrance in the **NIH All of Us Research Program** (v9, whole-genome sequencing).

Huang Lab, Icahn School of Medicine at Mount Sinai.

**Flow**

```
VAT (27 genes, tabix) ─► sites VCF ─► fastVEP ACMG-AMP (per chromosome) ─┐
VAT ClinVar P/LP (review criteria to verify) ───────────────────────────────────────────────┼─► three-way comparison
VAT SpliceAI / REVEL / AlphaMissense (AI arm, planned) ─────────────────┘   (concordant / ClinVar-only / fastVEP-only)
                                                                              │
VDS genotypes (535,662 WGS) ─► carriers ──────────────────────────────────────┤
OMOP condition_occurrence ─► cancer phenotypes ─► SEER validation ─────────────┴─► penetrance (Forrest 2022)
```

## Design constraints

- **Code only.** No participant data, no controlled-tier derivatives, no counts between 1 and 20,
  no licensed references. The hook helps screen files but cannot certify disclosure safety. See `docs/DATA_POLICY.md`.
- **Population denominator.** Prevalence and penetrance use the full WGS roster with EHR diagnosis
  coverage, never the case-enriched case-control cohort.
- **Verify, don't trust.** fastVEP fails silently when a supplementary database is missing;
  `acmg_fastvep/20_verify_stack.sh` checks that criteria actually evaluate.
- **Every decision is logged** with its reasoning in `docs/DECISIONS.md`.

## Layout

| Path | Contents |
|---|---|
| `config/` | environment paths, external input adapters, panel genes/target regions |
| `workflow/` | output-location checks, capped dry-run query runner |
| `phenotypes/phecode/` | historical paused branch: dated mapping, malignant tiers, distinct-date flags |
| `phenotypes/` | survey/EHR evidence query reconstructions, four FH groups, control screening, concept audit |
| `carriers/` | header-driven VAT extraction, format-only keys, source-list reconciliation, legacy helpers |
| `carriers/vds/` | roster audit and reconstructed variant/sparse/dense QC pilot |
| `analysis/seer/` | recovered original SEER code: mapping freeze, prevalence, nine comparisons, two separate sensitivities, ovarian scope, figure |
| `analysis/penetrance/` | explicitly unrun draft, requiring callability and opt-in |
| `acmg_fastvep/`, `setup/` | user-reconstructed setup/annotation; historical versions still need recovery |
| `reports/` | recovered interactive report builders (pan-cancer, SEER); all results and narrative external |
| `tests/` | synthetic tests only |
| `docs/` | manifest, decisions, reconstruction differences, missing inputs, export review |
| `hooks/` | data guard; code-only review still required |

## Status

| Component | Historical analysis / export status |
|---|---|
| fastVEP stack and panel | Reported built/annotated historically; reconstructed scripts reviewed, commit/release evidence incomplete |
| PheTK/phecodeX | Historical branch paused; query/tier/threshold code reconstructed; exact maps/versions pending |
| Family history / personal surveys | Query helper recovered; grouping/screens reconstructed; exact clinical-review maps pending |
| Variant reconciliation | Source-membership reconstruction exported; external source lists required |
| VDS | Pilot historically validated; scripts reconstructed, not executed here; full extraction and final QC pending |
| SEER | Descriptive comparisons and sensitivities completed historically; original code recovered (SQL identical to executed cells); phenotype review remains open |
| SEER standardization / confidence intervals | Not performed; no result or completed implementation claimed |
| Penetrance / prospective risk | Proposed only; draft safeguards corrected; no completed model |
| Reports | Original pan-cancer and SEER builders recovered with result text removed; external payloads required |
| AI-score arm | Planned |

## Quick start (Workbench)

```bash
git clone <this repo> && cd aou-germline-penetrance
ln -s ../../hooks/pre-commit .git/hooks/pre-commit
source config/params.env
setup/00_restore_workspace.sh
# Restore approved reference snapshots and verify unknown manifest fields first.
# fastVEP reconstruction is gated pending version/helper review.
```

Building the ACMG stack from scratch: `acmg_fastvep/10_*` through `15_*`, then `20_verify_stack.sh`.

## References

- Huang KL et al. Pathogenic germline variants in 10,389 adult cancers. *Cell* 2018.
- Forrest IS et al. Population-based penetrance of deleterious clinical variants. *JAMA* 2022.
- Richards S et al. ACMG-AMP standards for sequence variant interpretation. *Genet Med* 2015.
- All of Us Research Program Genomics Investigators. Genomic data in the All of Us Research Program. *Nature* 2024.
- fastVEP: https://github.com/Huang-lab/fastVEP
- Related: https://github.com/Huang-lab/germline-plp-carrier-nf (Mount Sinai cohorts)
- All of Us Research Primer: https://huang-lab.github.io/AOU_research_primer/

## Code export, not analysis execution

The November 8 export did not read participant datasets, rerun queries, extract genotypes or publish anything. New Python steps run as modules after sourcing config; see `docs/INPUTS.md`. No saved outputs or result tables are bundled. Recover original source cells and maps inside Workbench for exact reproduction; reconstructions are labeled explicitly.

Read `docs/MANIFEST.md`, `docs/RECONSTRUCTION_DIFFS.md`, `docs/RECOVERY_GAPS.md`, and `docs/EXPORT_REVIEW.md` before use. Unknown version dates are not replaced by current releases. `RUN_QUERIES=0` is the default; explicit execution remains capped. Genotype QC thresholds remain unresolved. This folder was not initialized as a Git repository during export.

### SEER code recovery (November 9, 2026)

The original SEER cells were found in the Codex session that ran the October 20-22 work.
That work was done in Codex, not Claude Code.
They replace the November 8 SEER reconstructions; see `analysis/seer/README.md` and `docs/RECONSTRUCTION_DIFFS.md`.
Nothing was rerun, queried or downloaded.
Equivalence was shown on synthetic inputs only.

## License

The code and documentation are released under the MIT License; see [`LICENSE`](LICENSE).
The license covers this repository only.
It grants no rights to All of Us data, which stays under the All of Us Data User Code of Conduct, or to third-party references such as OMIM, Rita Lu's OMOP concept mapping, or downloaded annotation databases.
