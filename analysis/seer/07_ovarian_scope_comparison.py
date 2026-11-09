"""Ovarian scope comparison with SEER - RECOVERED (October 22, 2026).

Purpose: put the ovary-specific counts on the fixed primary denominator and
compare them with the original definition and SEER Ovary. No BigQuery scan.

Provenance: comparison part of msg 3317 (2026-10-22T14:39Z). Checks, columns
and labels unchanged.

Inputs: OVARY_OUTPUT (04_ovarian_scope), SEER_COMPARISONS, CANCER_DATE_SENSITIVITY.
Output (outside repo): OVARY_COMPARISON CSV (historical
seer_ovarian_scope_sensitivity_2023.csv).

Decisions:
- Original >=1-date counts must equal the saved primary counts, and original
  >=2-date counts must equal the saved cancer-date sensitivity, in every band.
- Ovary-specific cases are a subset; the hierarchical non-ovarian breakdown
  must add up exactly.
- Ratio only for SEER point values > 0. Historical finding (internal): the
  narrower set changed prevalence only slightly, so it was not adopted.
"""
import csv

from workflow.runtime import env, external


def scope_comparison(scope_counts, baseline_rows, sensitivity_rows, reference):
    """Pure function. scope_counts are query rows; others are CSV rows."""
    baseline = {r["age_band"]: r for r in baseline_rows
                if r["cancer"] == "ovarian" and r["sex_at_birth"] == "Female"
                and r["coverage_rule"] == "ge1_dated_condition"}
    previous = {r["age_band"]: r for r in sensitivity_rows
                if r["cancer"] == "ovarian" and r["sex_at_birth"] == "Female"}
    if len(scope_counts) != 3 or {r["age_band"] for r in scope_counts} != {"40–64", "65–74", "75+"}:
        raise ValueError("Expected the three matched age bands")
    out = []
    for row in scope_counts:
        band = row["age_band"]
        original = baseline[band]
        denominator = int(original["aou_denominator"])
        if row["original_cases"] != int(original["aou_cases"]):
            raise ValueError("Original ovarian cases did not reproduce")
        if row["original_cases_ge2_cancer_dates"] != int(previous[band]["cases_ge2_cancer_dates"]):
            raise ValueError("Original >=2-date ovarian cases did not reproduce")
        if row["explicitly_ovarian_cases"] + row["without_explicit_ovarian_evidence"] != row["original_cases"]:
            raise ValueError("Ovarian partition failed")
        if (row["no_ovarian_with_fallopian_cancer"] + row["no_ovarian_or_fallopian_with_adnexal_cancer"]
                + row["lesion_only"] != row["without_explicit_ovarian_evidence"]):
            raise ValueError("Non-ovarian breakdown failed")
        if not (0 <= row["explicitly_ovarian_cases_ge2_dates"] <= row["explicitly_ovarian_cases"]
                <= row["original_cases"] <= denominator):
            raise ValueError("Ovarian counts are not nested")
        if row["explicitly_ovarian_cases_ge2_dates"] > row["original_cases_ge2_cancer_dates"]:
            raise ValueError("Ovary-specific >=2-date cases exceed original")
        published = str(original["seer_percent_as_published"]).strip()
        bounded = published.startswith("<")
        seer_value = float(published.lstrip("<").strip())
        original_percent = 100 * row["original_cases"] / denominator
        ovarian_percent = 100 * row["explicitly_ovarian_cases"] / denominator
        out.append({
            "reference_date": reference,
            "sex_at_birth": "Female",
            **row,
            "fixed_primary_denominator": denominator,
            "original_prevalence_percent": original_percent,
            "explicitly_ovarian_prevalence_percent": ovarian_percent,
            "explicitly_ovarian_ge2_dates_prevalence_percent":
                100 * row["explicitly_ovarian_cases_ge2_dates"] / denominator,
            "seer_percent_as_published": published,
            "seer_value_is_upper_bound": bounded,
            "explicitly_ovarian_to_seer_ratio_approximate":
                ovarian_percent / seer_value if not bounded and seer_value > 0 else None,
            "difference_from_original_percentage_points": ovarian_percent - original_percent,
        })
    return out


def _read(var):
    with external(var).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main():
    import pyarrow.parquet as pq
    rows = scope_comparison(pq.read_table(external("OVARY_OUTPUT")).to_pylist(),
                            _read("SEER_COMPARISONS"), _read("CANCER_DATE_SENSITIVITY"),
                            env("REFERENCE_DATE"))
    with external("OVARY_COMPARISON", True).open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
