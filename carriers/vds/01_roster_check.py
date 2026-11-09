"""Reconstruct exact unique VDS sample-roster matching (columns only).
Inputs: VDS_PATH, HAIL_SAMPLE_ROSTER_GCS TSV with s header uploaded in Workbench.
Output: VDS_ROSTER_AUDIT internal JSON of match/uniqueness summaries.
Decisions: reject missing/noninteger/duplicate IDs and any set difference.
Local notebook paths are not assumed visible to Spark workers. No genotypes read.
"""
from workflow.runtime import env,write_json
from carriers.vds.common import initialize

def main():
    hl=initialize();vds=hl.vds.read_vds(env('VDS_PATH'))
    roster=hl.import_table(env('HAIL_SAMPLE_ROSTER_GCS'),types={'s':hl.tstr},key='s')
    columns=vds.variant_data.cols().select()
    n=columns.count();rn=roster.count()
    unique=columns.group_by(columns.s).aggregate(n=hl.agg.count())
    ru=roster.group_by(roster.s).aggregate(n=hl.agg.count())
    duplicates=unique.filter(unique.n>1).count()+ru.filter(ru.n>1).count()
    missing=columns.filter(hl.is_missing(columns.s)).count()
    invalid=columns.filter(hl.is_defined(columns.s)&~columns.s.matches('^[0-9]+$')).count()
    absent=roster.anti_join(columns).count();extra=columns.anti_join(roster).count()
    meta=dict(vds_samples=n,roster_samples=rn,duplicated_sample_keys=duplicates,
              missing_sample_ids=missing,non_integer_sample_ids=invalid,
              roster_absent=absent,vds_extra=extra,passed=n==rn and not any([duplicates,missing,invalid,absent,extra]))
    write_json('VDS_ROSTER_AUDIT',meta)
    if not meta['passed']: raise ValueError('VDS roster audit failed; inspect internal artifact')

if __name__=='__main__': main()
