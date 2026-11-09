"""Hail initialization and pilot interval helpers for the reconstructed pilot.
Inputs: environment config, external PILOT_TARGETS TSV target_key,gene,group.
Outputs: lazy Hail objects only; user-visible results are never printed.
Decisions: GRCh38, bounded pilot intervals, no full-panel extraction by default.
"""
import csv
from workflow.runtime import env,external

def initialize():
    import hail as hl
    hl.init(master=env('HAIL_MASTER'),log=str(external('HAIL_LOG',True)),
        tmp_dir=env('HAIL_TMP_DIR'),quiet=True,
        spark_conf={'spark.driver.memory':env('HAIL_DRIVER_MEMORY'),
                    'spark.driver.maxResultSize':env('HAIL_MAX_RESULT_SIZE'),
                    'spark.hadoop.fs.gs.requester.pays.mode':'AUTO',
                    'spark.hadoop.fs.gs.requester.pays.project.id':env('GOOGLE_PROJECT'),
                    'spark.hadoop.fs.gs.requester.pays.buckets':env('REQUESTER_PAYS_BUCKET')})
    hl.default_reference('GRCh38')
    return hl

def targets():
    from carriers.keys import canonical_key
    with external('PILOT_TARGETS').open() as f: rows=list(csv.DictReader(f,delimiter='\t'))
    for r in rows: r['target_key']=canonical_key(r['target_key'])
    if not rows or len(rows)>int(env('PILOT_MAX_TARGETS')):
        raise ValueError('Pilot target limit exceeded; full extraction not implemented')
    if len({r['target_key'] for r in rows})!=len(rows): raise ValueError('Duplicate pilot targets')
    return rows

def load_pilot(hl):
    vds=hl.vds.read_vds(env('VDS_PATH'))
    if vds.variant_data.locus.dtype.reference_genome.name!='GRCh38': raise ValueError('Wrong reference genome')
    intervals=[]
    for r in targets():
        c,p,_,_=r['target_key'].split(':');pos=int(p)
        # Minimal representation can shift positions. Only this local pilot window
        # is searched; unmatched is unresolved, not an absent allele or noncarrier.
        pad=int(env('PILOT_INTERVAL_PADDING'))
        intervals.append(hl.parse_locus_interval(f'{c}:{max(1,pos-pad)}-{pos+pad}',reference_genome='GRCh38'))
    maxlen=hl.eval(vds.reference_data.index_globals().ref_block_max_length)
    if maxlen is None or maxlen<=0: raise ValueError('Reference-block maximum is required')
    # Hail uses its maximum-length reference-block metadata for interval slicing.
    return hl.vds.filter_intervals(vds,intervals,split_reference_blocks=True)

def mapped_matrix(hl,mt):
    import json
    raw=json.loads(external('PILOT_ROW_MAP').read_text())
    groups={}
    for r in raw:
        if r['status']!='unique_match': continue
        groups.setdefault(r['raw_key'],[]).append(dict(target_key=r['target_key'],alt_index=r['alt_index']))
    if not groups: raise ValueError('No uniquely resolved targets')
    lookup=hl.literal(groups,hl.tdict(hl.tstr,hl.tarray(hl.tstruct(target_key=hl.tstr,alt_index=hl.tint32))))
    key=hl.str(mt.locus)+':'+hl.delimit(mt.alleles,':')
    mt=mt.annotate_rows(targets=lookup.get(key))
    mt=mt.filter_rows(hl.is_defined(mt.targets));mt=mt.explode_rows(mt.targets)
    return mt
