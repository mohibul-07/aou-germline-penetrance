# Decision log

Each entry: what we decided, why, and what it would cost to get it wrong. Newest last.

## Cohort and confounding

**Ancestry PCs instead of self-reported race (Jul 2026).**
MUTYH heterozygote ORs were 1.36-1.55 with race dummies and 0.84-1.28 (all null) with 16 genetic
ancestry PCs. In the second-primary analysis -- where cases and comparison group come from the same
cancer-patient population, so there is no ancestry imbalance -- race dummies and PCs agreed (1.14 vs
1.15). The disagreement in case-control analyses was a property of the study design (random controls
differ in ancestry from cases), not of the covariates. The PC-adjusted colorectal OR (1.11) matched
published meta-analyses; the race-adjusted one (1.43) was above all of them.

**BRCA1/2 positive control.** If PCs over-corrected, known strong associations would shrink. They didn't:
BRCA1-breast, BRCA2-breast, BRCA1/2-ovarian, BRCA2-prostate all survived with expected effect sizes.

**Logistic regression, not SMOTE; PSM only as sensitivity.** SMOTE synthesizes data for prediction, not
inference. PSM discarded most breast cases inside the caliper; regression with PCs uses everyone.

**Second-primary contamination.** Secondary-neoplasm concepts name the destination site. 808 of 1,244
dual-flagged patients had metastasis-consistent combinations. Removing them moved MUTYH's OR toward 1.0;
the null held.

## Population denominator (Sep-Nov 2026)

**Full WGS population, not the 77K case-control cohort.** The 77K cohort contains every cancer case but
only 30,000 random controls. It is valid for odds ratios but would inflate prevalence (~20% for breast)
and penetrance. Prevalence and penetrance use the 535,662-participant WGS roster.

**Coverage = >=1 dated condition record (376,944).** The program EHR flag (414,372) includes people with
visits/labs/meds but no diagnoses. Forrest excluded participants without diagnosis data; we match that.
>=2 distinct dates (363,410) is the sensitivity analysis. The ICD-only count (364,261) would match a
phecode/ICD definition; our phenotype uses OMOP standard concepts, so people with non-ICD source
vocabularies still count.

**Participants without diagnosis data are excluded, never used as controls.** They are unknown, not
unaffected. Counting them as unaffected adds hidden cases to the control group and "unaffected"
carriers whose records are simply empty, pulling penetrance and risk difference toward zero.

**Identical eligibility for carriers and non-carriers.** Coverage, age >= 20, and sex restrictions apply
to both groups; this matters more than which threshold is chosen.

## Phenotypes

