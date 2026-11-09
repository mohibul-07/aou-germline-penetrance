"""Nine-panel AoU versus SEER prevalence figure - RECOVERED (October 22, 2026).

Purpose: draw the historical figure seer_all_nine_prevalence_comparison_2023
(PNG/PDF) from the consolidated comparison table.

Provenance: plotting cell msg 3161 (2026-10-22T14:15Z). Layout, colors,
titles, markers, legend, footnote, masking rule, dpi and bounding box are
unchanged. The PNG Md downloaded from the Workbench is the canonical
historical figure (SHA-256 recorded in docs/MANIFEST.md); this code is how it
was drawn. Recovery changes: paths come from config, the non-interactive Agg
backend is selected, `plt.show()` and the printed masked-point count are
removed (the count goes to metadata), and the GCS copy is left to the
Workbench backup step.

Input: SEER_COMPARISONS (02_compare).
Outputs (outside repo): FIGURE_PNG, FIGURE_PDF, FIGURE_METADATA.

Decisions:
- Solid circles: AoU >=1 dated condition. Dashed: AoU >=2 dates of ANY
  diagnosis (coverage sensitivity). The figure does NOT show the >=2
  cancer-date or ovarian-scope sensitivities.
- Dotted squares: SEER complete prevalence. SEER '<' values are drawn as open
  downward triangles at the bound, never as point estimates.
- Each AoU POINT is masked if its cases, denominator or unaffected count is
  1-20 (point-level masking, as historically). The earlier export
  reconstruction masked whole series instead; that was a new rule and has been
  reverted. Masking alone is not dissemination clearance.
- Panels use their own vertical scales; no confidence intervals or
  age standardization.
"""
import csv

from workflow.runtime import external, write_json

CANCERS = ["breast", "prostate", "colorectal", "lung", "melanoma",
           "kidney", "ovarian", "pancreatic", "stomach"]
BANDS = ["40–64", "65–74", "75+"]
COLORS = {"Female": "#7b4d91", "Male": "#087f82"}
TITLES = {
    "colorectal": "Colorectal, including appendix",
    "melanoma": "Melanoma — scope review pending",
    "kidney": "Kidney — SEER also includes renal pelvis",
}


def plot_safe(row):
    cases = int(row["aou_cases"])
    denominator = int(row["aou_denominator"])
    unaffected = denominator - cases
    return not any(1 <= count <= 20 for count in [cases, denominator, unaffected])


def draw(rows):
    """Return (figure, masked_points). Pure plotting; writes nothing."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.lines import Line2D

    lookup = {}
    for row in rows:
        key = (row["cancer"], row["sex_at_birth"], row["age_band"], row["coverage_rule"])
        if key in lookup:
            raise ValueError("Duplicate stratum")
        lookup[key] = row
    masked_points = 0

    fig, axes = plt.subplots(3, 3, figsize=(16, 13))
    for ax, cancer in zip(axes.flat, CANCERS):
        for sex, color in COLORS.items():
            if (cancer, sex, BANDS[0], "ge1_dated_condition") not in lookup:
                continue
            for coverage, style, marker in [("ge1_dated_condition", "-", "o"),
                                            ("ge2_condition_dates", "--", None)]:
                values = []
                for band in BANDS:
                    row = lookup[(cancer, sex, band, coverage)]
                    if plot_safe(row):
                        values.append(float(row["aou_percent"]))
                    else:
                        values.append(np.nan)
                        masked_points += 1
                ax.plot(range(3), values, color=color, linestyle=style,
                        marker=marker, linewidth=1.7, markersize=5)
            seer_points, bounds = [], []
            for index, band in enumerate(BANDS):
                published = str(lookup[(cancer, sex, band, "ge1_dated_condition")]
                                ["seer_percent_as_published"]).strip()
                if published.startswith("<"):
                    seer_points.append(np.nan)
                    bounds.append((index, float(published[1:])))
                else:
                    seer_points.append(float(published))
            ax.plot(range(3), seer_points, color=color, linestyle=":",
                    marker="s", linewidth=1.5, markersize=5)
            for index, upper_bound in bounds:
                ax.scatter(index, upper_bound, marker="v", facecolors="none",
                           edgecolors=color, s=65, zorder=5)
                ax.annotate("<", (index, upper_bound), xytext=(7, 0),
                            textcoords="offset points", color=color, va="center")
        ax.set_title(TITLES.get(cancer, cancer.title()), fontsize=10)
        ax.set_xticks(range(3), BANDS)
        ax.set_xlabel("Age at prevalence")
        ax.set_ylabel("Prevalence (%)")
        ax.set_ylim(bottom=0)
        ax.grid(axis="y", alpha=0.2)
        ax.spines[["top", "right"]].set_visible(False)

    legend = [
        Line2D([0], [0], color=COLORS["Female"], lw=2, label="Female"),
        Line2D([0], [0], color=COLORS["Male"], lw=2, label="Male"),
        Line2D([0], [0], color="black", marker="o", label="AoU: ≥1 diagnosis date"),
        Line2D([0], [0], color="black", linestyle="--", label="AoU: ≥2 dates"),
        Line2D([0], [0], color="black", linestyle=":", marker="s",
               label="SEER complete prevalence"),
        Line2D([0], [0], color="black", marker="v", markerfacecolor="none",
               linestyle="None", label="SEER upper bound"),
    ]
    fig.suptitle("Recorded cancer prevalence in All of Us versus SEER — January 1, 2023",
                 fontsize=16, y=0.995)
    fig.legend(handles=legend, loc="upper center", bbox_to_anchor=(0.5, 0.97),
               ncol=3, frameon=False)
    fig.text(
        0.5, 0.015,
        "Original Rita OMOP definitions; retrospective v9 WGS cohort. "
        "SEER percentages rounded; no confidence intervals shown.\n"
        "Panels use different vertical scales. Kidney site mismatch and melanoma "
        "scope differences remain unresolved. Small AoU cells masked.",
        ha="center", fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.06, 1, 0.90))
    return fig, masked_points


def main():
    import matplotlib.pyplot as plt
    with external("SEER_COMPARISONS").open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 90:
        raise ValueError("Expected 90 comparison rows")
    fig, masked_points = draw(rows)
    fig.savefig(external("FIGURE_PNG", True), dpi=220, bbox_inches="tight")
    fig.savefig(external("FIGURE_PDF", True), bbox_inches="tight")
    plt.close(fig)
    write_json("FIGURE_METADATA", {
        "source": "SEER_COMPARISONS",
        "masked_aou_points": masked_points,
        "mask_rule": "Mask when cases, denominator, or unaffected count is 1–20.",
        "seer_bounds": "Shown as open downward triangles; not point estimates.",
        "dashed_lines": "At least two dates of any diagnosis: coverage sensitivity, not cancer-date sensitivity.",
        "confidence_intervals_shown": False,
        "age_standardization_performed": False,
        "phenotype_validation_complete": False,
        "external_sharing": "Requires final dissemination review; masking alone is not clearance.",
    })


if __name__ == "__main__":
    main()
