"""Workbench I/O and bounded query execution.
Inputs: exported config/params.env, external files. Outputs: files outside this repo.
Decision: dry run by default; execution is explicit and capped. Never print results.
New export infrastructure, not an original notebook cell.
"""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def env(name):
    value = os.environ.get(name)
    if not value:
        raise ValueError('Missing configuration: ' + name)
    return value

def external(name, output=False):
    p = Path(env(name)).expanduser().resolve()
    if p == ROOT or ROOT in p.parents:
        raise ValueError('Analysis inputs/outputs must stay outside the code repository')
    if output:
        p.parent.mkdir(parents=True, exist_ok=True)
    return p

def write_json(name, value):
    external(name, True).write_text(json.dumps(value, indent=2, default=str))

def roster_parameter():
    import pyarrow.parquet as pq
    from google.cloud import bigquery
    ids = pq.read_table(external('WGS_ROSTER'), columns=['person_id'])['person_id'].to_pylist()
    if any(v is None for v in ids) or len(ids) != len(set(ids)):
        raise ValueError('Roster IDs must be present and unique')
    return bigquery.ScalarQueryParameter('wgs_ids', 'STRING', '\n'.join(str(int(v)) for v in ids))

def cdr():
    import re
    value = env('WORKSPACE_CDR')
    if not re.fullmatch(r'[A-Za-z0-9_-]+\.[A-Za-z0-9_]+', value):
        raise ValueError('Expected project.dataset')
    return value

ROSTER_CTE = "SELECT CAST(id AS INT64) AS person_id FROM UNNEST(SPLIT(@wgs_ids, '\\n')) AS id"

def run_query(sql, parameters, prefix, cap_gib=None):
    """Save SQL and dry-run metadata; only execute with RUN_QUERIES=1.
    Prefix config variables: _SQL, _METADATA, _OUTPUT. Parquet streams in batches.
    cap_gib optionally restores a step's historical billing cap; the effective
    cap is never above MAXIMUM_BYTES_BILLED. Returns True only if executed.
    Metadata and results are internal Workbench artifacts, not cleared for release.
    """
    from google.cloud import bigquery
    client = bigquery.Client(project=env('GOOGLE_PROJECT'))
    external(prefix + '_SQL', True).write_text(sql)
    estimate = client.query(sql, job_config=bigquery.QueryJobConfig(
        dry_run=True, use_query_cache=False, query_parameters=parameters))
    cap = int(env('MAXIMUM_BYTES_BILLED'))
    if cap_gib is not None:
        cap = min(cap, int(cap_gib * 1024**3))
    meta = {'dry_run_bytes': estimate.total_bytes_processed, 'maximum_bytes_billed': cap,
            'executed': False, 'cdr': cdr()}
    write_json(prefix + '_METADATA', meta)
    if os.environ.get('RUN_QUERIES', '0') != '1':
        return False
    if estimate.total_bytes_processed > cap:
        raise ValueError('Estimated query exceeds configured cap')
    import pyarrow.parquet as pq
    job = client.query(sql, job_config=bigquery.QueryJobConfig(
        query_parameters=parameters, maximum_bytes_billed=cap))
    writer = None
    try:
        for batch in job.result().to_arrow_iterable():
            if writer is None:
                writer = pq.ParquetWriter(external(prefix + '_OUTPUT', True), batch.schema)
            writer.write_batch(batch)
        if writer is None:
            # Empty result schema is retained without collecting participant rows.
            table = job.result().to_arrow()
            pq.write_table(table, external(prefix + '_OUTPUT', True))
    finally:
        if writer is not None:
            writer.close()
    meta.update(executed=True, job_id=job.job_id,
                actual_bytes_processed=job.total_bytes_processed,
                actual_bytes_billed=job.total_bytes_billed)
    write_json(prefix + '_METADATA', meta)
    return True

def read_json(name):
    return json.loads(external(name).read_text())

def update_json(name, values):
    """Merge decision/provenance fields into an existing metadata file."""
    path = external(name, True)
    current = json.loads(path.read_text()) if path.is_file() else {}
    current.update(values)
    path.write_text(json.dumps(current, indent=2, default=str))
