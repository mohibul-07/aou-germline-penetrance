"""Reconstruct broad/strict distinct-date counts and threshold flags on full roster.
Inputs: PHECODE_TIERS and WGS_ROSTER; output PHECODE_FLAGS Parquet.
Decision: same-date codes count once per cancer, >=1 primary, >=2 sensitivity;
no roster participant is removed. Run in Workbench; output is participant-level.
Uses SQLite on disk to avoid storing all distinct dates in Python memory.
"""
import sqlite3
from workflow.runtime import external

def main():
    import pyarrow as pa
    import pyarrow.parquet as pq
    db=external('PHECODE_SQLITE',True)
    if db.exists(): raise ValueError('Choose a new scratch database path')
    con=sqlite3.connect(db)
    try:
        con.execute('CREATE TABLE dates (person_id INTEGER,cancer TEXT,date TEXT,malignant INTEGER, PRIMARY KEY(person_id,cancer,date))')
        for b in pq.ParquetFile(external('PHECODE_TIERS')).iter_batches():
            rows=b.to_pylist()
            con.executemany('INSERT INTO dates VALUES (?,?,?,?) ON CONFLICT(person_id,cancer,date) DO UPDATE SET malignant=MAX(malignant,excluded.malignant)',
                [(r['person_id'],r['cancer'],str(r['date']),int(r['malignant'])) for r in rows])
            con.commit()
        ids=pq.read_table(external('WGS_ROSTER'),columns=['person_id'])['person_id'].to_pylist()
        con.execute('CREATE TABLE roster(person_id INTEGER PRIMARY KEY)')
        con.executemany('INSERT INTO roster VALUES (?)',[(v,) for v in ids])
        # All approved cancers, including those with no matched dates, come from the map.
        import csv
        with external('PHECODE_MAPPING').open() as f: cancers=sorted({r['cancer'] for r in csv.DictReader(f)})
        con.execute('CREATE TABLE cancers(cancer TEXT PRIMARY KEY)')
        con.executemany('INSERT INTO cancers VALUES (?)',[(v,) for v in cancers])
        cur=con.execute('SELECT r.person_id,c.cancer,COUNT(d.date),COALESCE(SUM(d.malignant),0) FROM roster r CROSS JOIN cancers c LEFT JOIN dates d ON r.person_id=d.person_id AND c.cancer=d.cancer GROUP BY r.person_id,c.cancer')
        writer=None
        try:
            while True:
                rows=cur.fetchmany(25000)
                if not rows: break
                records=[dict(person_id=i,cancer=c,broad_dates=b,malignant_dates=m,broad_ge1=b>=1,broad_ge2=b>=2,malignant_ge1=m>=1,malignant_ge2=m>=2) for i,c,b,m in rows]
                t=pa.Table.from_pylist(records)
                if writer is None: writer=pq.ParquetWriter(external('PHECODE_FLAGS',True),t.schema)
                writer.write_table(t)
        finally:
            if writer: writer.close()
    finally: con.close()

if __name__=='__main__': main()
