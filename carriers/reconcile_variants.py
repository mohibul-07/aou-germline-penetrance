"""Reconstruct target-panel filtering and exact source membership reconciliation.
Inputs: COMPARISON_TSV (key,gene,group), headerless CLINVAR_KEYS and FASTVEP_KEYS,
PANEL_GENES. Outputs: SUPPORTED_VARIANTS, UNRESOLVED_VARIANTS, RECONCILE_AUDIT.
Decision: target gene filter; remove exact duplicate rows only; reconstruct labels
from source membership. Unsupported keys are retained for review, never invented.
Historical totals are documented in MANIFEST, not embedded as executable results.
"""
import csv
from collections import defaultdict
from workflow.runtime import external, write_json
from carriers.keys import canonical_key

def source_keys(path):
    with path.open() as f:
        return {canonical_key(row[0]) for row in csv.reader(f,delimiter='\t') if row}

def reconcile(rows, genes, clinvar, fastvep):
    assignments = defaultdict(set)
    seen = set()
    for row in rows:
        if row['gene'] not in genes:
            continue
        sig = tuple(sorted(row.items()))
        if sig in seen:
            continue
        seen.add(sig)
        assignments[canonical_key(row['key'])].add((row['gene'],row['group']))
    supported, unresolved = [], []
    for key, labels in sorted(assignments.items()):
        cv, fv = key in clinvar, key in fastvep
        group = 'concordant' if cv and fv else 'clinvar_only' if cv else 'fastvep_only' if fv else 'absent_from_both_source_lists'
        row = dict(target_key=key, gene=';'.join(sorted({g for g,_ in labels})),
                   group=group, saved_labels=';'.join(sorted({g for _,g in labels})),
                   multiple_genes=len({g for g,_ in labels})>1)
        (supported if cv or fv else unresolved).append(row)
    return supported, unresolved

def main():
    # Panel is public config; all variant inputs/outputs remain outside repo.
    from workflow.runtime import env
    from pathlib import Path
    genes=set(Path(env('PANEL_GENES')).read_text().split())
    with external('COMPARISON_TSV').open() as f:
        rows=list(csv.DictReader(f,delimiter='\t'))
    supported,unresolved=reconcile(rows,genes,source_keys(external('CLINVAR_KEYS')),source_keys(external('FASTVEP_KEYS')))
    fields=['target_key','gene','group','saved_labels','multiple_genes']
    for variable, records in [('SUPPORTED_VARIANTS',supported),('UNRESOLVED_VARIANTS',unresolved)]:
        with external(variable,True).open('w') as f:
            w=csv.DictWriter(f,fields,delimiter='\t');w.writeheader();w.writerows(records)
    write_json('RECONCILE_AUDIT',{'supported_keys':len(supported),'unresolved_keys':len(unresolved),
        'normalization':'prefix/format only; not left alignment or build verification'})

if __name__ == '__main__':
    main()
