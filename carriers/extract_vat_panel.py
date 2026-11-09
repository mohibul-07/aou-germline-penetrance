"""Streaming, header-driven reconstruction of VAT extraction.
Inputs: VAT compressed TSV, TARGETS_BED confirmed bed0; outputs PANEL_VAT,
PANEL_SITES VCF and PANEL_AC TSV; scratch VAT_SQLITE. Paths from config.
Decisions: retain regional rows; deduplicate sites, not transcript evidence;
never assume a fixed allele-count column; no annotation is a carrier call.
Original extraction commands are not recoverable; this corrects reconstruction bugs.
"""
import csv,gzip,sqlite3,subprocess
from pathlib import Path
from workflow.runtime import external,env
from carriers.keys import vat_to_vcf

def main():
    if env('TARGETS_COORDINATE_SYSTEM')!='bed0': raise ValueError('BED convention unconfirmed')
    db=external('VAT_SQLITE',True)
    if db.exists(): raise ValueError('Choose a fresh scratch database')
    con=sqlite3.connect(db)
    con.execute('CREATE TABLE sites (vid TEXT PRIMARY KEY, chrom TEXT,pos INTEGER,ref TEXT,alt TEXT,ac TEXT)')
    try:
        with gzip.open(external('VAT'),'rt') as f: header=next(csv.reader(f,delimiter='\t'))
        header[0]=header[0].lstrip('#')
        vi=header.index('vid'); ai=header.index('gvs_all_ac')
        with external('PANEL_VAT',True).open('w') as out:
            writer=csv.writer(out,delimiter='\t');writer.writerow(header)
            with Path(env('TARGETS_BED')).open() as regions:
                for line in regions:
                    if not line.strip() or line.startswith('#'): continue
                    chrom,start,end,*_=line.split()
                    if int(start)<0 or int(end)<=int(start): raise ValueError('Invalid BED interval')
                    proc=subprocess.Popen(['tabix',str(external('VAT')),f'{chrom}:{int(start)+1}-{end}'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
                    for row in csv.reader(proc.stdout,delimiter='\t'):
                        writer.writerow(row)
                        c,p,r,a=vat_to_vcf(row[vi])
                        con.execute('INSERT OR IGNORE INTO sites VALUES (?,?,?,?,?,?)',(row[vi],c,p,r,a,row[ai]))
                    if proc.wait()!=0: raise RuntimeError('tabix extraction failed')
                    con.commit()
        with external('PANEL_SITES',True).open('w') as out, external('PANEL_AC',True).open('w') as ac:
            out.write('##fileformat=VCFv4.2\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n')
            for vid,c,p,r,a,count in con.execute('SELECT * FROM sites ORDER BY chrom,pos,ref,alt'):
                out.write(f'{c}\t{p}\t.\t{r}\t{a}\t.\t.\t.\n');ac.write(f'{vid}\t{count}\n')
    finally: con.close()

if __name__=='__main__': main()
