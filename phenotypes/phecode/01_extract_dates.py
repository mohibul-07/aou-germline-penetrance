"""Reconstruct dated PheTK/phecodeX evidence aggregation; historical branch paused.
Input: PHECODE_MAPPING CSV vocabulary_id,code,phecode,cancer; WGS_ROSTER; CDR.
Output: PHECODE_* SQL/metadata/internal Parquet grouped by person,cancer,date,code.
Decision: exact source-code mapping only, normalized dots/case; no descendants.
The installed PheTK map and package version must be restored; no map is bundled.
This reconstructs the query approach, not an unverified PheTK API call.
"""
import csv,json
from workflow.runtime import external,cdr,run_query,roster_parameter,ROSTER_CTE

def main():
    from google.cloud import bigquery
    with external('PHECODE_MAPPING').open() as f: mapping=list(csv.DictReader(f))
    q=f"""WITH roster AS ({ROSTER_CTE}), mapping AS (
 SELECT JSON_VALUE(x,'$.vocabulary_id') AS vocabulary_id,
 REPLACE(UPPER(JSON_VALUE(x,'$.code')),'.','') AS code,
 JSON_VALUE(x,'$.phecode') AS phecode,JSON_VALUE(x,'$.cancer') AS cancer
 FROM UNNEST(JSON_QUERY_ARRAY(@mapping)) x)
 SELECT DISTINCT co.person_id,m.cancer,m.phecode,co.condition_start_date AS date,
 c.vocabulary_id,REPLACE(UPPER(c.concept_code),'.','') AS code
 FROM `{cdr()}.condition_occurrence` co JOIN roster USING(person_id)
 JOIN `{cdr()}.concept` c ON co.condition_source_concept_id=c.concept_id
 JOIN mapping m ON c.vocabulary_id=m.vocabulary_id AND REPLACE(UPPER(c.concept_code),'.','')=m.code
 WHERE co.condition_start_date IS NOT NULL"""
    run_query(q,[roster_parameter(),bigquery.ScalarQueryParameter('mapping','STRING',json.dumps(mapping))],'PHECODE')

if __name__=='__main__': main()
