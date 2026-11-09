"""WGS/EHR diagnosis-coverage preflight - RECOVERED original SQL (October 21, 2026).

Purpose: before any phenotype or SEER work, measure how much of the verified v9
WGS roster has usable diagnosis data, and compare that with the program EHR flag.

Provenance: Codex session cells msg 2397 (schema check, 15:16Z), msg 2409
(dry run, 15:17Z) and msg 2419 (execution, 15:20Z; job 6d2f1f73-...).
The SQL is in analysis/seer/sql.py:coverage_preflight, unchanged.

Inputs: WGS_ROSTER Parquet (person_id); CDR tables cb_search_person,
condition_occurrence, concept, person (schema check only).
Outputs (outside repo): COVERAGE_SCHEMA JSON; COVERAGE_SQL, COVERAGE_METADATA
and the one-row aggregate COVERAGE_OUTPUT Parquet.

Decisions:
- Diagnosis dates use condition_start_date (DATE), never the datetime column.
- The verified roster (exact, unique) is authoritative; program WGS flags are
  audited against it, not used to define it.
- ICD comparison uses the source concept vocabulary ICD9CM/ICD10CM.
- No age, death or cancer exclusion is applied at this stage.
- After review with Md, primary coverage = >=1 dated condition of any
  diagnosis; >=2 distinct condition dates = coverage sensitivity (msg 2439).
- Historical billing cap: 5 GiB.

Repairs made during recovery (not historical behavior): the hard-coded
roster total in the original asserts is replaced by the roster file's length;
results are written to metadata instead of printed.

Usage: python -m analysis.00_ehr_coverage_check [schema|run]
"""
import sys

from analysis.seer import sql
from analysis.seer.common import roster_ids, roster_parameter
from workflow.runtime import cdr, env, external, run_query, update_json, write_json

REQUIRED_COLUMNS = {
    "cb_search_person": ["person_id", "has_ehr_data", "has_whole_genome_variant"],
    "condition_occurrence": [
        "person_id", "condition_concept_id", "condition_source_concept_id",
        "condition_start_date", "condition_type_concept_id",
    ],
    "person": ["person_id", "birth_datetime", "year_of_birth", "sex_at_birth_concept_id"],
}


def query(dataset):
    return sql.coverage_preflight(dataset)


def schema_check():
    """Recovered msg 2397: table schemas only, no clinical rows are read."""
    from google.cloud import bigquery
    client = bigquery.Client(project=env("GOOGLE_PROJECT"))
    found = {}
    for table_name, columns in REQUIRED_COLUMNS.items():
        fields = {f.name: f.field_type for f in client.get_table(f"{cdr()}.{table_name}").schema}
        found[table_name] = {c: fields.get(c, "NOT PRESENT") for c in columns}
    write_json("COVERAGE_SCHEMA", {"cdr": cdr(), "columns": found,
                                   "clinical_query_performed": False})


def validate(counts, roster_total):
    """Recovered msg 2419 identities; raises if any fails."""
    if counts["verified_wgs_roster"] != roster_total:
        raise ValueError("Roster count mismatch")
    if not (counts["roster_with_ge2_condition_dates"] <= counts["roster_with_dated_condition"]
            <= counts["roster_with_any_condition"] <= counts["verified_wgs_roster"]):
        raise ValueError("Coverage counts are not nested")
    if not (counts["roster_with_dated_icd_source_condition"] <= counts["roster_with_icd_source_condition"]
            <= counts["roster_with_any_condition"]):
        raise ValueError("ICD counts are not nested")
    if counts["roster_with_dated_icd_source_condition"] > counts["roster_with_dated_condition"]:
        raise ValueError("Dated ICD exceeds dated coverage")
    if counts["program_wgs_flag_total"] != (counts["roster_with_program_wgs_flag"]
                                            + counts["program_wgs_flag_outside_verified_roster"]):
        raise ValueError("Program WGS flag identity failed")


def run():
    import pyarrow.parquet as pq
    ids = roster_ids()
    if not run_query(query(cdr()), [roster_parameter(ids)], "COVERAGE", cap_gib=5):
        return
    rows = pq.read_table(external("COVERAGE_OUTPUT")).to_pylist()
    if len(rows) != 1:
        raise ValueError("Expected one aggregate row")
    validate(rows[0], len(ids))
    update_json("COVERAGE_METADATA", {
        "roster": "Previously verified v9 WGS roster",
        "age_or_cancer_exclusions_applied": False,
        "primary_coverage": "At least one dated condition of any diagnosis",
        "sensitivity_coverage": "At least two distinct condition dates",
        "icd_comparison": "Source concept vocabulary ICD9CM or ICD10CM",
        "dissemination": "Internal Workbench output; review every nonzero count before sharing",
    })


def main(argv=None):
    step = (argv if argv is not None else sys.argv[1:] or ["run"])[0]
    {"schema": schema_check, "run": run}[step]()


if __name__ == "__main__":
    main()
