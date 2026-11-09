"""Carrier-cancer association, ancestry-PC adjusted (one cancer type vs controls).

Model: cancer ~ carrier + age + sex_male + PC1..PC16, participants with PCs only.
  - Drop sex_male for sex-specific cancers (Ovarian, Prostate) -> otherwise singular matrix.
  - Skip pairs with < 3 total carriers; report case/control carrier counts with every estimate.
  - Benjamini-Hochberg FDR across all tests.
  - scikit-learn breaks on the AoU Hail/Dataproc image (numpy dtype size changed); use statsmodels.
  - For sparse carriers (separation), use Firth regression (`firthmodels`) instead of plain Logit.

Historical result values removed for code-only export. This draft is not a validated model.
"""
import argparse

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests

PCS = [f"pc{i}" for i in range(1, 17)]
CANCERS = ["Breast", "Prostate", "Ovarian", "Colorectal", "Melanoma", "Lung", "Kidney", "Pancreatic", "Stomach"]
SEX_SPECIFIC = {"Ovarian", "Prostate"}


def fit(df, carrier_col, cancer, control_label="Control"):
    s = df[df["group"].isin([cancer, control_label]) & (df["has_pcs"] == 1)].copy()
    s["y"] = (s["group"] == cancer).astype(int)
    n_case = int(s.loc[s.y == 1, carrier_col].sum())
    n_ctrl = int(s.loc[s.y == 0, carrier_col].sum())
    if n_case + n_ctrl < 3:
        return None
    cov = ["age"] + PCS + ([] if cancer in SEX_SPECIFIC else ["sex_male"])
    X = sm.add_constant(s[[carrier_col] + cov])
    m = sm.Logit(s["y"], X).fit(disp=False, maxiter=200)
    lo, hi = np.exp(m.conf_int().loc[carrier_col])
    return dict(cancer=cancer, case_carriers=n_case, ctrl_carriers=n_ctrl,
                OR=np.exp(m.params[carrier_col]), ci_lo=lo, ci_hi=hi, p=m.pvalues[carrier_col])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cohort", required=True, help="one row per person: group, age, sex_male, has_pcs, pc1..pc16")
    ap.add_argument("--carriers", required=True, help="person_id, gene (or vid)")
    ap.add_argument("--unit", default="gene", choices=["gene", "vid"])
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    df = pd.read_csv(a.cohort)
    car = pd.read_csv(a.carriers)
    rows = []
    for unit, g in car.groupby(a.unit):
        df["carrier"] = df["person_id"].isin(set(g["person_id"])).astype(int)
        for c in CANCERS:
            try:
                r = fit(df, "carrier", c)
            except Exception as e:  # perfect separation etc.
                r = dict(cancer=c, error=str(e))
            if r:
                rows.append({a.unit: unit, **r})
    res = pd.DataFrame(rows)
    ok = res["p"].notna()
    res.loc[ok, "fdr_q"] = multipletests(res.loc[ok, "p"], method="fdr_bh")[1]
    res.to_csv(a.out, index=False)
    pass  # Output withheld: never print controlled counts.


if __name__ == "__main__":
    main()
