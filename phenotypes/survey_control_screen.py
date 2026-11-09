"""Reconstruct target-specific personal-survey review of candidate controls.
Inputs: CANDIDATE_CONTROLS Parquet person_id,cancer,candidate_control,eligible_case;
PERSONAL_SURVEY Parquet person_id,site (positive Self reports only).
Output: SCREENED_CONTROLS Parquet of original flags plus provisional review flags.
Decisions: survey reports do not create cases; other cancer sites are allowed.
Melanoma uses skin_unspecified only as exclusion sensitivity, never proof of melanoma.
"""
from workflow.runtime import external

def main():
    import pandas as pd
    from pyarrow import Table
    import pyarrow.parquet as pq
    personal=pd.read_parquet(external('PERSONAL_SURVEY'),columns=['person_id','site'])
    sites={site:set(g.person_id) for site,g in personal.groupby('site')}
    writer=None
    try:
        for b in pq.ParquetFile(external('CANDIDATE_CONTROLS')).iter_batches():
            d=b.to_pandas()
            for c in ['candidate_control','eligible_case']:
                if d[c].isna().any() or not pd.api.types.is_bool_dtype(d[c]):
                    raise ValueError('Eligibility flags must be non-null booleans')
            if (d.candidate_control & d.eligible_case).any():
                raise ValueError('Case/control overlap')
            report=d.apply(lambda r:r.person_id in sites.get('skin_unspecified' if r.cancer=='melanoma' else r.cancer,set()),axis=1)
            d['personal_target_review']=d.candidate_control & report
            d['provisional_screened_control']=d.candidate_control & ~report
            d['screen_type']=d.cancer.map(lambda c:'skin_report_exclusion_sensitivity' if c=='melanoma' else 'provisional_target_screen')
            t=Table.from_pandas(d,preserve_index=False)
            if writer is None: writer=pq.ParquetWriter(external('SCREENED_CONTROLS',True),t.schema)
            writer.write_table(t)
    finally:
        if writer: writer.close()

if __name__ == '__main__':
    main()
