"""Synthetic checks of the recovered SEER code: invented counts and files only."""
import importlib
import json

import pytest

from analysis.seer import sql
from analysis.seer.reference import SEER_REFERENCES, read_reference

mod = importlib.import_module


def seer_csv(tmp_path, title='Stomach', sex='Female', values=('<0.1', '0.2', '0.3'), footnote=True):
    lines = [title, '"People Alive with Cancer (U.S. Prevalence) on January 1, 2023"',
             f'"By Age at Prevalence, {sex}"', '', 'Age at Prevalence,Number,Percent',
             'Ages <40,"1,000",<0.1']
    lines += [f'Ages {b},"2,000",{v}' for b, v in zip(['40-64', '65-74', '75+'], values)]
    if footnote:
        lines.append('-Cases diagnosed more than 31 years ago were estimated using the completeness index method.')
    p = tmp_path / f'{title}_{sex}.csv'
    p.write_text('\n'.join(lines) + '\n')
    return p


def test_sql_matches_recorded_rules():
    q2025 = sql.prevalence_v9_cutoff('synthetic.dataset')
    q2023 = sql.prevalence_seer_aligned('synthetic.dataset')
    assert 'co.condition_start_date <= @reference_date' in q2025 and "'40–49'" in q2025
    assert 'co.condition_start_date < @reference_date' in q2023 and "'40–64'" in q2023 and "'40–49'" not in q2023
    for q in [q2023, sql.cancer_date_sensitivity('d.s'), sql.ovarian_scope('d.s')]:
        assert 'primary_death_record = TRUE' in q and 'concept_ancestor' not in q
    assert "AND (h.cancer != 'prostate' OR d.sex_at_birth = 'Male')" in sql.cancer_date_sensitivity('d.s')


def test_parser_sex_word_boundary_and_bounds(tmp_path):
    female = seer_csv(tmp_path)
    rows = read_reference(female, 'Stomach', 'Female')
    assert rows[0]['seer_value_is_upper_bound'] and rows[0]['seer_percent'] == .1
    with pytest.raises(ValueError):  # "Male" must not match "Female"
        read_reference(female, 'Stomach', 'Male')
    with pytest.raises(ValueError):  # early sites rejected bounds historically
        read_reference(female, 'Stomach', 'Female', bounds_allowed=False)
    with pytest.raises(ValueError):
        read_reference(seer_csv(tmp_path, footnote=False), 'Stomach', 'Female')


def test_reference_table_sex_restrictions():
    sexes = {r[0]: r[2] for r in SEER_REFERENCES}
    assert sexes['breast'] == ['Female'] and sexes['ovarian'] == ['Female'] and sexes['prostate'] == ['Male']
    assert len(SEER_REFERENCES) == 9 and sum(len(r[2]) for r in SEER_REFERENCES) == 15


def aou_rows():
    rows = []
    for sex in ['Female', 'Male']:
        for band in ['20–39', '40–64', '65–74', '75+']:
            r = dict(demographic_status='adult_without_recorded_death_by_reference', sex_at_birth=sex,
                     age_band=band, wgs_participants=1000, primary_coverage_denominator=900,
                     sensitivity_coverage_denominator=800)
            for c in sql.CANCERS:
                r[c], r[c + '_ge2_dates'] = 90, 60
            rows.append(r)
    return rows


def test_compare_and_coverage_sensitivity(tmp_path):
    compare = mod('analysis.seer.02_compare').compare
    refs = {('stomach', s): read_reference(seer_csv(tmp_path, sex=s), 'Stomach', s) for s in ['Female', 'Male']}
    refs[('breast', 'Female')] = read_reference(seer_csv(tmp_path, 'Breast', values=('2.0', '4.0', '8.0')), 'Breast', 'Female')
    out = compare(aou_rows(), refs, '2023-01-01')
    assert len(out) == (2 * 3 + 3) * 2
    assert all(r['age_band'] != '20–39' for r in out)
    bounded = [r for r in out if r['seer_value_is_upper_bound']]
    assert bounded and all(r['aou_to_seer_ratio_approximate'] is None for r in bounded)
    cov = mod('analysis.seer.05_coverage_sensitivity').coverage_sensitivity(out)
    assert len(cov) == 9 and all(r['ge2_dates_denominator'] == 800 for r in cov)


def test_cancer_date_requires_exact_baseline():
    m = mod('analysis.seer.03_cancer_date_sensitivity')
    base = [dict(cancer='lung', sex_at_birth='Male', age_band='40–64', coverage_rule='ge1_dated_condition',
                 aou_cases='90', aou_denominator='900', seer_percent_as_published='0.5',
                 site_scope_status='x')]
    counts = [dict(cancer='lung', sex_at_birth='Male', age_band='40–64', cases_ge1_cancer_date=90,
                   cases_ge2_cancer_dates=60, cases_exactly1_cancer_date=30)]
    out = m.comparisons(counts, base, '2023-01-01')
    assert out[0]['fixed_primary_denominator'] == 900 and out[0]['case_retention_percent'] == pytest.approx(200 / 3)
    counts[0]['cases_ge1_cancer_date'] = 91
    with pytest.raises(ValueError):
        m.comparisons(counts, base, '2023-01-01')
    summary = m.summary([{k: ('' if v is None else v) for k, v in out[0].items()}])
    assert summary[0]['strata_with_point_ratios'] == 1


