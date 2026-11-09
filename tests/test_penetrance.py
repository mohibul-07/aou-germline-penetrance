import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[1] / "analysis" / "penetrance"))
from penetrance import penetrance_table  # noqa: E402


def synthetic():
    # 100 synthetic women, 6 carriers of v1 (BRCA1), 4 of them with breast cancer; 10 non-carrier cases
    cohort = pd.DataFrame({"person_id": range(100), "sex_at_birth": "Female", "age": 50, "eligible": True})
    carriers = pd.DataFrame({"person_id": range(6), "vid": "v1", "gene": "BRCA1", "zygosity": "het"})
    cases = pd.DataFrame({"person_id": list(range(4)) + list(range(50, 60)), "cancer": "Breast"})
    variants = pd.DataFrame({"vid": ["v1"], "gene": ["BRCA1"], "concordance_group": ["concordant"]})
    gene_cancer = pd.DataFrame({"gene": ["BRCA1"], "cancer": ["Breast"]})
    return carriers, cohort, cases, variants, gene_cancer


def test_penetrance_and_rd():
    r = penetrance_table(*synthetic(), min_carriers=6).iloc[0]
    assert r.n_carriers == 6 and r.carriers_affected == 4
    assert abs(r.penetrance - 4 / 6) < 1e-9
    assert abs(r.noncarrier_prev - 10 / 94) < 1e-9
    assert abs(r.risk_difference - (4 / 6 - 10 / 94)) < 1e-9


def test_min_carrier_filter():
    assert penetrance_table(*synthetic(), min_carriers=7).empty


def test_sex_restriction_excludes_men():
    carriers, cohort, cases, variants, gc = synthetic()
    cohort.loc[:2, "sex_at_birth"] = "Male"          # 3 carrier men drop out of breast analysis
    assert penetrance_table(carriers, cohort, cases, variants, gc, min_carriers=3).iloc[0].n_carriers == 3
