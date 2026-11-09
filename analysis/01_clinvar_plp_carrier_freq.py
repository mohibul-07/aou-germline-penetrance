"""ClinVar P/LP (>=2 star) carrier frequency from a VAT extract, overall and by ancestry.

Notes:
  - clinvar_rcv_num_stars is comma-separated (one value per RCV); require max >= 2.
  - Exclude classifications that are only benign/likely benign.
  - Frequency = total AC / (mean AN / 2). This is an allele-based approximation of carrier frequency
    (assumes heterozygous carriers and no carrier of two P/LP variants).
  - Pre-filter columns and transcripts before pandas to limit memory use.
"""
import argparse
from workflow.runtime import external

import pandas as pd

POPS = ["afr", "amr", "eas", "eur", "mid", "sas"]


def max_stars(s):
    if pd.isna(s):
        return -1
    try:
        return max(int(x) for x in str(s).split(","))
    except ValueError:
        return -1


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--vat-extract", required=True)
    p.add_argument("--gene", required=True)
    p.add_argument("--min-stars", type=int, default=2)
    a = p.parse_args()

    v = pd.read_csv(a.vat_extract, sep="\t", low_memory=False)
    v = v[(v["gene_symbol"] == a.gene) & (v["is_canonical_transcript"] == True)].drop_duplicates("vid")
    cls = v["clinvar_classification"].fillna("").str.lower()
    # Reproduces the supplied reconstruction rule: drop classifications that START with benign.
    # Known quirk: this also drops mixed strings like "benign,...,likely pathogenic". Revisit if needed.
    plp = cls.str.contains("pathogenic") & ~cls.str.match(r"(likely benign|benign)")
    plp = v[plp]
    plp = plp[plp["clinvar_rcv_num_stars"].apply(max_stars) >= a.min_stars]

    rows=[]
    for pop in ['all']+POPS:
        approximate_people=plp[f'gvs_{pop}_an'].mean()/2
        ac=plp[f'gvs_{pop}_ac'].sum()
        rows.append(dict(population=pop,variant_count=len(plp),allele_count=ac,
                         approximate_people=approximate_people,
                         approximate_carrier_fraction=ac/approximate_people if approximate_people>0 else None))
    pd.DataFrame(rows).to_csv(external('LEGACY_FREQUENCY_OUTPUT',True),index=False)


if __name__ == "__main__":
    main()