def test_ovarian_classes_must_partition_original():
    classes = mod('analysis.seer.04_ovarian_scope').scope_classes
    rows = [dict(concept_id='1', scope_class='ovary'), dict(concept_id='2', scope_class='fallopian_cancer'),
            dict(concept_id='3', scope_class='adnexal'), dict(concept_id='4', scope_class='lesion')]
    assert classes(rows, [1, 2, 3, 4])['adnexal'] == [3]
    with pytest.raises(ValueError):
        classes(rows, [1, 2, 3, 4, 5])
    with pytest.raises(ValueError):
        classes(rows + [dict(concept_id='5', scope_class='lesion')], [1, 2, 3, 4, 5])


def test_point_masking_is_inclusive_1_to_20():
    plot_safe = mod('analysis.seer.06_plot').plot_safe
    assert plot_safe(dict(aou_cases=21, aou_denominator=500))
    assert plot_safe(dict(aou_cases=0, aou_denominator=500))
    assert not plot_safe(dict(aou_cases=20, aou_denominator=500))
    assert not plot_safe(dict(aou_cases=490, aou_denominator=500))


def test_mapping_selection_rules():
    m = mod('analysis.seer.00_rita_mapping')
    rows = m.select_rows([
        (2, {'Group': 'Breast ', 'Name of Condition': 'Malignant neoplasm', 'OMOP Concept ID': 11.0, 'Source Code': 'C50'}),
        (3, {'Group': 'Skin/Mucosa', 'Name of Condition': 'Melanoma of mucosa', 'OMOP Concept ID': '12', 'Source Code': ''}),
        (4, {'Group': 'Skin', 'Name of Condition': 'Basal cell carcinoma', 'OMOP Concept ID': 13, 'Source Code': ''}),
        (5, {'Group': 'Renal Pelvis', 'Name of Condition': 'Malignant neoplasm', 'OMOP Concept ID': 14, 'Source Code': ''}),
    ])
    assert [(r['cancer'], r['concept_id']) for r in rows] == [('breast', 11), ('melanoma', 12)]
    assert rows[1]['name_review_flag'] and rows[1]['skin_mucosa_group_flag']
    with pytest.raises(ValueError):
        m.select_rows([(2, {'Group': 'Lung', 'Name of Condition': 'x', 'OMOP Concept ID': 1.5, 'Source Code': ''})])


def test_unrun_impact_audit_is_refused(monkeypatch):
    monkeypatch.delenv('ALLOW_UNRUN_IMPACT_AUDIT', raising=False)
    with pytest.raises(RuntimeError):
        mod('phenotypes.concept_audit').impact()
    pairs = [('prostate', 5)]
    rel = [dict(original_concept_id=5, target_concept_id=9, relationship_invalid_reason=None,
                target_invalid_reason=None, target_standard_status='S', target_domain='Condition')]
    got = mod('phenotypes.concept_audit').impact_mapping(pairs, rel)
    assert got[-1] == {'cancer': 'prostate', 'concept_id': 9, 'mapping_set': 'replacement_candidate'}


def test_seer_report_renders_without_leftover_slots():
    render = mod('reports.build_seer_report').render
    rows = [dict(cancer='Stomach', sex='Female', age='40–64', aou_percent=0.5, seer_percent='<0.1', ratio=None)] * 45
    review = dict(primary_comparisons=rows,
                  cancer_date_retention_percent={f'c{i}': 50.0 for i in range(9)},
                  coverage_sensitivity_change_percentage_points={f'c{i}': [0.0, 0.1] for i in range(9)},
                  cancer_date_sensitivity_change_percentage_points={f'c{i}': [-0.2, -0.1] for i in range(9)},
                  ovarian_scope_sensitivity=[dict(age='40–64', original_percent=.5, ovary_specific_percent=.4,
                                                  seer_percent=.2, ratio=2.0)])
    text = {k: 'synthetic' for k in ['conclusion', 'coverage_result', 'coverage_note', 'cancer_date_result',
                                     'two_date_note', 'ovarian_result', 'note_2025']}
    text.update(roster_total=1000, unique_concepts=10, retired_concepts=1, ovarian_scale_max=1.0,
                coverage_bars=[['Roster', 1000], ['Covered', 900]])
    page = render(review, text, b'not-a-real-png', 10, 10)
    assert '__T_' not in page and '__IMAGE__' not in page and json.dumps('synthetic') .strip('"') in page
