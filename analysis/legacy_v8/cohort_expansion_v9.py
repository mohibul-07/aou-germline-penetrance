"""Expand the v8 cohort with new v9 cancer cases (same OMOP concept definitions).

Steps: query each cancer's concept IDs in v9 condition_occurrence; keep person_ids not already in the
cohort; pull demographics; flag mets (secondary_cancer_concepts_final.csv); attach ancestry PCs.

v9 ancestry file: ancestry_preds.tsv, PCs packed as a list string in `pca_features` (16 values),
id column `research_id`. 

Known gaps after expansion:
  - Carrier flags (e.g., MUTYH_het) for new participants were set to 0 as placeholders;
    pan_cancer_variants.csv is v8-only. v9 carriers must come from the VDS.
  - `group` for multi-primary new participants was assigned alphabetically, not by earliest diagnosis.
"""
import ast
import os
from workflow.runtime import external

import pandas as pd


def parse_pcs(ancestry_tsv: str) -> pd.DataFrame:
    a = pd.read_csv(ancestry_tsv, sep="\t", usecols=["research_id", "pca_features"])
    pcs = pd.DataFrame(a["pca_features"].apply(ast.literal_eval).tolist(),
                       columns=[f"pc{i}" for i in range(1, 17)])
    pcs.insert(0, "person_id", a["research_id"].values)
    return pcs


if __name__ == "__main__":
    pcs = parse_pcs(os.environ["ANCESTRY"])
    pcs.to_parquet(external("LEGACY_PCS_OUTPUT",True),index=False)
