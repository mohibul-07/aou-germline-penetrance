"""Reconstruct provisional full-roster family-history grouping from saved signals.
Inputs: WGS_ROSTER; FH_SIGNALS Parquet (person_id and non-null boolean fields
relative_history, clinical_positive, reported_none, additional_review).
Outputs: FH_GROUPS full-roster Parquet, retaining every evidence flag.
Decision precedence: positive evidence > additional review > explicit None > unknown.
None without positive/review evidence is not proven absence of familial risk.
Exact raw-to-review flag mapping is not recoverable: supply the approved saved
signal table after adapting column names; do not infer those flags from text/zero.
"""
import numpy as np
from workflow.runtime import external

FIELDS=['relative_history','clinical_positive','reported_none','additional_review']

def assign_groups(relative, clinical, none, review):
    positive=np.asarray(relative,dtype=bool)|np.asarray(clinical,dtype=bool)
    return np.select([positive,np.asarray(review,dtype=bool),np.asarray(none,dtype=bool)],
        ['history_evidence_present','additional_review_needed_without_positive_signal',
         'reported_none_without_additional_review_signals'],default='unknown_history')

def main():
    import pyarrow as pa
    import pyarrow.parquet as pq
    ids=np.asarray(pq.read_table(external('WGS_ROSTER'),columns=['person_id'])['person_id'])
    if len(ids)!=len(np.unique(ids)):
        raise ValueError('Duplicate roster identifiers')
    order=np.argsort(ids); ids=ids[order]
    flags=np.zeros((len(ids),len(FIELDS)),dtype=bool);seen=np.zeros(len(ids),dtype=bool)
    for batch in pq.ParquetFile(external('FH_SIGNALS')).iter_batches(columns=['person_id']+FIELDS):
        b=batch.to_pydict(); keys=np.asarray(b['person_id']); idx=np.searchsorted(ids,keys)
        if np.any(idx>=len(ids)) or np.any(ids[idx]!=keys) or len(idx)!=len(np.unique(idx)) or np.any(seen[idx]):
            raise ValueError('Signals must be unique and roster-matched')
        for j,f in enumerate(FIELDS):
            if any(type(v) is not bool for v in b[f]):
                raise ValueError('Signal columns must be explicit non-null booleans')
            flags[idx,j]=b[f]
        seen[idx]=True
    # Require full approved signals: a missing processing row is not unknown evidence.
    if not seen.all():
        raise ValueError('Signal table must cover the full roster')
    out={'person_id':ids,**{f:flags[:,j] for j,f in enumerate(FIELDS)}}
    out['family_history_group']=assign_groups(*flags.T)
    pq.write_table(pa.table(out),external('FH_GROUPS',True))

if __name__ == '__main__':
    main()
