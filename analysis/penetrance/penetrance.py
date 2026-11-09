"""Per-variant penetrance, risk difference, and Fisher exact test (Forrest et al. 2022).

DRAFT -- not yet run. Inputs/outputs are configured PEN_* paths in params.env.
Decisions: identical eligibility, lowercase cancer labels, unique metadata, explicit
per-variant callability required by CLI; no unknown genotypes become noncarriers.
Function callable_pairs=None is retained for synthetic complete-genotype tests only.
This estimates observed disease fraction, not future risk; no Firth, confidence
interval, age-specific incidence, or external validation is implemented.

carriers.csv   : person_id, vid, gene, zygosity
cohort.csv     : person_id, sex_at_birth, age, eligible (bool; coverage + age rules applied)
cases.csv      : person_id, cancer            (OMOP phenotype, one row per person x cancer)
variants.tsv   : vid, gene, concordance_group, clinvar_stars, consequence
gene_cancer.tsv: gene, cancer                 (primary pairs, approved by Dr. Huang)
"""
import os
from workflow.runtime import external, env

import pandas as pd
from scipy.stats import fisher_exact

SEX_RESTRICT = {"ovarian": "Female", "prostate": "Male", "breast": "Female"}


def penetrance_table(carriers, cohort, cases, variants, gene_cancer, min_carriers=6, callable_pairs=None):
    if cohort.person_id.duplicated().any():
        raise ValueError("Cohort must be unique")
    if not pd.api.types.is_bool_dtype(cohort.eligible) or cohort.eligible.isna().any():
        raise ValueError("Eligibility must be non-null boolean")
    if variants.duplicated(["vid", "gene"]).any():
        raise ValueError("Variant metadata must be unique")
    cohort = cohort[cohort["eligible"]]
    cases = cases.copy(); cases["cancer"] = cases.cancer.str.lower()
    gene_cancer = gene_cancer.copy(); gene_cancer["cancer"] = gene_cancer.cancer.str.lower()
    gene_cancer = gene_cancer.drop_duplicates(["gene", "cancer"])
    case_sets = cases.groupby("cancer")["person_id"].apply(set).to_dict()
    rows = []
    for vid, g in carriers.groupby("vid"):
        gene = g["gene"].iloc[0]
        for cancer in gene_cancer.loc[gene_cancer["gene"] == gene, "cancer"]:
            pop = cohort
            if cancer in SEX_RESTRICT:
                pop = pop[pop["sex_at_birth"] == SEX_RESTRICT[cancer]]
            ids = set(pop["person_id"])
            if callable_pairs is not None:
                known = set(callable_pairs.loc[callable_pairs.vid == vid, "person_id"])
                if not (set(g.person_id) & ids) <= known:
                    raise ValueError("Carrier call not in callable population")
                ids &= known
            car = set(g["person_id"]) & ids
            if len(car) < min_carriers:
                continue
            non = ids - car
            cs = case_sets.get(cancer, set())
            a, b = len(car & cs), len(car - cs)          # carriers affected / unaffected
            c, d = len(non & cs), len(non - cs)          # non-carriers affected / unaffected
            if not non:
                continue
            pen, prev = a / (a + b), c / (c + d)
            _, p = fisher_exact([[a, b], [c, d]], alternative="two-sided")
            rows.append(dict(vid=vid, gene=gene, cancer=cancer, n_carriers=a + b, carriers_affected=a,
                             penetrance=pen, noncarrier_n=c + d, noncarrier_affected=c,
                             noncarrier_prev=prev, risk_difference=pen - prev, fisher_p=p))
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.merge(variants, on=["vid", "gene"], how="left")


def main():
    if os.environ.get("ALLOW_DRAFT_PENETRANCE") != "1":
        raise ValueError("Unrun draft: analysis plan and genotype QC must be agreed first")
    # Runtime requires explicit per-variant callability, unlike legacy carrier-list subtraction.
    res = penetrance_table(pd.read_csv(external("PEN_CARRIERS")),
        pd.read_csv(external("PEN_COHORT")), pd.read_csv(external("PEN_CASES")),
        pd.read_csv(external("PEN_VARIANTS"), sep="\t"),
        pd.read_csv(external("GENE_CANCER_MAPPING"), sep="\t"),
        int(env("PEN_MIN_CARRIERS")), pd.read_csv(external("PEN_CALLABILITY")))
    res.to_csv(external("PEN_OUTPUT", True), index=False)


if __name__ == "__main__":
    main()
