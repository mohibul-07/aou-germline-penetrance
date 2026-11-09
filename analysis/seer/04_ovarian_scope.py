"""Ovarian site-scope sensitivity query - RECOVERED (October 22, 2026).

Purpose: measure how much of the ovarian group rests on non-ovarian evidence
(fallopian-tube cancer, unspecified adnexal cancer, a fallopian lesion), using
the same 2023 rules and the unchanged primary denominator.

Provenance: inspection msg 3267 (concept labels from the saved vocabulary
audit), dry run msg 3305, execution msg 3317 (job 6b7200ee-...), 6 GiB cap.
SQL in analysis/seer/sql.py:ovarian_scope, unchanged. The historical cell
embedded the four concept-ID lists as literals; recovery reads them from an
external reviewed file so Rita's private mapping stays out of source code.

Inputs: OVARY_SCOPE_MAPPING CSV (concept_id, scope_class) where scope_class is
ovary | fallopian_cancer | adnexal | lesion; CANCER_MAPPING; WGS_ROSTER; CDR
tables; REFERENCE_DATE. Restore the classes from the historical Workbench
metadata rita_ovarian_scope_audit_2023_metadata.json.
Outputs (outside repo): OVARY_* SQL, metadata and three-row Parquet.

Decisions:
- The four classes must partition the original ovarian concepts exactly, with
  exactly one adnexal and one lesion concept (as historically).
- The lesion concept's name does not establish malignancy. SEER Ovary excludes
  fallopian tube (other female genital sites).
- Non-ovarian breakdown is hierarchical: fallopian cancer, then adnexal, then
  lesion only.
- Never edit CANCER_MAPPING and never promote the ovary-only set to primary
  without review.
"""
import csv

from analysis.seer import sql
from analysis.seer.common import mapping_pairs, reference_date, roster_parameter
from workflow.runtime import cdr, external, run_query, update_json

CLASSES = ("ovary", "fallopian_cancer", "adnexal", "lesion")


def scope_classes(rows, original_ids):
    """Validate the reviewed class file against the original ovarian concepts."""
    classes = {c: [] for c in CLASSES}
    for row in rows:
        if row["scope_class"] not in classes:
            raise ValueError("Unknown ovarian scope class")
        classes[row["scope_class"]].append(int(row["concept_id"]))
    flat = [i for ids in classes.values() for i in ids]
    if len(flat) != len(set(flat)) or set(flat) != set(original_ids):
        raise ValueError("Scope classes must partition the original ovarian concepts")
    if len(classes["adnexal"]) != 1 or len(classes["lesion"]) != 1 or not classes["ovary"]:
        raise ValueError("Expected one adnexal concept, one lesion concept and ovary concepts")
    return {c: sorted(ids) for c, ids in classes.items()}


def main():
    from google.cloud import bigquery
    original = sorted(i for cancer, i in mapping_pairs() if cancer == "ovarian")
    with external("OVARY_SCOPE_MAPPING").open(encoding="utf-8-sig", newline="") as handle:
        classes = scope_classes(list(csv.DictReader(handle)), original)
    params = [
        roster_parameter(),
        bigquery.ArrayQueryParameter("original_ids", "INT64", original),
        bigquery.ArrayQueryParameter("ovary_ids", "INT64", classes["ovary"]),
        bigquery.ArrayQueryParameter("fallopian_ids", "INT64", classes["fallopian_cancer"]),
        bigquery.ScalarQueryParameter("adnexal_id", "INT64", classes["adnexal"][0]),
        bigquery.ScalarQueryParameter("lesion_id", "INT64", classes["lesion"][0]),
        bigquery.ScalarQueryParameter("reference_date", "DATE", reference_date()),
    ]
    if run_query(sql.ovarian_scope(cdr()), params, "OVARY", cap_gib=6):
        update_json("OVARY_METADATA", {
            "reference_date": reference_date().isoformat(),
            "concepts_per_class": {c: len(ids) for c, ids in classes.items()},
            "denominator": "Unchanged primary diagnosis-coverage population",
            "nonovarian_breakdown": "Hierarchical: fallopian cancer, then adnexal cancer, then lesion only",
            "original_primary_definition_modified": False,
            "status": "Separate site-scope sensitivity; revised primary requires review",
            "dissemination": "Internal Workbench output; suppress small cells before external sharing",
        })


if __name__ == "__main__":
    main()
