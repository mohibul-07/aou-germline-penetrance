"""Attach VAT allele counts to the ClinVar/ACMG concordance table and filter by carrier count.

Inputs:
  three_way_comparison.tsv  columns: key, gene, consequence, acmg, acmg_criteria, group
                            group in {concordant, clinvar_only, fastvep_only}
  panel_27_vat_ac.tsv       vid \t gvs_all_ac   (from 40_extract_vat_panel.sh)

AC is population-wide (~535K WGS). It is a screening proxy for carrier count, NOT the cohort carrier
count. Use it to decide which variants are worth person-level extraction.
"""
import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from keys import comparison_key_to_vat  # noqa: E402


def load_panel(path):
    return {l.strip() for l in open(path) if l.strip()}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--comparison", required=True)
    p.add_argument("--vat-ac", required=True)
    p.add_argument("--panel", required=True, help="config/panel_genes.txt")
    p.add_argument("--group", default="concordant")
    p.add_argument("--min-ac", type=int, default=10, help="keep variants with AC > min-ac")
    p.add_argument("--out", required=True)
    a = p.parse_args()

    ac = {}
    with open(a.vat_ac) as f:
        for line in f:
            vid, val = line.rstrip("\n").split("\t")[:2]
            ac[vid] = int(float(val or 0))

    panel = load_panel(a.panel)
    kept = []
    with open(a.comparison) as f:
        r = csv.DictReader(f, delimiter="\t")
        for row in r:
            if row["group"] != a.group or row["gene"] not in panel:   # drop off-panel neighbors
                continue
            vid = comparison_key_to_vat(row["key"])
            n = ac.get(vid, 0)
            if n > a.min_ac:
                kept.append((vid, row["gene"], row["consequence"], row["acmg"], row["acmg_criteria"], n))

    kept.sort(key=lambda x: -x[-1])
    with open(a.out, "w", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["vid", "gene", "consequence", "acmg", "acmg_criteria", "vat_ac"])
        w.writerows(kept)
    pass  # Output withheld: never print controlled counts.


if __name__ == "__main__":
    main()
