"""Classify malignant site evidence within already selected PheTK mappings.
Inputs: PHECODE_OUTPUT Parquet dated mapped evidence. Output: PHECODE_TIERS Parquet.
Decision: broad means mapped evidence; strict excludes appendix, renal pelvis,
trachea and non-cutaneous melanoma. Other evidence stays broad, not cancer-free.
Personal-history/in-situ subcategory labels need the original reviewed map; they
are not guessed here. Reconstructed malignant rules from the saved report code.
"""
from workflow.runtime import external

def malignant(cancer,vocabulary,code):
    c=str(code).upper().replace('.','').strip()
    if vocabulary=='ICD10CM':
        if cancer=='colorectal': return c.startswith(('C18','C19','C20')) and not c.startswith('C181')
        prefixes={'breast':('C50',),'prostate':('C61',),'lung':('C34',),'kidney':('C64',),
                  'melanoma':('C43',),'ovarian':('C56',),'pancreatic':('C25',),'stomach':('C16',)}
    elif vocabulary=='ICD9CM':
        if cancer=='colorectal': return (c.startswith('153') and not c.startswith('1535')) or c.startswith(('1540','1541'))
        if cancer=='lung': return c.startswith('162') and not c.startswith('1620')
        prefixes={'breast':('174','175'),'prostate':('185',),'kidney':('1890',),
                  'melanoma':('172',),'ovarian':('1830',),'pancreatic':('157',),'stomach':('151',)}
    else: return False
    return c.startswith(prefixes.get(cancer,()))

def main():
    import pyarrow as pa
    import pyarrow.parquet as pq
    writer=None
    try:
        for b in pq.ParquetFile(external('PHECODE_OUTPUT')).iter_batches():
            d=b.to_pydict()
            d['malignant']=[malignant(c,v,k) for c,v,k in zip(d['cancer'],d['vocabulary_id'],d['code'])]
            t=pa.table(d)
            if writer is None: writer=pq.ParquetWriter(external('PHECODE_TIERS',True),t.schema)
            writer.write_table(t)
    finally:
        if writer: writer.close()

if __name__=='__main__': main()
