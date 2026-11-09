"""Original-mapping prevalence aggregates - RECOVERED (October 21, 2026).

Purpose: count, by sex and age band, participants with diagnosis coverage and
with each of the nine cancers under Rita's unchanged mapping.

Provenance (SQL in analysis/seer/sql.py, unchanged):
- baseline: msg 2554/2564, job 46c494d2-..., sex x birth-year bands, no age,
  death or sex-specific restriction. Preliminary only.
- v9cutoff: msg 2594/2604, job b51b114b-..., reference 2025-01-01, diagnoses
  ON OR BEFORE the date, 10-year age bands. Preserved as the separate initial
  baseline; never substituted for 2023 denominators.
- seer2023: msg 2725/2735, job 7645e039-..., reference 2023-01-01, diagnoses
  STRICTLY BEFORE the date, SEER-matchable bands 40-64/65-74/75+.
All historical runs used a 6 GiB cap.

Inputs: WGS_ROSTER, CANCER_MAPPING; CDR condition_occurrence, person, concept,
aou_death. V9_CUTOFF_REFERENCE_DATE (2025-01-01) and REFERENCE_DATE
(2023-01-01) select the reference dates.
Outputs (outside repo): BASELINE_*, PREVALENCE_2025_* and PREVALENCE_* SQL,
metadata and aggregate Parquet. v9cutoff also writes PREVALENCE_2025_LONG CSV
(historical seer_validation_aou_prevalence.csv layout).

Decisions:
- Coverage: >=1 dated condition before the reference (primary); >=2 distinct
  condition dates (coverage sensitivity, which also changes the denominator).
  `<cancer>_ge2_dates` = cancer AND >=2 condition dates of ANY diagnosis; it is
  the coverage sensitivity, NOT the >=2 cancer-date rule (see step 03).
- Completed age from birth_datetime at the reference date; adults >= 20.
- Death: earliest primary record in CDR aou_death; dated on/before reference
  -> recorded_deceased_by_reference. No death record does not verify survival.
- Status precedence: missing birth date, then under 20, then recorded death.
- Sex at birth = CDR concept name; non-Female/Male categories stay in the audit.
- Multiple cancers per participant are allowed. Original concepts only.

Repairs during recovery: the original asserts against literal coverage totals
now compare with the saved COVERAGE_OUTPUT; results are not printed.

Usage: python -m analysis.seer.01_prevalence_counts [baseline|v9cutoff|seer2023]
"""
import csv
import sys

from analysis.seer import sql
from analysis.seer.common import (ELIGIBLE_STATUS, SEX_RESTRICTIONS, coverage_totals,
                                  mapping_parameter, reference_date, roster_ids,
                                  roster_parameter)
from workflow.runtime import cdr, external, run_query, update_json

CANCERS = sql.CANCERS


def query(dataset):
    """The SEER-aligned 2023 query used by all later comparisons."""
    return sql.prevalence_seer_aligned(dataset)


def check_rows(rows, cancers=CANCERS):
    """Recovered msg 2604/2735 per-row nesting checks. Pure function."""
    for row in rows:
        primary = row["primary_coverage_denominator"]
        sensitivity = row["sensitivity_coverage_denominator"]
        if not 0 <= sensitivity <= primary <= row["wgs_participants"]:
            raise ValueError("Coverage denominators are not nested")
        for cancer in cancers:
            if not 0 <= row[f"{cancer}_ge2_dates"] <= row[cancer] <= primary:
                raise ValueError("Cancer counts are not nested")
            if row[f"{cancer}_ge2_dates"] > sensitivity:
                raise ValueError("Coverage-sensitivity cases exceed denominator")


def long_rows(rows, reference):
    """Recovered msg 2604 long layout for eligible Female/Male strata."""
    out = []
    for row in rows:
        if row["demographic_status"] != ELIGIBLE_STATUS or row["sex_at_birth"] not in {"Female", "Male"}:
            continue
        for cancer in CANCERS:
            if cancer in SEX_RESTRICTIONS and row["sex_at_birth"] != SEX_RESTRICTIONS[cancer]:
                continue
            for coverage, denominator, cases in [
                ("ge1_dated_condition", row["primary_coverage_denominator"], row[cancer]),
                ("ge2_condition_dates", row["sensitivity_coverage_denominator"], row[f"{cancer}_ge2_dates"]),
            ]:
                out.append({"reference_date": reference.isoformat(), "cancer": cancer,
                            "sex_at_birth": row["sex_at_birth"], "age_band": row["age_band"],
                            "coverage_rule": coverage, "cases": cases, "denominator": denominator,
                            "prevalence": cases / denominator if denominator else None})
    return out


