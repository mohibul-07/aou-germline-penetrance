"""Vocabulary and replacement audits of Rita's mapping - RECOVERED (October 21, 2026).

Purpose: check every selected concept against the CDR vocabulary and list the
explicit relationships of retired/updated concepts, WITHOUT changing the
phenotype.

Provenance (Codex cells, SQL in analysis/seer/sql.py, unchanged):
- vocabulary: msg 2472 dry run, msg 2482 execution (job 29c127ba-...), 2 GiB cap;
- replacements: msg 2494 dry run, msg 2514 execution (job 7e01f254-...), 4 GiB cap;
- impact: msg 2524, DRY RUN ONLY. Md stopped this step (msgs 2541-2554) and
  the original mapping was frozen. It was never executed, so no impact result
  exists. The CLI refuses it unless ALLOW_UNRUN_IMPACT_AUDIT=1.

Inputs: CANCER_MAPPING (from analysis.seer.00_rita_mapping); WGS_ROSTER for
impact only. Outputs (outside repo): VOCAB_* and REPLACEMENT_* SQL, metadata
and Parquet; IMPACT_* only if explicitly enabled.

Decisions:
- Original concepts are preserved even when retired; replacements are
  candidates only. Example from the audit: the retired prostate metastasis
  concept maps to a site-unspecified metastatic neoplasm, which must never be
  added to prostate.
- Impact candidates (if ever run): valid relationship, valid standard target,
  Condition domain, not already in the original pairs.

Usage: python -m phenotypes.concept_audit [vocabulary|replacements|impact]
"""
import json
import os
import sys

from analysis.seer import sql
from analysis.seer.common import mapping_pairs, roster_parameter
from workflow.runtime import cdr, external, run_query, update_json


def vocabulary():
    from google.cloud import bigquery
    ids = sorted({concept_id for _, concept_id in mapping_pairs()})
    if not run_query(sql.concept_vocabulary_audit(cdr()),
                     [bigquery.ArrayQueryParameter("concept_ids", "INT64", ids)],
                     "VOCAB", cap_gib=2):
        return
    import pyarrow.parquet as pq
    rows = pq.read_table(external("VOCAB_OUTPUT")).to_pylist()
    found = [r["concept_id"] for r in rows]
    if len(found) != len(set(found)) or not set(found) <= set(ids):
        raise ValueError("Unexpected vocabulary rows")
    update_json("VOCAB_METADATA", {
        "requested_unique_concepts": len(ids),
        "found_unique_concepts": len(found),
        "missing_concept_ids": sorted(set(ids) - set(found)),
        "patient_records_queried": False,
        "mapping_changed": False,
    })


def obsolete_ids():
    import pyarrow.parquet as pq
    rows = pq.read_table(external("VOCAB_OUTPUT")).to_pylist()
    return sorted(r["concept_id"] for r in rows if r["invalid_reason"])


def replacements():
    from google.cloud import bigquery
    ids = obsolete_ids()
    if not run_query(sql.replacement_audit(cdr()),
                     [bigquery.ArrayQueryParameter("concept_ids", "INT64", ids)],
                     "REPLACEMENT", cap_gib=4):
        return
    import pyarrow.parquet as pq
    rows = pq.read_table(external("REPLACEMENT_OUTPUT")).to_pylist()
    if not all(r["original_concept_id"] in ids for r in rows):
        raise ValueError("Relationship for a concept that was not requested")
    update_json("REPLACEMENT_METADATA", {
        "obsolete_concept_ids_reviewed": len(ids),
        "relationship_rows": len(rows),
        "patient_records_queried": False,
        "phenotype_mapping_modified": False,
        "interpretation": "Relationship candidates only; no replacement automatically adopted.",
    })


def impact_mapping(original_pairs, replacement_rows):
    """Recovered msg 2524 candidate logic. Pure function."""
    original_set = set(original_pairs)
    cancer_by_original = {concept_id: cancer for cancer, concept_id in original_pairs}
    candidates = sorted({
        (cancer_by_original[r["original_concept_id"]], r["target_concept_id"])
        for r in replacement_rows
        if r["relationship_invalid_reason"] is None
        and r["target_invalid_reason"] is None
        and r["target_standard_status"] == "S"
        and r["target_domain"] == "Condition"
    })
    additions = [p for p in candidates if p not in original_set]
    return ([{"cancer": c, "concept_id": i, "mapping_set": "original"} for c, i in original_pairs]
            + [{"cancer": c, "concept_id": i, "mapping_set": "replacement_candidate"} for c, i in additions])


def impact():
    if os.environ.get("ALLOW_UNRUN_IMPACT_AUDIT", "0") != "1":
        raise RuntimeError("Historically dry-run only and never executed; set ALLOW_UNRUN_IMPACT_AUDIT=1 "
                           "only after review. Per-concept participant counts need small-cell review.")
    import pyarrow.parquet as pq
    from google.cloud import bigquery
    rows = pq.read_table(external("REPLACEMENT_OUTPUT")).to_pylist()
    mapping = impact_mapping(mapping_pairs(), rows)
    run_query(sql.replacement_impact(cdr()),
              [roster_parameter(), bigquery.ScalarQueryParameter("mapping_json", "STRING", json.dumps(mapping))],
              "IMPACT", cap_gib=6)


def main(argv=None):
    step = (argv if argv is not None else sys.argv[1:] or ["vocabulary"])[0]
    {"vocabulary": vocabulary, "replacements": replacements, "impact": impact}[step]()


if __name__ == "__main__":
    main()
