# Population-based variant penetrance (NEXT)

Procedure: Forrest IS et al. *Population-Based Penetrance of Deleterious Clinical Variants.*
JAMA 2022;327(4):350-359.

| Step | Forrest | This project |
|---|---|---|
| Population | unselected biobank, age >= 20, has ICD data | WGS with >=1 dated condition, age >= 20 |
| Variants | ClinVar P/LP + novel LoF; no novel missense; no recessive-only genes | ClinVar P/LP (all; >=2-star sensitivity) and fastVEP ACMG P/LP, 27-gene panel |
| Phenotype | ICD-10 present = case; all matching codes absent = control | OMOP definition under review after descriptive SEER comparisons |
| Penetrance | carriers with disease / all carriers | same |
| Risk difference | penetrance - non-carrier prevalence; Fisher exact | same, plus adjusted Firth/logistic (age, sex, PC1-16) for >10 carriers |
| Strata | review status, consequence, ancestry, age >= 20...70 | same + **concordance group** (concordant / ClinVar-only / fastVEP-only) |

Decisions:
- Variants with >5 carriers (Forrest included singletons -- state the difference).
- Comparison group: ALL eligible non-carriers (with and without cancer), same coverage/age/sex rules.
- Sex restriction for both groups: ovarian = female, prostate = male, breast = female primary.
- Penetrance is crude (proportion at current age): a 45-year-old carrier without cancer counts as
  unaffected. Age thresholds partly address this; age-specific incidence curves are the full fix.
- Key added value: does fastVEP-only penetrance approach ClinVar P/LP (under-curated pathogenic
  variants) or sit near baseline (over-calling)?
- Direct comparison: Forrest reports BRCA2 c.32340301del (47%) and c.32340630_32340631del (100%);
  these appear to correspond to our 13-32340300-GT-G and 13-32340629-CTT-C (confirm normalization).

This remains an unrun proposal. Minimum carrier counts are draft parameters, not final approvals. CLI requires explicit per-variant callability; synthetic tests may assume complete calls. No future-risk, Firth or confidence-interval implementation is provided. No claim of validated phenotypes or calibrated clinical risk.
