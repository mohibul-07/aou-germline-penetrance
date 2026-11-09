"""Dr. Huang's simple model: outcome = secondary cancer, tested on EVERYONE (cases + controls) with PCs.
Outcomes: mets_narrow, mets_conservative, second_primary. Controls contribute zero events.
"""
import sys

import numpy as np
import pandas as pd
import statsmodels.api as sm

PCS = [f"pc{i}" for i in range(1, 17)]

def main():
    from workflow.runtime import external
    df = pd.read_csv(external('LEGACY_COHORT'))
    full = df[df.has_pcs == 1]
    X = sm.add_constant(full[["MUTYH_het", "age", "sex_male"] + PCS])
    rows=[]
    for outcome in ["mets_narrow", "mets_conservative", "second_primary"]:
        m = sm.Logit(full[outcome], X).fit(disp=False)
        lo, hi = np.exp(m.conf_int().loc["MUTYH_het"])
        rows.append(dict(outcome=outcome,n_outcome=int(full[outcome].sum()),
                         OR=np.exp(m.params['MUTYH_het']),ci_lo=lo,ci_hi=hi,p=m.pvalues['MUTYH_het']))
    pd.DataFrame(rows).to_csv(external('LEGACY_SECONDARY_OUTPUT',True),index=False)

if __name__=='__main__': main()
