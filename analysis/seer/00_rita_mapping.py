"""Freeze Rita Lu's original OMOP cancer mapping - RECOVERED (October 21, 2026).

Purpose: turn the restored workbook into the nine-cancer concept list used by
every SEER step, without changing any concept.

Provenance: Codex cells msg 2439 (workbook inspection, 15:32Z) and msg 2451
(mapping freeze, 15:33Z). Selection logic, review regex, integer checks and
output columns are unchanged.

Inputs: RITA_WORKBOOK (Final_Cancer_Groups_OMOP_AoU.xlsx, sheet "Sheet2",
columns Group, Name of Condition, OMOP Concept ID, Source Code). The workbook
is Huang Lab third-party material and is never copied into this repository.
Outputs (outside repo): CANCER_MAPPING CSV
(cancer, concept_id, workbook_group, condition_name, source_code,
workbook_row, name_review_flag, skin_mucosa_group_flag) and MAPPING_METADATA.

Decisions:
- Group labels are stripped of surrounding spaces before matching.
- Breast, Prostate, Colorectum, Lung, Kidney, Ovary, Pancreas, Stomach map
  one-to-one. Melanoma = rows in Skin or Skin/Mucosa whose name contains
  "melanoma" (case-insensitive).
- Kidney is the Kidney group only; the separate Renal Pelvis group is not added.
- Concept IDs must be positive integers; duplicate rows are kept in the CSV but
  matching uses unique (cancer, concept_id) pairs; no concept may belong to two
  cancers.
- Names matching the review pattern (history, in situ, secondary, metastasis,
  mucosa, renal pelvis, appendix, uncertain, benign) are FLAGGED for review,
  never removed. No descendants or replacements are added.

Repairs during recovery: historical asserts of exact concept totals are moved
to metadata so private mapping sizes are not hard-coded; nothing is printed.
"""
import csv
import re
from collections import Counter, defaultdict
from decimal import Decimal

from workflow.runtime import external, write_json

GROUP_MAP = {
    "Breast": "breast",
    "Prostate": "prostate",
    "Colorectum": "colorectal",
    "Lung": "lung",
    "Kidney": "kidney",
    "Ovary": "ovarian",
    "Pancreas": "pancreatic",
    "Stomach": "stomach",
}
REVIEW_PATTERN = re.compile(
    r"history|in[\s-]+situ|secondary|metasta|mucosa|"
    r"renal pelvis|appendi|uncertain|benign",
    re.IGNORECASE,
)
COLUMNS = ["Group", "Name of Condition", "OMOP Concept ID", "Source Code"]


def select_rows(rows):
    """rows: iterable of (sheet_row_number, {column: value}). Pure function."""
    mapping_rows = []
    for sheet_row, values in rows:
        original_group = str(values["Group"] or "")
        group = original_group.strip()
        name = str(values["Name of Condition"] or "")
        cancer = GROUP_MAP.get(group)
        if group in {"Skin", "Skin/Mucosa"} and "melanoma" in name.lower():
            cancer = "melanoma"
        if cancer is None:
            continue
        raw_id = values["OMOP Concept ID"]
        if raw_id is None:
            raise ValueError(f"Missing concept ID at workbook row {sheet_row}")
        numeric_id = Decimal(str(raw_id).strip())
        if not (numeric_id.is_finite() and numeric_id == numeric_id.to_integral_value()):
            raise ValueError(f"Non-integer concept ID at workbook row {sheet_row}")
        concept_id = int(numeric_id)
        if concept_id <= 0:
            raise ValueError(f"Non-positive concept ID at workbook row {sheet_row}")
        mapping_rows.append({
            "cancer": cancer,
            "concept_id": concept_id,
            "workbook_group": original_group,
            "condition_name": name,
            "source_code": str(values["Source Code"] or ""),
            "workbook_row": sheet_row,
            "name_review_flag": bool(REVIEW_PATTERN.search(name)),
            "skin_mucosa_group_flag": group == "Skin/Mucosa",
        })
    return mapping_rows


def audit(mapping_rows):
    ids_by_cancer, cancers_by_id = defaultdict(set), defaultdict(set)
    for row in mapping_rows:
        ids_by_cancer[row["cancer"]].add(row["concept_id"])
        cancers_by_id[row["concept_id"]].add(row["cancer"])
    if len(ids_by_cancer) != 9:
        raise ValueError("Expected nine cancer groups")
    cross_group = {str(k): sorted(v) for k, v in cancers_by_id.items() if len(v) > 1}
    if cross_group:
        raise ValueError("Concepts assigned to multiple cancers need review")
    flagged = {(r["cancer"], r["concept_id"]) for r in mapping_rows
               if r["name_review_flag"] or r["skin_mucosa_group_flag"]}
    return {
        "workbook_rows_by_cancer": dict(Counter(r["cancer"] for r in mapping_rows)),
        "unique_concepts_by_cancer": {c: len(v) for c, v in ids_by_cancer.items()},
        "unique_concepts_total": len(cancers_by_id),
        "cross_group_concepts": cross_group,
        "flagged_cancer_concept_pairs": len(flagged),
    }


def read_workbook():
    from openpyxl import load_workbook
    book = load_workbook(external("RITA_WORKBOOK"), read_only=True, data_only=True)
    try:
        iterator = book["Sheet2"].iter_rows(values_only=True)
        header = next(iterator)
        indices = {name: header.index(name) for name in COLUMNS}
        return [(n, {k: v[i] for k, i in indices.items()})
                for n, v in enumerate(iterator, start=2)]
    finally:
        book.close()


def main():
    mapping_rows = select_rows(read_workbook())
    summary = audit(mapping_rows)
    with external("CANCER_MAPPING", True).open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(mapping_rows[0]))
        writer.writeheader()
        writer.writerows(mapping_rows)
    write_json("MAPPING_METADATA", {
        **summary,
        "primary_coverage": "At least one dated condition_occurrence of any diagnosis",
        "sensitivity_coverage": "At least two distinct condition dates",
        "case_rule": "At least one occurrence of an explicitly listed concept",
        "descendants_added": False,
        "replacements_added": False,
        "kidney_definition": "Kidney group only; separate Renal Pelvis group not added",
        "mapping_status": "Original explicit mapping frozen as baseline; review flags pending",
    })


if __name__ == "__main__":
    main()
