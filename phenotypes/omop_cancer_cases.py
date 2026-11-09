"""Build cancer case flags and first diagnosis dates from OMOP concept IDs (v9 CDR).

Inputs: reviewed workbook supplied by caller. Output: in-memory concept lists.
Decision: preserve original workbook groups, no descendants; extraction CLI disabled
because the reconstruction queried all CDR people without roster/date restrictions.
"""
import pandas as pd

CANCER_GROUPS = {
    "Breast": ["Breast"],
    "Prostate": ["Prostate"],
    "Colorectal": ["Colorectum"],
    "Lung": ["Lung"],
    "Kidney": ["Kidney"],
    "Ovarian": ["Ovary"],
    "Pancreatic": ["Pancreas"],
    "Stomach": ["Stomach"],
}
MELANOMA_GROUPS = ["Skin", "Skin ", "Skin/Mucosa"]


def load_concepts(xlsx: str) -> dict[str, list[int]]:
    m = pd.read_excel(xlsx)
    out = {}
    for cancer, groups in CANCER_GROUPS.items():
        out[cancer] = m.loc[m["Group"].isin(groups), "OMOP Concept ID"].dropna().astype(int).unique().tolist()
    skin = m[m["Group"].isin(MELANOMA_GROUPS)]
    mel = skin[skin["Name of Condition"].str.contains("melanoma", case=False, na=False)]
    out["Melanoma"] = mel["OMOP Concept ID"].dropna().astype(int).unique().tolist()
    return out


def main():
    raise RuntimeError("Use analysis/seer/01_prevalence_counts.py for aggregate comparisons; legacy unrestricted extraction was not exported as an executed step")

if __name__ == "__main__":
    main()
