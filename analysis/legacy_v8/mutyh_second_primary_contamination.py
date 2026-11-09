"""Second-primary contamination check.

OMOP secondary-neoplasm concepts name the DESTINATION site ("secondary malignant neoplasm of lung" =
metastasis found in lung). A breast patient with lung metastasis may also carry a plain lung cancer
code and be miscounted as a second primary. We flag participants with both second_primary and
mets_conservative whose cancer combination matches a plausible metastatic route, then re-fit:
  1. original (all second primaries)
  2. clean only (second primary without any mets flag)
  3. excluding plausible-route cases
Model: second_primary ~ MUTYH_het + age + sex_male + PC1..16, cancer patients with PCs.
"""
from workflow.runtime import external
import json
import numpy as np
import pandas as pd
import statsmodels.api as sm

PCS = [f"pc{i}" for i in range(1, 17)]

# primary -> plausible metastatic destinations among our 9 sites
MET_ROUTES = {
    "Breast": ["Lung", "Kidney", "Ovarian", "Stomach"],
    "Prostate": ["Lung", "Kidney"],
    "Colorectal": ["Lung", "Stomach"],
    "Melanoma": ["Lung", "Stomach"],
    "Lung": ["Kidney", "Stomach", "Breast"],
    "Kidney": ["Lung", "Pancreatic"],
    "Ovarian": ["Lung", "Stomach", "Colorectal"],
    "Pancreatic": ["Lung", "Stomach", "Colorectal"],
    "Stomach": ["Lung", "Colorectal", "Ovarian"],
}


def plausible_met(cancers: str) -> bool:
    t = cancers.split(",")
    return any(o in MET_ROUTES.get(p, []) for p in t for o in t if o != p)


def fit(df, y):
    X = sm.add_constant(df[["MUTYH_het", "age", "sex_male"] + PCS])
    m = sm.Logit(y.astype(int), X).fit(disp=False)
    lo, hi = np.exp(m.conf_int().loc["MUTYH_het"])
    return dict(n_outcome=int(y.sum()), OR=np.exp(m.params["MUTYH_het"]), ci=(lo, hi), p=m.pvalues["MUTYH_het"])


def main(cohort_csv):
    df = pd.read_csv(cohort_csv)
    both = (df.second_primary == 1) & (df.mets_conservative == 1)
    flagged = set(df.loc[both & df.all_cancer_types.apply(plausible_met), "person_id"])
    c = df[(df.is_case == 1) & (df.has_pcs == 1)]
    clean = c[c.mets_conservative == 0]
    without_routes = c[~c.person_id.isin(flagged)]
    rows = [dict(definition='original', **fit(c,c.second_primary)),
            dict(definition='without_any_metastasis', **fit(clean,clean.second_primary)),
            dict(definition='without_plausible_routes', **fit(without_routes,without_routes.second_primary))]
    external('LEGACY_CONTAMINATION_OUTPUT',True).write_text(json.dumps(rows,default=float))


if __name__ == "__main__":
    import sys
    main(sys.argv[1])
