"""Adapt the recovered prepare_family_survey_query.py into an env-driven step.
Inputs: SURVEY_PAIR_MAPPING CSV with reviewed exact question/answer pairs,
WGS_ROSTER, ds_survey. Outputs: SURVEY_* query, metadata, internal evidence Parquet.
Decisions: preserve Self, relative, root None, root self-or-family and unknown
separately; aggregate distinct dates and retain undated response counts.
Mapping content is withheld, never reconstructed from memory.
"""
import csv
import json
from workflow.runtime import external, cdr, roster_parameter, run_query, ROSTER_CTE

def main():
    from google.cloud import bigquery
    with external('SURVEY_PAIR_MAPPING').open() as f:
        rows=list(csv.DictReader(f))
    mapping=[dict(question_id=int(r['question_concept_id']),answer_id=int(r['answer_concept_id']),
                  evidence_class=r['evidence_class'],relative=r['relative']) for r in rows]
    if any(r['evidence_class']=='needs_review' for r in mapping) or len({(r['question_id'],r['answer_id']) for r in mapping})!=len(mapping):
        raise ValueError('Mapping must be reviewed and unique by question/answer')
    q=f"""WITH roster AS ({ROSTER_CTE}), mapping AS (
 SELECT CAST(JSON_VALUE(item,'$.question_id') AS INT64) AS question_id,
 CAST(JSON_VALUE(item,'$.answer_id') AS INT64) AS answer_id,
 JSON_VALUE(item,'$.evidence_class') AS evidence_class, JSON_VALUE(item,'$.relative') AS relative
 FROM UNNEST(JSON_QUERY_ARRAY(@pair_mapping)) item)
 SELECT s.person_id,s.question_concept_id,s.answer_concept_id,m.evidence_class,m.relative,
 COUNT(DISTINCT DATE(s.survey_datetime)) AS distinct_response_dates,
 MIN(s.survey_datetime) AS first_response_datetime,MAX(s.survey_datetime) AS last_response_datetime,
 COUNTIF(s.survey_datetime IS NULL) AS undated_response_rows
 FROM `{cdr()}.ds_survey` s JOIN roster USING(person_id)
 JOIN mapping m ON s.question_concept_id=m.question_id AND s.answer_concept_id=m.answer_id
 WHERE s.question_concept_id IN UNNEST(@question_ids)
 GROUP BY s.person_id,s.question_concept_id,s.answer_concept_id,m.evidence_class,m.relative"""
    params=[roster_parameter(),bigquery.ScalarQueryParameter('pair_mapping','STRING',json.dumps(mapping)),
            bigquery.ArrayQueryParameter('question_ids','INT64',sorted({r['question_id'] for r in mapping}))]
    run_query(q,params,'SURVEY')

if __name__ == '__main__':
    main()