**OMOP concept definition (Rita's mapping) for SEER and penetrance; phecodes paused.** Phecode
extraction (PheTK, phecodeX) is complete but on hold while the original definition is validated.

**>=1 distinct cancer date as primary, >=2 as sensitivity.** Repeated coding can change specificity and sensitivity; it is not independent confirmation of disease. Do not choose a threshold just to match SEER.

**Concept audit before updating retired concepts.** Replacements can be broader than the original
(prostate-specific -> generic metastatic neoplasm). Count people under original vs replacement first.

**SEER comparison counts living participants.** SEER prevalence = people alive on a reference date with a
cancer history. Deceased participants are excluded from the SEER comparison (not from penetrance, where a
carrier who died of the cancer is exactly who should be counted).

## Variant classification

**Three-arm comparison: ClinVar >=2-star, fastVEP ACMG-AMP, AI-calibrated scores.** Disagreements are the
clinically interesting set: fastVEP-only variants (mostly PVS1-driven loss-of-function) suggest a
curation gap; ClinVar-only variants carry expert evidence ACMG rules can't capture.

**Follow ACMG_SETUP.md exactly; verify by annotation, not by build success.** Missing databases fail
silently. Historical classification changes motivated the check; small result counts are withheld.

**ClinGen Gene-Disease Validity instead of OMIM.** Same role (gates PVS1), public, no license.
genemap2.txt must not be committed.

**SpliceAI and PhyloP from gnomAD v4.1 INFO fields.** No Illumina account or UCSC download needed;
classification uses only the max delta score.

**Per-chromosome runs.** Full-genome references didn't fit a 50 GB node; per-chromosome subsets ran the
1.34M-variant panel in ~16 minutes.

**Filter to the 27 panel genes before counting.** Coordinate-based extraction pulls neighboring genes.

## Penetrance (planned)

**Follow Forrest et al. 2022:** per-variant penetrance, non-carrier prevalence, risk difference, Fisher
exact. Add adjusted Firth/logistic models (age, sex, PCs) for variants with >10 carriers.
**Variants with >5 carriers** (Forrest included singletons; state the difference).
**Sex restriction:** ovarian female, prostate male, breast female (primary).
**Known limitation:** crude penetrance treats young unaffected carriers as unaffected; age thresholds
help, age-specific incidence curves are the full answer.


## Export corrections and recovered decisions (November 8, 2026)

These entries qualify earlier wording, rather than silently rewriting historical decisions.

- **Prevalence reference:** January 1, 2023 for SEER comparisons; diagnosis dates strictly before it, age at that date, exclude recorded primary death on/before it. January 1, 2025 is the separate initial v9-cutoff analysis. No death record is not proof of survival.
- **Matched age bands:** 40–64, 65–74, 75+. Eligibility still starts at age 20; the younger adult band is not comparable to SEER's under-40 band that includes children. Use completed age from birth_datetime, not birth year alone.
- **Coverage and case sensitivity differ:** >=2 ANY diagnosis dates changes coverage/denominator; >=2 dates within the SAME cancer changes the numerator with the primary denominator fixed. The main graph shows coverage sensitivity.
- **SEER type/scope:** complete prevalence; colorectal includes appendix. Kidney-only AoU versus kidney+renal-pelvis SEER remains a mismatch, and melanoma site/behavior remains under review. The ovary-only definition is a sensitivity, not adopted primary. No age standardization or confidence intervals were computed in the historical comparisons.
- **Rounded reference percentages:** values such as <0.1 are upper bounds, with no point ratio. Numeric SEER ratios are approximate. Do not reconstruct populations from rounded percentages.
- **Disclosure:** counts from 1 through 20 inclusive, including complements and values inferable from totals, require suppression/review. A count of 20 is not safe. The reconstructed plotting function suppresses entire paired series when a basic count check fails. (Superseded November 9: the recovered figure masks individual points, as historically; see below.) Cross-table/marginal disclosure still needs Workbench review; no source file is automatically cleared.
- **Survey groups:** relative/EHR positive evidence takes precedence, then additional review, then explicit None, then unknown. Positive evidence can coexist with review signals. Unknown, missing text, and numeric zero are not negative history. Self reports are personal history; root self-or-family is not a relative-only report.
- **Clinical FH provenance:** exclude PPI source vocabulary and reviewed survey record types from clinical evidence. EHR positive codes are signals, not clinician-confirmed histories. Exact pair/concept/review maps remain external and must be restored.
- **Control screen:** target-specific personal Self reports flag provisional control review, not new cases. Other cancer types stay allowed. Skin-unspecified reports are a melanoma sensitivity only; preserve original candidates.
- **Variant membership:** filter source-assigned gene symbols to the approved panel and reconstruct membership from restored headerless ClinVar and fastVEP P/LP lists. Do not force historical unfiltered totals. Unsupported keys remain unresolved. P/LP set membership alone does not establish ClinVar star criteria or absence from all ClinVar positions.
- **Genotype source:** VAT has annotations, not individual calls. The verified VDS bucket has no '-v9' suffix. VDS sample membership was exact and unique across the full roster. The legacy cohort and new-case additions do not define the v9 extraction gap.
- **Alleles:** preserve global ALT indices; convert LGT through LA. Minimal representation is trimming, not reference-based left alignment. Ambiguous matches stay unresolved.
- **Missing calls:** filter intervals before dense conversion and restore filtered/absent entries with unfilter_entries. Missing calls remain missing; defined without the target allele may carry another alternate allele.
- **QC is unresolved:** GQ 20 was a descriptive bin only. FT semantics, depth/balance, ploidy, and final carrier/noncarrier callability thresholds were not adopted. No full-panel extraction has run.
- **Penetrance plan remains proposed:** carrier-count thresholds, Firth/logistic extensions, gene–cancer pairs and future-risk methods are not completed/approved results. The draft computes a cross-sectional disease fraction. A prospective design must handle entry, follow-up, death and prevention procedures; it cannot blindly reuse prevalence eligibility.
- **Phecode branch paused:** keep historical mapping and strict tiers separate from the active Rita OMOP branch. Exact original source-map/version is required; no automatic descendants or replacement expansion.


## Recovered SEER decisions (November 9, 2026)

Source: the executed October 20-22 cells and Md's replies in the Codex session (see MANIFEST).
These entries record what was actually decided and run.
Where they correct the November 8 wording above, the correction is stated.

- **Order of work (October 20 handoff):** coverage preflight, review with Md, OMOP phenotype and SEER comparison, then penetrance.
  The phecode branch stayed paused (October 16).
- **Coverage rule approved by Md (October 21, msg 2436):** primary = at least one dated condition of any diagnosis; sensitivity = at least two distinct condition dates.
  The program EHR flag is audit-only.
- **Rita's mapping frozen unchanged (msgs 2541-2554):** the replacement audit took too long, so Md agreed to freeze the original explicit concepts as the baseline.
  The 12 retired/updated concepts are documented, replacements stay candidates, and the patient-level impact query was never run.
  The prostate replacement target is a site-unspecified metastatic neoplasm and must never be added to prostate.
- **Mapping selection:** workbook group labels are stripped of spaces, melanoma = Skin or Skin/Mucosa rows naming melanoma, and Kidney excludes the separate Renal Pelvis group.
  Eight names were flagged for review (appendix, metastasis-from, melanoma in situ and similar), not removed.
- **Reference dates:** January 1, 2025 (documented v9 cutoff; diagnoses on or before) was the first age/sex run and is kept as a separate baseline.
  SEER complete prevalence is published for January 1, 2023, so the comparison uses that date with diagnoses strictly before it.
- **Demographic status precedence:** missing birth date, then under 20, then recorded primary death on/before the reference.
  Death comes from CDR `aou_death` primary records.
  This corrects the November 8 reconstruction, which read deaths from an uploaded Parquet file and checked death first.
- **Sex:** CDR concept names Female/Male.
  Other categories stay in the audit rows and are excluded only from the comparison.
- **SEER site choices:** colorectal uses "Colon and Rectum (including Appendix)" complete prevalence, which matches Rita's scope.
  "Excluding appendix" exists only as limited duration and was not used.
  Kidney alone exists only as limited duration, so "Kidney and Renal Pelvis" complete was used as a provisional, flagged mismatch.
- **Bounds:** the breast, prostate, colorectal and lung cells would have stopped on a `<` value.
  From melanoma on, `<` values were kept as upper bounds with no point ratio and no difference.
- **Coverage sensitivity result use:** prevalence rose in every stratum, so stricter coverage did not explain the AoU excess, and primary coverage was kept.
- **Cancer-date sensitivity:** the denominator was fixed and all 45 baseline case counts had to reproduce exactly (they did).
  The original cell finished its query but stalled while printing.
  The results were saved from memory without repeating the query.
  No threshold is chosen to match SEER.
- **Ovarian scope:** the original 13 concepts = 8 explicitly ovarian malignant + 3 fallopian-tube cancer + 1 unspecified adnexal + 1 fallopian lesion.
  The non-ovarian breakdown is hierarchical.
  The ovary-only definition is a sensitivity analysis, not adopted.
- **Pancreas:** endocrine pancreatic malignancies were not automatically excluded, and the retired metastasis-from-pancreas concept stays in the baseline.
- **Figure masking (corrects the November 8 entry):** the historical figure masked individual AoU points with cases, denominator or unaffected count in 1-20.
  The November 8 reconstruction's whole-series suppression was a new rule and has been reverted.
  Masking is not dissemination clearance.
- **Reports:** Md asked for a separate HTML for October 21, then asked that the October 22 findings and the Workbench PNG be added to that report, with visuals and simple words.
  Reports stay on the Mac and are never uploaded to All of Us.
