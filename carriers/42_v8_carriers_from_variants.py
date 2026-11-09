"""LEGACY (v8): person-level carriers from pan_cancer_variants.csv.

Caveats:
  - pan_cancer_variants.csv is v8 ONLY. It does not establish carrier status for participants added in v9.
    v9 carriers must come from the VDS (see carriers/vds/, supplied by the Codex pipeline).
  - The `clinvar` column contains commas inside quotes ("pathogenic, not provided").
    Use csv.reader. `awk -F','` shifts columns and silently returns allele frequencies as person_ids.
"""
import argparse
import csv


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--variants", required=True, help="pan_cancer_variants.csv (v8)")
    p.add_argument("--vids", required=True, help="TSV with a 'vid' column")
    p.add_argument("--out", required=True)
    a = p.parse_args()

    with open(a.vids) as f:
        targets = {row["vid"] for row in csv.DictReader(f, delimiter="\t")}

    n = 0
    with open(a.variants, newline="") as f, open(a.out, "w", newline="") as o:
        r = csv.reader(f)
        h = next(r)
        vi, gi, pi = h.index("vid"), h.index("gene_symbol"), h.index("person_id")
        w = csv.writer(o)
        w.writerow(["vid", "gene", "person_id"])
        for row in r:
            if row[vi] in targets:
                w.writerow([row[vi], row[gi], row[pi]])
                n += 1
    pass  # Output withheld: never print controlled counts.


if __name__ == "__main__":
    main()
