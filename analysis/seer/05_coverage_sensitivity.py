"""Coverage sensitivity: >=1 versus >=2 ANY diagnosis dates - RECOVERED (Oct 22, 2026).

Purpose: show how requiring more diagnosis activity changes prevalence. This
check changes the denominator (and the cases within it). It is NOT the
repeated-cancer-date rule in 03_cancer_date_sensitivity.

Provenance: second half of consolidation cell msg 3149 (2026-10-22T14:13Z).
Columns, pairing and checks unchanged. No BigQuery scan.

Input: SEER_COMPARISONS (from 02_compare).
Output (outside repo): COVERAGE_SENSITIVITY CSV, 45 rows when complete
(historical seer_all_nine_coverage_sensitivity_2023.csv).

Decisions: the stricter rule must not add cases or denominator; differences
are percentage points; retained denominator is a percentage of primary.
Historical finding (internal): prevalence rose in every stratum, so this
check did not explain the AoU excess; primary coverage was retained.
"""
import csv

from workflow.runtime import external


def coverage_sensitivity(combined):
    """Pure function over consolidated comparison rows (numeric fields)."""
    lookup = {}
    for row in combined:
        key = (row["cancer"], row["sex_at_birth"], row["age_band"], row["coverage_rule"])
        if key in lookup:
            raise ValueError("Duplicate stratum")
        lookup[key] = row
    out = []
    for row in combined:
        if row["coverage_rule"] != "ge1_dated_condition":
            continue
        stricter = lookup[(row["cancer"], row["sex_at_birth"], row["age_band"], "ge2_condition_dates")]
        if stricter["aou_cases"] > row["aou_cases"] or stricter["aou_denominator"] > row["aou_denominator"]:
            raise ValueError("Stricter coverage added participants")
        out.append({
            "cancer": row["cancer"],
            "sex_at_birth": row["sex_at_birth"],
            "age_band": row["age_band"],
            "primary_cases": row["aou_cases"],
            "primary_denominator": row["aou_denominator"],
            "primary_percent": row["aou_percent"],
            "ge2_dates_cases": stricter["aou_cases"],
            "ge2_dates_denominator": stricter["aou_denominator"],
            "ge2_dates_percent": stricter["aou_percent"],
            "change_percentage_points": stricter["aou_percent"] - row["aou_percent"],
            "denominator_retained_percent": 100 * stricter["aou_denominator"] / row["aou_denominator"],
        })
    return out


def read_comparisons():
    with external("SEER_COMPARISONS").open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row["aou_cases"] = int(row["aou_cases"])
        row["aou_denominator"] = int(row["aou_denominator"])
        row["aou_percent"] = float(row["aou_percent"])
    return rows


def main():
    out = coverage_sensitivity(read_comparisons())
    if len(out) != 45:
        raise ValueError("Expected 45 paired strata")
    with external("COVERAGE_SENSITIVITY", True).open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(out[0]))
        writer.writeheader()
        writer.writerows(out)


if __name__ == "__main__":
    main()
