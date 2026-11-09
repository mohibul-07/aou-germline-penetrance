"""Parse SEER*Explorer complete-prevalence CSV exports - RECOVERED (Oct 21-22, 2026).

Purpose: read the public SEER exports exactly as published, without changing
rounded values or inventing denominators.

Provenance: per-site cells msg 2713 (breast inspection), 2735 (breast), 2765
(prostate), 2895/2905 (colorectal), 3002 (lung), 3022 (melanoma), 3074
(kidney), 3094 (ovary), 3116 (pancreas), 3137 (stomach). The historical cells
repeated one parsing template per site; the checks here are the union of those
cells, applied to every site. Where cells differed:
- breast/prostate cells did not check the completeness-index footnote (it was
  present in the files; msg 2720 shows it). It is now required for all sites;
- breast, prostate, colorectal and lung cells REJECTED '<' bounds, and later
  cells preserved them as upper bounds. That per-site behavior is kept with
  `bounds_allowed`;
- the site title was checked as `[title] in rows` for early sites and as the
  first cell for later ones; the first-cell form is used for all sites.

Inputs: file path plus one SEER_REFERENCES entry. Outputs: in-memory rows.
Public reference metadata only. No SEER values are stored in this repository.

Reference provenance recovered from the exports' own footnotes (msg 2720/2902):
U.S. prevalence on January 1, 2023, estimated from 2023 prevalence
proportions in the SEER 12 Areas and the average of 2022 and 2023 Census
population estimates; first invasive tumor per site diagnosed 1992-2022 (31
years); older cases estimated with the completeness-index method. The printed
breast and colorectal footers say "Created by ... SEER*Explorer on Wed Oct 21
2026"; prostate was downloaded October 21 and the other sites October 22, 2026
(session timeline; their footers were not printed). The underlying SEER data
release/submission is not named in the exports and remains UNKNOWN.
Percentages are rounded to one decimal place.
"""
import csv
import re
from decimal import Decimal

BANDS = {"Ages 40-64": "40–64", "Ages 65-74": "65–74", "Ages 75+": "75+"}
SITE_SCOPE_STATUS = {
    "kidney": "Kidney versus Kidney and Renal Pelvis: mismatch",
    "melanoma": "Melanoma site/behavior review pending",
}
DEFAULT_SCOPE_STATUS = "Baseline comparison; detailed phenotype review pending"

# cancer, SEER site title (first cell), sexes, filename stem, historical comparison
# filename, bounds allowed. Filenames follow the historical layout:
# {stem}_{sex}_complete_prevalence_2023.csv in SEER_REFERENCE_DIR.
SEER_REFERENCES = [
    ("breast", "Breast", ["Female"], "seer_breast", "seer_breast_female_comparison_2023.csv", False),
    ("prostate", "Prostate", ["Male"], "seer_prostate", "seer_prostate_male_comparison_2023.csv", False),
    ("colorectal", "Colon and Rectum (including Appendix)", ["Female", "Male"],
     "seer_colorectal_including_appendix", "seer_colorectal_including_appendix_comparison_2023.csv", False),
    ("lung", "Lung and Bronchus", ["Female", "Male"], "seer_lung_bronchus",
     "seer_lung_bronchus_comparison_2023.csv", False),
    ("melanoma", "Melanoma of the Skin", ["Female", "Male"], "seer_melanoma_skin",
     "seer_melanoma_skin_comparison_2023.csv", True),
    ("kidney", "Kidney and Renal Pelvis", ["Female", "Male"], "seer_kidney_renal_pelvis",
     "seer_kidney_renal_pelvis_provisional_comparison_2023.csv", True),
    ("ovarian", "Ovary", ["Female"], "seer_ovarian", "seer_ovarian_female_comparison_2023.csv", True),
    ("pancreatic", "Pancreas", ["Female", "Male"], "seer_pancreatic",
     "seer_pancreatic_comparison_2023.csv", True),
    ("stomach", "Stomach", ["Female", "Male"], "seer_stomach", "seer_stomach_comparison_2023.csv", True),
]


def reference_filename(stem, sex):
    return f"{stem}_{sex.lower()}_complete_prevalence_2023.csv"


def read_reference(path, title, sex, reference_label="January 1, 2023", bounds_allowed=True):
    with open(path, encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))
    if not rows or not rows[0] or rows[0][0].strip().casefold() != title.casefold():
        raise ValueError("SEER site mismatch")
    if not any(row and reference_label in row[0] for row in rows):
        raise ValueError("SEER reference date mismatch")
    if not any(row and "Age at Prevalence" in row[0] and re.search(rf"\b{sex}\b", row[0])
               for row in rows):
        raise ValueError("SEER sex mismatch")
    if not any(row and "completeness index" in row[0].lower() for row in rows):
        raise ValueError("Complete-prevalence footnote missing; review the export")
    values = {}
    for row in rows:
        if row and row[0] in BANDS:
            band = BANDS[row[0]]
            if band in values:
                raise ValueError("Duplicate SEER age band")
            published = row[2].strip()
            bounded = published.startswith("<")
            if bounded and not bounds_allowed:
                raise ValueError(f"{sex}, {band}: {published} is a bound; historical cell rejected bounds")
            value = float(Decimal(published[1:].strip() if bounded else published))
            if not 0 <= value <= 100:
                raise ValueError("SEER percentage out of range")
            values[band] = dict(age_band=band, seer_percent_as_published=published,
                                seer_percent=value, seer_value_is_upper_bound=bounded)
    if set(values) != set(BANDS.values()):
        raise ValueError("Expected the three matched age bands")
    return [values[b] for b in BANDS.values()]
