""">=2 cancer dates within the same cancer, fixed denominator - RECOVERED (Oct 22, 2026).

Purpose: test how much prevalence depends on single-date cancer coding, while
keeping the approved primary denominator (>=1 dated condition) fixed. This is a
numerator sensitivity, separate from the coverage sensitivity in step 05.

Provenance:
- query: msg 3187 dry run, msg 3199 execution (job 4ee8fb8a-...), 6 GiB cap;
  SQL in analysis/seer/sql.py:cancer_date_sensitivity, unchanged;
- comparison: msg 3199 (in-memory), saved by recovery cell msg 3233 after the
  original cell stalled while printing (cause not established; the recovery
  called Python builtins explicitly and did not repeat the query);
- summary: msg 3245 (seer_cancer_date_sensitivity_summary_2023.csv).

Inputs: WGS_ROSTER, CANCER_MAPPING, CDR tables, REFERENCE_DATE; SEER_COMPARISONS.
Outputs (outside repo): CANCER_DATE_* SQL/metadata/Parquet counts,
CANCER_DATE_SENSITIVITY CSV, CANCER_DATE_SUMMARY CSV.

Decisions:
- Same 2023 rules as the primary: diagnoses before reference, age >= 40 for
  matched bands, no primary death on/before reference, Female/Male, breast and
  ovary Female only, prostate Male only.
- Every >=1-date case count must reproduce the saved primary count exactly
  before any sensitivity value is computed (all 45 did historically).
- Repeated codes do not independently confirm disease, and single-date records
  are not automatically false positives. No threshold is chosen to match SEER.

Usage: python -m analysis.seer.03_cancer_date_sensitivity [run|compare|summary]
  run     = query (dry run unless RUN_QUERIES=1), then compare;
  compare = rebuild the comparison from saved counts without any query.
"""
import csv
import sys

from analysis.seer import sql
from analysis.seer.common import mapping_parameter, reference_date, roster_parameter
from workflow.runtime import cdr, env, external, run_query, update_json


def comparisons(counts, baseline_rows, reference):
    """Recovered msg 3199 comparison. counts: query rows; baseline_rows:
    SEER_COMPARISONS rows (strings or numbers). Pure function."""
    baseline = {}
    for row in baseline_rows:
        if row["coverage_rule"] != "ge1_dated_condition":
            continue
        key = (row["cancer"], row["sex_at_birth"], row["age_band"])
        if key in baseline:
            raise ValueError("Duplicate baseline stratum")
        baseline[key] = row
    out, seen = [], set()
    for row in counts:
        key = (row["cancer"], row["sex_at_birth"], row["age_band"])
        if key not in baseline or key in seen:
            raise ValueError(f"Unexpected or duplicate stratum {key}")
        seen.add(key)
        original = baseline[key]
        one = int(row["cases_ge1_cancer_date"])
        two = int(row["cases_ge2_cancer_dates"])
        single = int(row["cases_exactly1_cancer_date"])
        denominator = int(original["aou_denominator"])
        if one != int(original["aou_cases"]):
            raise ValueError(f"Baseline mismatch for {key}")
        if two + single != one or not 0 <= two <= one <= denominator or denominator <= 0:
            raise ValueError(f"Invalid counts for {key}")
        primary_percent = 100 * one / denominator
        sensitivity_percent = 100 * two / denominator
        published = str(original["seer_percent_as_published"]).strip()
        bounded = published.startswith("<")
        seer_value = float(published.lstrip("<").strip())
        ratio_available = not bounded and seer_value > 0
        out.append({
            "reference_date": reference,
            "cancer": row["cancer"],
            "sex_at_birth": row["sex_at_birth"],
            "age_band": row["age_band"],
            "fixed_primary_denominator": denominator,
            "cases_ge1_cancer_date": one,
            "cases_ge2_cancer_dates": two,
            "cases_exactly1_cancer_date": single,
            "case_retention_percent": 100 * two / one if one else None,
            "primary_prevalence_percent": primary_percent,
            "ge2_cancer_dates_prevalence_percent": sensitivity_percent,
            "change_percentage_points": sensitivity_percent - primary_percent,
            "seer_percent_as_published": published,
            "seer_value_is_upper_bound": bounded,
            "primary_aou_to_seer_ratio_approximate": primary_percent / seer_value if ratio_available else None,
            "ge2_cancer_dates_aou_to_seer_ratio_approximate":
                sensitivity_percent / seer_value if ratio_available else None,
            "site_scope_status": original["site_scope_status"],
        })
    if seen != set(baseline):
        raise ValueError("Not every baseline stratum was reproduced")
    return out


def summary(rows):
    """Recovered msg 3245 summary over saved CSV rows (empty string = no ratio)."""
    out = []
    for cancer, sex in sorted({(r["cancer"], r["sex_at_birth"]) for r in rows}):
        selected = [r for r in rows if r["cancer"] == cancer and r["sex_at_birth"] == sex]
        point = [r for r in selected
                 if r["primary_aou_to_seer_ratio_approximate"] not in ("", None)
                 and r["ge2_cancer_dates_aou_to_seer_ratio_approximate"] not in ("", None)]
        primary = [float(r["primary_aou_to_seer_ratio_approximate"]) for r in point]
        repeated = [float(r["ge2_cancer_dates_aou_to_seer_ratio_approximate"]) for r in point]
        out.append({
            "cancer": cancer,
            "sex_at_birth": sex,
            "strata_with_point_ratios": len(point),
            "strata_without_point_ratios": len(selected) - len(point),
            "primary_ratio_min": min(primary) if point else None,
            "primary_ratio_max": max(primary) if point else None,
            "ge2_cancer_dates_ratio_min": min(repeated) if point else None,
            "ge2_cancer_dates_ratio_max": max(repeated) if point else None,
            "site_scope_status": selected[0]["site_scope_status"],
        })
    return out


def _write(var, rows):
    with external(var, True).open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _read(var):
    with external(var).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def compare():
    import pyarrow.parquet as pq
    counts = pq.read_table(external("CANCER_DATE_OUTPUT")).to_pylist()
    rows = comparisons(counts, _read("SEER_COMPARISONS"), env("REFERENCE_DATE"))
    _write("CANCER_DATE_SENSITIVITY", rows)
    update_json("CANCER_DATE_METADATA", {
        "reference_date": env("REFERENCE_DATE"),
        "strata": len(rows),
        "all_baseline_case_counts_reproduced": True,
        "denominator": "Fixed primary population with >=1 dated condition",
        "case_sensitivity": ">=2 distinct dates with original mapped cancer concepts",
        "original_primary_definition_changed": False,
        "interpretation": "Repeated coding does not independently confirm a diagnosis.",
        "dissemination": "Internal Workbench output; suppress small cells before external sharing",
    })


def run():
    from google.cloud import bigquery
    params = [roster_parameter(), mapping_parameter(),
              bigquery.ScalarQueryParameter("reference_date", "DATE", reference_date())]
    if run_query(sql.cancer_date_sensitivity(cdr()), params, "CANCER_DATE", cap_gib=6):
        compare()


def write_summary():
    _write("CANCER_DATE_SUMMARY", summary(_read("CANCER_DATE_SENSITIVITY")))


def main(argv=None):
    step = (argv if argv is not None else sys.argv[1:] or ["run"])[0]
    {"run": run, "compare": compare, "summary": write_summary}[step]()


if __name__ == "__main__":
    main()
