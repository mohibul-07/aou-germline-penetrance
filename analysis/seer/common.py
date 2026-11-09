"""Shared inputs for the recovered SEER steps.

Inputs: WGS_ROSTER Parquet (person_id), CANCER_MAPPING CSV written by
analysis.seer.00_rita_mapping (cancer, concept_id, workbook columns).
Outputs: BigQuery parameters and in-memory checks only; nothing is printed.

Decisions recovered from the October 21-22 cells:
- roster: the verified v9 WGS roster, unique non-null integer person_id,
  passed as one newline-joined STRING parameter (`@wgs_ids`);
- mapping: sorted unique (cancer, concept_id) pairs from Rita's workbook,
  passed as one JSON STRING parameter (`@mapping_json`), with no descendants
  or replacement concepts;
- sex labels are the CDR concept names 'Female' and 'Male'.
Expected historical totals (roster size, concept counts) are deliberately not
hard-coded; they live in the internal Workbench metadata, not in source.
"""
import csv
import json

from workflow.runtime import env, external

SEX_RESTRICTIONS = {"breast": "Female", "prostate": "Male", "ovarian": "Female"}
MATCHED_BANDS = ["40–64", "65–74", "75+"]
ELIGIBLE_STATUS = "adult_without_recorded_death_by_reference"


def roster_ids():
    import pyarrow.parquet as pq
    ids = pq.read_table(external("WGS_ROSTER"), columns=["person_id"],
                        use_threads=False)["person_id"].to_pylist()
    if any(v is None for v in ids) or len(ids) != len(set(ids)):
        raise ValueError("Roster IDs must be present and unique")
    return sorted(int(v) for v in ids)


def roster_parameter(ids=None):
    from google.cloud import bigquery
    ids = roster_ids() if ids is None else ids
    return bigquery.ScalarQueryParameter("wgs_ids", "STRING", "\n".join(map(str, ids)))


def mapping_pairs(var="CANCER_MAPPING"):
    with external(var).open(encoding="utf-8-sig", newline="") as handle:
        return sorted({(row["cancer"], int(row["concept_id"])) for row in csv.DictReader(handle)})


def mapping_parameter(pairs=None):
    from google.cloud import bigquery
    pairs = mapping_pairs() if pairs is None else pairs
    return bigquery.ScalarQueryParameter("mapping_json", "STRING", json.dumps(
        [{"cancer": cancer, "concept_id": concept_id} for cancer, concept_id in pairs]))


def reference_date(var="REFERENCE_DATE"):
    from datetime import date
    return date.fromisoformat(env(var))


def coverage_totals():
    """Return the saved preflight totals used to cross-check later queries.

    Historically the 376,944 / 363,410 coverage totals were asserted as
    literals. The recovered code compares against the saved preflight output
    instead, which is the same check without embedding a result in source.
    """
    import pyarrow.parquet as pq
    rows = pq.read_table(external("COVERAGE_OUTPUT")).to_pylist()
    if len(rows) != 1:
        raise ValueError("Coverage preflight output must have exactly one row")
    return rows[0]
