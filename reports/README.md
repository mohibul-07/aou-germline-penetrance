# Report code only

`build_pan_cancer_report.py` and `pan_cancer_template.py` retain the original builder's layout and JavaScript/SVG charts. All static body text was moved to sequential external `__TEXT_n__` slots to avoid embedding results. The original report-data JSON and October HTML fragment were not copied. Without those external inputs, exact report reconstruction is intentionally incomplete.

Input slots correspond to each nonblank DOM text node before the report-data script in the original build_report.py, in order; `__OCT7__` is separate. Restore the original narrative inside Workbench or an approved environment and build a slot→plain-text JSON. Source schema and original artifact are required; do not fill unknown values from memory. New results do not belong in source code.

Run `python -m reports.build_pan_cancer_report` after sourcing config. This writes an internal report only. Review counts, narrative, complements, cross-table margins and fragments before sharing. `disclosure.py` provides a basic inclusive small-cell check, not disclosure clearance. No generated report or chart is bundled.

## SEER report (recovered October 21-22 builder)

`build_seer_report.py` and `seer_template.py` are the final Mac builder from the Codex session (msg 3394), with the same layout, charts, filters and checks.
Result sentences and observed numbers were moved to named `__T_*__` slots filled from the external `REPORT_SEER_TEXT` file. The review data and the figure stay external too.
With the historical inputs, the rendered page is byte-identical to `seer_validation_session_2026-10-21.html` (checked locally November 9, 2026; inputs not copied).
Run `python -m reports.build_seer_report` after sourcing config.
The superseded first October 21 builder and the separate October 22 review draft were not exported.
