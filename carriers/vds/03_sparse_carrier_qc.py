"""Reconstruct sparse target-carrier QC descriptions for resolved pilot alleles.
Inputs: PILOT_ROW_MAP, pilot VDS; output SPARSE_PILOT_AUDIT internal JSON.
Decisions: convert LGT via LA to global GT, count target allele dosage, describe
FT and GQ bins. GQ boundary is descriptive ONLY; no quality-pass rule adopted.
No individual carrier IDs are collected or exported by this step.
"""
from workflow.runtime import env,write_json
from carriers.vds.common import initialize,load_pilot,mapped_matrix

def main():
    hl=initialize();mt=mapped_matrix(hl,load_pilot(hl).variant_data)
    mt=mt.annotate_entries(GT=hl.vds.lgt_to_gt(mt.LGT,mt.LA))
    mt=mt.annotate_entries(target_dosage=hl.or_missing(hl.is_defined(mt.GT),
        hl.sum(hl.range(mt.GT.ploidy).map(lambda i:hl.int32(mt.GT[i]==mt.targets.alt_index)))))
    carrier=mt.target_dosage>0
    boundary=int(env('DESCRIPTIVE_GQ_BOUNDARY'))
    mt=mt.annotate_rows(raw_carriers=hl.agg.count_where(carrier),
        ft=hl.agg.filter(carrier,hl.agg.counter(hl.if_else(hl.is_missing(mt.FT),'missing',hl.str(mt.FT)))),
        gq=hl.agg.filter(carrier,hl.agg.counter(hl.if_else(hl.is_missing(mt.GQ),'missing',
            hl.if_else(mt.GQ>=boundary,'at_least_boundary','below_boundary')))))
    rows=mt.rows().select('targets','raw_carriers','ft','gq').collect()
    write_json('SPARSE_PILOT_AUDIT',[dict(target_key=r.targets.target_key,raw_carriers=r.raw_carriers,
                                        ft=dict(r.ft),gq=dict(r.gq)) for r in rows])

if __name__=='__main__': main()
