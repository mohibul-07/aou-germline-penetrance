"""Reconstruct conservative EHR family-history evidence extraction (observation).
Inputs: CLINICAL_FH_MAPPING CSV concept_id,evidence_class; WGS_ROSTER; CDR.
Outputs: CLINICAL_FH_* SQL/metadata/internal Parquet, without raw patient text.
Decisions: exclude PPI source vocabulary and configured survey record types;
keep code/value evidence and date summaries separate. Numeric zero or missing
text does not establish negative history. This query is reconstructed, not the
original observed-value review; downstream additional-review mapping is required.
The original condition-table audit source was not recovered.
"""
import csv,json
from workflow.runtime import external,env,cdr,run_query,roster_parameter,ROSTER_CTE

def main():
    from google.cloud import bigquery
    with external('CLINICAL_FH_MAPPING').open() as f: rows=list(csv.DictReader(f))
    mapping=[dict(concept_id=int(r['concept_id']),evidence_class=r['evidence_class']) for r in rows]
    q=f"""WITH roster AS ({ROSTER_CTE}), mapping AS (
 SELECT CAST(JSON_VALUE(x,'$.concept_id') AS INT64) AS concept_id,
 JSON_VALUE(x,'$.evidence_class') AS evidence_class FROM UNNEST(JSON_QUERY_ARRAY(@mapping)) x)
 SELECT o.person_id,o.observation_concept_id,o.value_as_concept_id,m.evidence_class,
 COUNT(*) AS source_records,COUNT(DISTINCT o.observation_date) AS distinct_dates,
 MIN(o.observation_date) AS first_date,MAX(o.observation_date) AS last_date,
 COUNTIF(o.observation_date IS NULL) AS undated_rows,
 COUNTIF(o.value_as_number=0) AS numeric_zero_rows,
 COUNTIF(NULLIF(TRIM(o.value_as_string),'') IS NOT NULL) AS text_present_rows
 FROM `{cdr()}.observation` o JOIN roster USING(person_id)
 JOIN mapping m ON o.observation_concept_id=m.concept_id
 LEFT JOIN `{cdr()}.concept` sc ON sc.concept_id=o.observation_source_concept_id
 WHERE COALESCE(sc.vocabulary_id,'')!='PPI'
 AND COALESCE(o.observation_type_concept_id,0) NOT IN UNNEST(@survey_types)
 GROUP BY o.person_id,o.observation_concept_id,o.value_as_concept_id,m.evidence_class"""
    params=[roster_parameter(),bigquery.ScalarQueryParameter('mapping','STRING',json.dumps(mapping)),
       bigquery.ArrayQueryParameter('survey_types','INT64',[int(x) for x in env('SURVEY_RECORD_TYPES').split(',')])]
    run_query(q,params,'CLINICAL_FH')

if __name__=='__main__': main()