def baseline():
    import pyarrow.parquet as pq
    if not run_query(sql.birth_year_baseline(cdr()), [roster_parameter(), mapping_parameter()],
                     "BASELINE", cap_gib=6):
        return
    rows = pq.read_table(external("BASELINE_OUTPUT")).to_pylist()
    totals = coverage_totals()
    if sum(r["participants_with_dated_condition"] for r in rows) != totals["roster_with_dated_condition"]:
        raise ValueError("Primary coverage does not match the preflight")
    if sum(r["participants_with_ge2_dates"] for r in rows) != totals["roster_with_ge2_condition_dates"]:
        raise ValueError("Sensitivity coverage does not match the preflight")
    for r in rows:
        if not 0 <= r["participants_with_ge2_dates"] <= r["participants_with_dated_condition"]:
            raise ValueError("Coverage counts are not nested")
        if any(not 0 <= r[c] <= r["participants_with_dated_condition"] for c in CANCERS):
            raise ValueError("Cancer count exceeds coverage")
    update_json("BASELINE_METADATA", {
        "mapping": "Original explicit Rita concepts; no replacements or descendants added",
        "case_dates": "At least one dated matching condition",
        "stratification": "Sex at birth and birth-year bands; not final age bands",
        "age_20_restriction_applied": False,
        "sex_specific_cancer_restrictions_applied": False,
        "alive_at_index_restriction_applied": False,
        "status": "Preliminary baseline; not final SEER-comparable prevalence",
    })


def _prevalence(query_text, prefix, date_var, extra):
    import pyarrow.parquet as pq
    from google.cloud import bigquery
    ids = roster_ids()
    reference = reference_date(date_var)
    params = [roster_parameter(ids), mapping_parameter(),
              bigquery.ScalarQueryParameter("reference_date", "DATE", reference)]
    if not run_query(query_text, params, prefix, cap_gib=6):
        return None, reference
    rows = pq.read_table(external(prefix + "_OUTPUT")).to_pylist()
    if sum(r["wgs_participants"] for r in rows) != len(ids):
        raise ValueError("Strata do not sum to the roster")
    check_rows(rows)
    update_json(prefix + "_METADATA", {
        "reference_date": reference.isoformat(),
        "mapping": "Original Rita concepts; replacements and descendants not added",
        "age": "Completed years from birth_datetime at reference date; age >=20",
        "death_rule": "Exclude primary recorded death dates on/before reference date",
        "no_recorded_death_does_not_verify_survival": True,
        "sex_restrictions": SEX_RESTRICTIONS,
        "other_sex_categories": "Retained in audit; excluded from Male/Female comparison",
        "dissemination": "Internal Workbench output; apply small-cell suppression before external sharing",
        **extra,
    })
    return rows, reference


def v9cutoff():
    rows, reference = _prevalence(sql.prevalence_v9_cutoff(cdr()), "PREVALENCE_2025",
                                  "V9_CUTOFF_REFERENCE_DATE", {
        "diagnosis_history": "On or before the reference date",
        "reference_source": "https://support.researchallofus.org/hc/en-us/articles/360033200232-Data-Dictionaries",
        "status": "Initial v9-cutoff baseline; not used for SEER comparisons",
    })
    if rows is None:
        return
    totals = coverage_totals()
    if sum(r["primary_coverage_denominator"] for r in rows) != totals["roster_with_dated_condition"]:
        raise ValueError("Primary coverage does not match the preflight")
    if sum(r["sensitivity_coverage_denominator"] for r in rows) != totals["roster_with_ge2_condition_dates"]:
        raise ValueError("Sensitivity coverage does not match the preflight")
    records = long_rows(rows, reference)
    with external("PREVALENCE_2025_LONG", True).open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def seer2023():
    _prevalence(query(cdr()), "PREVALENCE", "REFERENCE_DATE", {
        "diagnosis_history": "Strictly before the reference date",
        "matched_age_bands": ["40–64", "65–74", "75+"],
        "unmatched_youngest_band": "AoU 20–39 versus SEER <40; not compared",
        "population": "Retrospective v9 WGS roster with pre-reference diagnosis coverage",
        "limitations": [
            "Original OMOP phenotype versus registry invasive-cancer ascertainment",
            "Incomplete EHR history and death ascertainment",
            "Volunteer and diagnosis-coverage selection",
            "WGS roster established after the prevalence reference date",
            "No age standardization or confidence intervals computed in this step",
        ],
    })


def main(argv=None):
    step = (argv if argv is not None else sys.argv[1:] or ["seer2023"])[0]
    {"baseline": baseline, "v9cutoff": v9cutoff, "seer2023": seer2023}[step]()


if __name__ == "__main__":
    main()
