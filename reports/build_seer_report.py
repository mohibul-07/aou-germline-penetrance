"""Build the cumulative October 21-22 SEER report - RECOVERED builder.

Purpose: render the interactive HTML review report (nine-cancer figure, two
sensitivity checks, ovarian scope, filterable primary comparisons, methods).

Provenance: /Users/mohibul/Agents/research_report/build_seer_report_2026-10-21.py,
final version written by the Codex session at msg 3394 (2026-10-22T14:50Z)
and run on the Mac, not in the Workbench. Chart/table generation, checks,
escaping and token substitution are unchanged. Superseded builders from the same
sessions (first October 21 version, msg 2952; separate October 22 review draft,
msg 3342) were not exported; see docs/RECOVERY_GAPS.md.

Inputs (all external, reviewed aggregate payloads; none are bundled):
- REPORT_SEER_REVIEW_DATA: JSON with primary_comparisons (45 rows: cancer, sex,
  age, aou_percent, seer_percent, ratio), cancer_date_retention_percent,
  coverage_sensitivity_change_percentage_points,
  cancer_date_sensitivity_change_percentage_points ({cancer: [min, max]}),
  ovarian_scope_sensitivity (rows: age, original_percent,
  ovary_specific_percent, seer_percent, ratio). Historical file:
  seer_review_data_2026-10-22.json.
- REPORT_SEER_TEXT: JSON with the result slots removed from the template:
  conclusion, coverage_result, coverage_note, cancer_date_result,
  two_date_note, ovarian_result, note_2025 (reviewed HTML strings; note_2025
  is the full sentence about the separate 2025 baseline),
  roster_total, unique_concepts, retired_concepts (integers),
  ovarian_scale_max (historically 1.4) and coverage_bars ([[label, count], ...],
  first entry the roster).
- REPORT_SEER_FIGURE: the original Workbench PNG.
Output: REPORT_SEER_HTML (outside repo). Nothing is printed.

Decisions: the embedded figure is used unchanged; supporting visuals use only
reported aggregates; no per-stratum values are invented; the report contains
no participant IDs. Small-cell and dissemination review is still required
before sharing.
"""
import base64
import json
from html import escape as h

from reports.seer_template import PAGE
from workflow.runtime import external


def retention_rows(review):
    out = ''
    for cancer, value in review['cancer_date_retention_percent'].items():
        cover = review['coverage_sensitivity_change_percentage_points'][cancer]
        case = review['cancer_date_sensitivity_change_percentage_points'][cancer]
        assert 0 <= value <= 100 and 0 <= cover[0] <= cover[1] and case[0] <= case[1] <= 0
        out += f'''<tr><th scope="row">{h(cancer)}</th><td><div class="retention"><div class="retention-track"><span style="width:{value}%"></span></div><b>{value:.1f}%</b></div></td><td class="number">{case[0]:+.3f} to {case[1]:+.3f}</td><td class="number">{cover[0]:+.3f} to {cover[1]:+.3f}</td></tr>'''
    return out


def ovarian_bars(review, scale):
    out = ''
    for row in review['ovarian_scope_sensitivity']:
        series = [('Original 13 concepts', row['original_percent'], 'original'),
                  ('Ovary-specific 8', row['ovary_specific_percent'], 'scoped'),
                  ('SEER Ovary', row['seer_percent'], 'seer')]
        bars = ''.join(f'<div class="comparison-bar"><span>{h(label)}</span><div class="comparison-track"><span class="{style}" style="width:{value/scale*100:.4f}%"></span></div><b>{value:.3f}%</b></div>' for label, value, style in series)
        out += f'''<article class="ovary-panel"><h3>Age {row['age']}</h3>{bars}<p class="micro">Change from original: <b>{row['ovary_specific_percent']-row['original_percent']:+.3f} percentage points</b><br>Ovary-specific / SEER ≈ {row['ratio']:.2f}</p></article>'''
    return out


def coverage_bars(bars):
    total = bars[0][1]
    return ''.join(f'<div class="coverage-row"><span>{h(label)}</span><div class="coverage-track"><span style="width:{count/total*100:.4f}%"></span></div><b>{count:,}</b></div>' for label, count in bars)


def fallback_rows(review):
    out = ''
    for row in review['primary_comparisons']:
        scope = ('Kidney / renal-pelvis mismatch' if row['cancer'] == 'Kidney' else
                 'Site / behavior review pending' if row['cancer'] == 'Melanoma' else
                 'Original broad group; scope sensitivity above' if row['cancer'] == 'Ovarian' else '')
        badge = f'<br><span class="pill">{h(scope)}</span>' if scope else ''
        ratio = 'Bound; no point ratio' if row['ratio'] is None else f'{row["ratio"]:.2f}'
        out += f'<tr><td>{h(row["cancer"])}{badge}</td><td>{h(row["sex"])}</td><td>{h(row["age"])}</td><td class="number">{row["aou_percent"]:.3f}</td><td class="number">{h(str(row["seer_percent"]))}</td><td class="number ratio">{ratio}</td></tr>'
    return out


def render(review, text, image_bytes, width, height):
    assert len(review['primary_comparisons']) == 45
    assert len(review['cancer_date_retention_percent']) == 9
    payload = {'rows': review['primary_comparisons'], 'updated': '2026-10-22'}
    image_uri = 'data:image/png;base64,' + base64.b64encode(image_bytes).decode()
    tokens = {
        '__IMAGE__': image_uri, '__WIDTH__': str(width), '__HEIGHT__': str(height),
        '__RETENTION__': retention_rows(review),
        '__OVARY__': ovarian_bars(review, float(text['ovarian_scale_max'])),
        '__COVERAGE__': coverage_bars(text['coverage_bars']),
        '__RESULT_ROWS__': fallback_rows(review),
        '__SCALE__': f"{float(text['ovarian_scale_max']):g}",
        '__T_CONCLUSION__': text['conclusion'],
        '__T_COVERAGE_RESULT__': text['coverage_result'],
        '__T_COVERAGE_NOTE__': text['coverage_note'],
        '__T_CANCER_DATE_RESULT__': text['cancer_date_result'],
        '__T_TWO_DATE_NOTE__': text['two_date_note'],
        '__T_OVARIAN_RESULT__': text['ovarian_result'],
        '__T_2025_NOTE__': text['note_2025'],
        '__T_ROSTER__': f"{int(text['roster_total']):,}",
        '__T_CONCEPTS__': str(int(text['unique_concepts'])),
        '__T_RETIRED__': str(int(text['retired_concepts'])),
        '__JSON__': json.dumps(payload, ensure_ascii=False).replace('<', '\\u003c'),
    }
    page = PAGE
    for token, value in tokens.items():
        page = page.replace(token, value)
    assert '__IMAGE__' not in page and '__RETENTION__' not in page and '__T_' not in page
    return page


def main():
    from PIL import Image
    review = json.loads(external('REPORT_SEER_REVIEW_DATA').read_text())
    text = json.loads(external('REPORT_SEER_TEXT').read_text())
    figure = external('REPORT_SEER_FIGURE')
    with Image.open(figure) as im:
        width, height = im.size
    external('REPORT_SEER_HTML', True).write_text(
        render(review, text, figure.read_bytes(), width, height))


if __name__ == '__main__':
    main()
