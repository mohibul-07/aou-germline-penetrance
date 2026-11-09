"""Reconstruct corrected dense reference-call pilot with missing entries retained.
Inputs: pilot VDS, PILOT_ROW_MAP, SPARSE_PILOT_AUDIT; output DENSE_PILOT_AUDIT.
Decisions: interval-filter before dense conversion, unfilter_entries, preserve
missing GT; compare target counts to sparse pilot. Defined without target can
include another ALT, so it is not always a reference-homozygous call.
No full-panel extraction or final genotype QC policy is implemented.
"""
import json
from workflow.runtime import external,write_json
from carriers.vds.common import initialize,load_pilot,mapped_matrix

def main():
    hl=initialize();vds=load_pilot(hl)
    vm=vds.variant_data.annotate_entries(GT=hl.vds.lgt_to_gt(vds.variant_data.LGT,vds.variant_data.LA))
    vds=hl.vds.VariantDataset(vds.reference_data,vm)
    mt=mapped_matrix(hl,hl.vds.to_dense_mt(vds).unfilter_entries())
    n=mt.count_cols()
    mt=mt.annotate_entries(target_dosage=hl.or_missing(hl.is_defined(mt.GT),
        hl.sum(hl.range(mt.GT.ploidy).map(lambda i:hl.int32(mt.GT[i]==mt.targets.alt_index)))))
    mt=mt.annotate_rows(sample_entries=hl.agg.count(),target_carriers=hl.agg.count_where(mt.target_dosage>0),
        defined_calls_without_target=hl.agg.count_where(mt.target_dosage==0),
        missing_calls=hl.agg.count_where(hl.is_missing(mt.GT)))
    sparse={r['target_key']:r['raw_carriers'] for r in json.loads(external('SPARSE_PILOT_AUDIT').read_text())}
    out=[]
    for r in mt.rows().select('targets','sample_entries','target_carriers','defined_calls_without_target','missing_calls').collect():
        if r.sample_entries!=n or r.target_carriers+r.defined_calls_without_target+r.missing_calls!=n or sparse[r.targets.target_key]!=r.target_carriers:
            raise ValueError('Pilot invariant failed; do not mark validation passed')
        out.append(dict(target_key=r.targets.target_key,samples=n,carriers=r.target_carriers,
                        defined_without_target=r.defined_calls_without_target,missing=r.missing_calls))
    if set(sparse)!={r['target_key'] for r in out}: raise ValueError('Pilot target sets differ')
    write_json('DENSE_PILOT_AUDIT',out)

if __name__=='__main__': main()
