"""Reconstruct pilot variant-key access and minimal-representation mapping.
Inputs: PILOT_TARGETS (externally restored historical pilot), VDS_PATH.
Output: PILOT_ROW_MAP JSON and unique/unresolved matches; no carrier calls.
Decisions: retain original row alleles/global ALT index; min_rep trims context,
not reference-based left alignment. Ambiguous/unmatched targets are unresolved.
Exact historical pilot keys are deliberately not embedded in source code.
"""
from workflow.runtime import write_json
from carriers.vds.common import initialize,load_pilot,targets

def main():
    hl=initialize();vds=load_pilot(hl);t=vds.variant_data.rows()
    t=t.select(alt=hl.range(1,hl.len(t.alleles)));t=t.explode(t.alt)
    t=t.annotate(minimal=hl.min_rep(t.locus,[t.alleles[0],t.alleles[t.alt]]))
    # Collect only small pilot row-key metadata, never genotype/sample entries.
    wanted={r['target_key'] for r in targets()}
    t=t.annotate(target_key=hl.str(t.minimal.locus)+':'+hl.delimit(t.minimal.alleles,':'))
    t=t.filter(hl.literal(wanted).contains(t.target_key))
    found={k:[] for k in wanted}
    for r in t.collect():
        found[r.target_key].append(dict(raw_key=str(r.locus)+':'+':'.join(r.alleles),alt_index=r.alt))
    out=[]
    for target in targets():
        matches=found[target['target_key']]
        if len(matches)==1: out.append({**target,**matches[0],'status':'unique_match'})
        else: out.append({**target,'status':'unresolved','matches':matches})
    write_json('PILOT_ROW_MAP',out)

if __name__=='__main__': main()
