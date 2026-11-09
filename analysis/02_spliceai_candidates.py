"""High-SpliceAI variants not classified P/LP in ClinVar (reclassification candidates).

Max of the four SpliceAI delta scores; thresholds 0.2 / 0.5 / 0.8.
Pre-filter the VAT columns in shell first, e.g.:
  awk -F'\\t' 'NR==1 || ($44=="BRCA1" && $56=="true")' brca1_vat.tsv | cut -f1,44,90,92,94,96
(column numbers from carriers/vat_columns.sh)
"""
import argparse

import pandas as pd


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--spliceai-tsv", required=True, help="vid, gene_symbol, 4 splice_ai_*_score columns")
    p.add_argument("--plp-vids", required=True, help="file with a 'vid' column (ClinVar P/LP)")
    p.add_argument("--threshold", type=float, default=0.5)
    p.add_argument("--out", required=True)
    a = p.parse_args()

    df = pd.read_csv(a.spliceai_tsv, sep="\t")
    score_cols = [c for c in df.columns if c.endswith("_score")]
    df[score_cols] = df[score_cols].apply(pd.to_numeric, errors="coerce")
    df["max_spliceai"] = df[score_cols].max(axis=1)
    plp = set(pd.read_csv(a.plp_vids)["vid"])
    df["is_plp"] = df["vid"].isin(plp)

    hi = df[df["max_spliceai"] >= a.threshold]
    pass  # Output withheld: never print controlled counts.
    hi[~hi["is_plp"]].sort_values("max_spliceai", ascending=False).to_csv(a.out, index=False)


if __name__ == "__main__":
    main()
