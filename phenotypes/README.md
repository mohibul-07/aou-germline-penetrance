# Cancer phenotypes (OMOP concept-based)

Primary definition for SEER validation and penetrance (phecode work is paused).

Source mapping: `Final_Cancer_Groups_OMOP_AoU.xlsx` (Rita Lu, Huang Lab). **Not committed** — ask Rita before
publishing. Columns: `Group`, `Name of Condition`, `OMOP Concept ID`, `Source Code`.

| Our cancer | `Group` value(s) | Notes |
|---|---|---|
| Breast | `Breast` | |
| Prostate | `Prostate` | |
| Colorectal | `Colorectum` | not "Colorectal" |
| Lung | `Lung` | |
| Kidney | `Kidney` | check renal pelvis vs SEER "Kidney and Renal Pelvis" |
| Ovarian | `Ovary` | |
| Pancreatic | `Pancreas` | |
| Stomach | `Stomach` | |
| Melanoma | `Skin`, `Skin ` (trailing space), `Skin/Mucosa` | keep only names containing "melanoma" (drops BCC, SCC, Kaposi) |

The executed selection is recovered in `analysis/seer/00_rita_mapping.py`: group labels are stripped of surrounding spaces, and melanoma means `Skin` or `Skin/Mucosa` rows whose name contains "melanoma".
`omop_cancer_cases.load_concepts` is the older export reconstruction; it gives the same concept sets for the restored workbook's labels, but the recovered module is the one to use.

Rules:
- Case = ≥1 dated occurrence in `condition_occurrence.condition_concept_id` before the reference date (≥2 distinct cancer dates = separate sensitivity).
- Multi-primary participants count in every cancer they have.
- Retired concepts: `concept_audit.py` holds the recovered vocabulary and replacement audits. The patient-level replacement impact query was only dry-run historically and is refused by default. No automatic replacement or descendant expansion is applied.

The SEER-branch cells were recovered from the Codex session; see `analysis/seer/README.md`.
Byte-identical cells are still unavailable for the other phenotype exports. See `docs/RECOVERY_GAPS.md` and `docs/INPUTS.md`. Phecode, survey and FH code are included separately; the phecode branch remains paused.
