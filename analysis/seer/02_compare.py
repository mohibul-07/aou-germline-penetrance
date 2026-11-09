"""All nine AoU-SEER comparisons - RECOVERED (October 21-22, 2026).

Purpose: compare saved 2023 AoU aggregates with SEER complete prevalence in
the three matched age bands, for the primary coverage rule and the >=2
any-diagnosis-date coverage sensitivity. No BigQuery scan.

Provenance: per-site cells msg 2735 (breast), 2765 (prostate), 2905
(colorectal), 3002 (lung), 3022 (melanoma), 3074 (kidney), 3094 (ovary),
3116 (pancreas), 3137 (stomach), then consolidation msg 3149. Historically each
site wrote its own CSV and msg 3149 merged them. Here the per-site template is
applied in a loop and the consolidated table is written directly, with the same
columns, row checks, labels and `source_file` names as the msg 3149 output
(seer_all_nine_comparisons_2023.csv). Per-site intermediate CSVs are not
regenerated; their columns (e.g. difference_percentage_points) were not
carried into the consolidated table historically either.

Inputs: PREVALENCE_OUTPUT (2023 aggregate from 01_prevalence_counts seer2023);
SEER exports in SEER_REFERENCE_DIR named as in reference.SEER_REFERENCES.
Output (outside repo): SEER_COMPARISONS CSV, 90 rows when all nine sites exist.

Decisions:
- Eligible strata: adult_without_recorded_death_by_reference, Female/Male,
  bands 40-64, 65-74, 75+. AoU 20-39 is never compared with SEER <40.
- Breast and ovary Female only; prostate Male only; other sites both sexes.
- Ratio only when SEER is a point value > 0; '<' values stay upper bounds.
- Colorectal reference includes appendix (matches Rita's scope). Kidney is a
  flagged site mismatch (SEER adds renal pelvis). Melanoma scope review pending.
- Rounded SEER percentages make every ratio approximate.
"""
import csv

from analysis.seer.common import ELIGIBLE_STATUS, MATCHED_BANDS
from analysis.seer.reference import (DEFAULT_SCOPE_STATUS, SEER_REFERENCES, SITE_SCOPE_STATUS,
                                     read_reference, reference_filename)
from workflow.runtime import env, external

COVERAGES = [("ge1_dated_condition", "primary_coverage_denominator", ""),
             ("ge2_condition_dates", "sensitivity_coverage_denominator", "_ge2_dates")]


def eligible_lookup(aou_rows):
    lookup = {}
    for row in aou_rows:
        if row["demographic_status"] == ELIGIBLE_STATUS and row["sex_at_birth"] in {"Female", "Male"}:
            key = (row["sex_at_birth"], row["age_band"])
            if key in lookup:
                raise ValueError("Duplicate eligible stratum")
            lookup[key] = row
    return lookup


def compare(aou_rows, references, reference_date):
    """references: {(cancer, sex): parsed SEER rows}. Pure function."""
    lookup = eligible_lookup(aou_rows)
    combined = []
    for cancer, _title, sexes, _stem, source_file, bounds_allowed in SEER_REFERENCES:
        for sex in sexes:
            if (cancer, sex) not in references:
                continue
            seer = {r["age_band"]: r for r in references[(cancer, sex)]}
            for band in MATCHED_BANDS:
                aou = lookup[(sex, band)]
                s = seer[band]
                if not bounds_allowed and not s["seer_percent"] > 0:
                    raise ValueError("Historical cell required a positive SEER percentage")
                for coverage, denominator_field, suffix in COVERAGES:
                    denominator = int(aou[denominator_field])
                    cases = int(aou[cancer + suffix])
                    if not (0 <= cases <= denominator and denominator > 0):
                        raise ValueError("Invalid numerator/denominator")
                    percent = 100 * cases / denominator
                    bounded = s["seer_value_is_upper_bound"]
                    combined.append({
                        "reference_date": reference_date,
                        "cancer": cancer,
                        "sex_at_birth": sex,
                        "age_band": band,
                        "coverage_rule": coverage,
                        "aou_cases": cases,
                        "aou_denominator": denominator,
                        "aou_percent": percent,
                        "seer_percent_as_published": s["seer_percent_as_published"],
                        "seer_value_is_upper_bound": bounded,
                        "aou_to_seer_ratio_approximate":
                            percent / s["seer_percent"] if not bounded and s["seer_percent"] > 0 else None,
                        "site_scope_status": SITE_SCOPE_STATUS.get(cancer, DEFAULT_SCOPE_STATUS),
                        "source_file": source_file,
                    })
    keys = [(r["cancer"], r["sex_at_birth"], r["age_band"], r["coverage_rule"]) for r in combined]
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate comparison stratum")
    return combined


def main():
    import pyarrow.parquet as pq
    aou_rows = pq.read_table(external("PREVALENCE_OUTPUT")).to_pylist()
    directory = external("SEER_REFERENCE_DIR")
    references = {}
    for cancer, title, sexes, stem, _source, bounds_allowed in SEER_REFERENCES:
        for sex in sexes:
            path = directory / reference_filename(stem, sex)
            if not path.is_file():
                raise FileNotFoundError(f"Missing SEER export: {path.name}")
            references[(cancer, sex)] = read_reference(path, title, sex, env("SEER_REFERENCE_LABEL"),
                                                       bounds_allowed)
    combined = compare(aou_rows, references, env("REFERENCE_DATE"))
    if len(combined) != 90:
        raise ValueError("Expected 90 rows: 45 strata x 2 coverage rules")
    with external("SEER_COMPARISONS", True).open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(combined[0]))
        writer.writeheader()
        writer.writerows(combined)


if __name__ == "__main__":
    main()
