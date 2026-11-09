"""Synthetic checks only: no observed keys, participant IDs, or dataset files."""
import importlib
import numpy as np
import pandas as pd
import pytest
from carriers.keys import canonical_key,vat_to_vcf
from carriers.reconcile_variants import reconcile
from phenotypes.family_history import assign_groups
from phenotypes.phecode import __name__ as unused
from reports.disclosure import safe_counts


def test_keys_do_not_double_prefix_or_drop_long_alleles():
    assert vat_to_vcf('chr2-101-A-ATTT')==('chr2',101,'A','ATTT')
    assert canonical_key('folder:any.vcf:chr2:101:A:ATTT')=='chr2:101:A:ATTT'
    with pytest.raises(ValueError): canonical_key('chr2:0:A:T')


def test_membership_uses_sources_not_saved_label():
    rows=[{'key':'chr1:101:A:T','gene':'GENE_A','group':'fastvep_only'},
          {'key':'chr1:101:A:T','gene':'GENE_A','group':'concordant'},
          {'key':'chr1:202:C:G','gene':'GENE_A','group':'concordant'},
          {'key':'chr1:303:G:T','gene':'NEIGHBOR','group':'concordant'}]
    supported,unresolved=reconcile(rows,{'GENE_A'},{'chr1:101:A:T'},{'chr1:101:A:T'})
    assert len(supported)==1 and supported[0]['group']=='concordant'
    assert len(unresolved)==1 and unresolved[0]['group']=='absent_from_both_source_lists'


def test_family_history_precedence():
    got=assign_groups([True,False,False,False],[False]*4,[True,True,True,False],[True,True,False,False])
    assert list(got)==['history_evidence_present','additional_review_needed_without_positive_signal',
        'reported_none_without_additional_review_signals','unknown_history']


def test_site_boundaries():
    f=importlib.import_module('phenotypes.phecode.02_evidence_tiers').malignant
    assert f('colorectal','ICD10CM','C18.9') and not f('colorectal','ICD10CM','C18.1')
    assert f('kidney','ICD9CM','189.0') and not f('kidney','ICD9CM','189.1')
    assert f('lung','ICD9CM','162.9') and not f('lung','ICD9CM','162.0')
    assert not f('melanoma','ICD10CM','D03.9')


def test_suppression_inclusive_and_complement():
    assert safe_counts([0,21,100])
    assert not safe_counts([20,100])
    assert not safe_counts([99,100,1])
    assert not safe_counts([float('nan')])


def test_seer_bound_and_wrong_type(tmp_path):
    from analysis.seer.reference import read_reference
    p=tmp_path/'synthetic.csv'
    p.write_text('Synthetic Site\n"January 1, 2023"\n"By Age at Prevalence, Female"\nAges 40-64,100,<0.1\nAges 65-74,200,0.2\nAges 75+,300,0.3\ncompleteness index method\n')
    rows=read_reference(p,'Synthetic Site','Female','January 1, 2023')
    assert rows[0]['seer_value_is_upper_bound'] and rows[0]['seer_percent']==.1
    with pytest.raises(ValueError): read_reference(p,'Wrong site','Female','January 1, 2023')


def test_lowercase_sex_and_callability():
    from analysis.penetrance.penetrance import penetrance_table
    cohort=pd.DataFrame({'person_id':['synthetic_a','synthetic_b','synthetic_c'],
                         'eligible':[True]*3,'sex_at_birth':['Male','Female','Female']})
    carriers=pd.DataFrame({'person_id':['synthetic_a','synthetic_b'],'vid':['synthetic_v']*2,'gene':['G']*2})
    cases=pd.DataFrame({'person_id':['synthetic_b'],'cancer':['breast']})
    variants=pd.DataFrame({'vid':['synthetic_v'],'gene':['G']})
    pairs=pd.DataFrame({'gene':['G'],'cancer':['breast']})
    callable_pairs=pd.DataFrame({'vid':['synthetic_v']*2,'person_id':['synthetic_b','synthetic_c']})
    r=penetrance_table(carriers,cohort,cases,variants,pairs,min_carriers=1,callable_pairs=callable_pairs)
    assert r.iloc[0].n_carriers==1 and r.iloc[0].noncarrier_n==1
    with pytest.raises(ValueError): penetrance_table(carriers,cohort,cases,variants,pairs,1,callable_pairs.iloc[1:])


def test_queries_use_date_and_do_not_apply_replacements():
    q=importlib.import_module('analysis.00_ehr_coverage_check').query('synthetic.dataset')
    assert 'condition_start_date' in q and 'condition_start_datetime' not in q
    q=importlib.import_module('analysis.seer.01_prevalence_counts').query('synthetic.dataset')
    assert 'co.condition_start_date < @reference_date' in q
    assert 'death_date <= @reference_date' in q and 'concept_ancestor' not in q
    assert 'primary_death_record = TRUE' in q and 'sensitivity_coverage_denominator' in q
