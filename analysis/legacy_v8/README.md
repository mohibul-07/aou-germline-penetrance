# Legacy analyses (v8 case-control cohort, 77K)

These used the case-enriched cohort (all cancer cases + 30,000 random controls). That design is valid
for odds ratios but NOT for prevalence or penetrance, which require the full population denominator.

| Script | Question | Outcome |
|---|---|---|
| `mutyh_second_primary_contamination.py` | Do metastases coded at the destination site leak into "second primary"? | 808 of 1,244 dual-flagged patients had metastatic-route combinations; MUTYH null held under all handling strategies |
| `secondary_cancer_full_cohort.py` | Dr. Huang's model: y = secondary cancer, tested on everyone | Null for mets (narrow, conservative) and second primary |
| `cohort_expansion_v9.py` | Add new v9 cancer cases with the same OMOP definitions | 64,750 -> 76,877 participants |

MUTYH heterozygote summary (all PC-adjusted, all null): case-control across 9 cancers, PSM 1:3,
metastatic disease, second primary, contamination-adjusted second primary, full-cohort model.
BRCA1/2 positive control confirmed PCs preserve real signal.
