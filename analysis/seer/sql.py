"""Recovered BigQuery SQL for the October 20-22, 2026 SEER workflow.

Provenance: the SQL text below was copied from the notebook cells that the
Codex session (rollout 2026-10-02 ... 01a0fce5) gave Md to run in the Workbench
on October 21-22, 2026. Each function names its source message and timestamp.
Changes from the historical cells are limited to:
  * the CDR identifier is passed in instead of a hard-coded string;
  * Python variables are returned instead of being left in notebook globals.
The query bodies, parameter names, joins, filters, labels and ordering are
unchanged. The 2023 SEER-aligned query is still derived from the 2025 query by
the same two asserted string replacements that were used historically.

Inputs: a `project.dataset` CDR string. Outputs: SQL strings only.
No query runs at import.
"""

CANCERS = [
    "breast", "prostate", "colorectal", "melanoma", "lung",
    "kidney", "ovarian", "pancreatic", "stomach",
]


def coverage_preflight(CDR):
    """Codex msg 2409, 2026-10-21T15:17Z; executed as job 6d2f1f73-... (msg 2419)."""
    return f"""
WITH roster AS (
  SELECT CAST(person_id AS INT64) AS person_id
  FROM UNNEST(SPLIT(@wgs_ids, '\\n')) AS person_id
),
program_flags AS (
  SELECT
    person_id,
    COUNT(*) AS source_rows,
    MAX(COALESCE(has_ehr_data, 0)) AS has_ehr,
    MAX(COALESCE(has_whole_genome_variant, 0)) AS has_wgs
  FROM `{CDR}.cb_search_person`
  GROUP BY person_id
),
diagnosis_coverage AS (
  SELECT
    co.person_id,
    COUNT(*) AS condition_records,
    COUNTIF(co.condition_start_date IS NOT NULL) AS dated_records,
    COUNT(DISTINCT co.condition_start_date) AS distinct_condition_dates,
    COUNTIF(c.vocabulary_id IN ('ICD9CM', 'ICD10CM')) AS icd_records,
    COUNTIF(
      c.vocabulary_id IN ('ICD9CM', 'ICD10CM')
      AND co.condition_start_date IS NOT NULL
    ) AS dated_icd_records
  FROM `{CDR}.condition_occurrence` AS co
  JOIN roster AS r ON r.person_id = co.person_id
  LEFT JOIN `{CDR}.concept` AS c
    ON c.concept_id = co.condition_source_concept_id
  GROUP BY co.person_id
)
SELECT
  COUNT(*) AS verified_wgs_roster,
  COUNTIF(p.person_id IS NOT NULL) AS roster_in_program_table,
  COUNTIF(p.source_rows > 1) AS roster_with_duplicate_program_rows,
  COUNTIF(p.has_wgs = 1) AS roster_with_program_wgs_flag,
  (
    SELECT COUNT(*)
    FROM program_flags
    WHERE has_wgs = 1
  ) AS program_wgs_flag_total,
  (
    SELECT COUNT(*)
    FROM program_flags AS f
    LEFT JOIN roster AS r ON r.person_id = f.person_id
    WHERE f.has_wgs = 1 AND r.person_id IS NULL
  ) AS program_wgs_flag_outside_verified_roster,
  COUNTIF(p.has_ehr = 1) AS roster_with_ehr_flag,
  COUNTIF(d.condition_records > 0) AS roster_with_any_condition,
  COUNTIF(d.dated_records > 0) AS roster_with_dated_condition,
  COUNTIF(d.distinct_condition_dates >= 2) AS roster_with_ge2_condition_dates,
  COUNTIF(d.icd_records > 0) AS roster_with_icd_source_condition,
  COUNTIF(d.dated_icd_records > 0) AS roster_with_dated_icd_source_condition,
  COUNTIF(
    p.has_ehr = 1 AND COALESCE(d.condition_records, 0) = 0
  ) AS ehr_flag_without_condition,
  COUNTIF(
    COALESCE(p.has_ehr, 0) != 1 AND d.condition_records > 0
  ) AS condition_without_ehr_flag,
  COUNTIF(
    d.condition_records > 0 AND d.dated_records = 0
  ) AS condition_but_no_dated_condition
FROM roster AS r
LEFT JOIN program_flags AS p ON p.person_id = r.person_id
LEFT JOIN diagnosis_coverage AS d ON d.person_id = r.person_id
"""


def concept_vocabulary_audit(CDR):
    """Codex msg 2472, 2026-10-21T15:35Z; executed as job 29c127ba-... (msg 2482)."""
    return f"""
SELECT
  concept_id,
  concept_name,
  domain_id,
  vocabulary_id,
  concept_class_id,
  standard_concept,
  concept_code,
  valid_start_date,
  valid_end_date,
  invalid_reason
FROM `{CDR}.concept`
WHERE concept_id IN UNNEST(@concept_ids)
ORDER BY concept_id
"""


def replacement_audit(CDR):
    """Codex msg 2494, 2026-10-21T15:38Z; executed as job 7e01f254-... (msg 2514)."""
    return f"""
SELECT
  cr.concept_id_1 AS original_concept_id,
  cr.relationship_id,
  cr.concept_id_2 AS target_concept_id,
  cr.invalid_reason AS relationship_invalid_reason,
  cr.valid_start_date AS relationship_valid_start,
  cr.valid_end_date AS relationship_valid_end,
  c.concept_name AS target_name,
  c.domain_id AS target_domain,
  c.vocabulary_id AS target_vocabulary,
  c.standard_concept AS target_standard_status,
  c.invalid_reason AS target_invalid_reason
FROM `{CDR}.concept_relationship` AS cr
LEFT JOIN `{CDR}.concept` AS c
  ON c.concept_id = cr.concept_id_2
WHERE cr.concept_id_1 IN UNNEST(@concept_ids)
  AND cr.relationship_id IN ('Maps to', 'Concept replaced by')
ORDER BY original_concept_id, relationship_id, target_concept_id
"""


def replacement_impact(CDR):
    """Codex msg 2524, 2026-10-21T15:42Z. DRY-RUN ONLY historically.

    Md stopped this step (msgs 2541-2554); the patient-level impact query was
    never executed, and the original mapping was frozen as the baseline.
    """
    return f"""
WITH roster AS (
  SELECT CAST(person_id AS INT64) AS person_id
  FROM UNNEST(SPLIT(@wgs_ids, '\\n')) AS person_id
),
mapping AS (
  SELECT
    JSON_VALUE(item, '$.cancer') AS cancer,
    CAST(JSON_VALUE(item, '$.concept_id') AS INT64) AS concept_id,
    JSON_VALUE(item, '$.mapping_set') AS mapping_set
  FROM UNNEST(JSON_QUERY_ARRAY(@mapping_json)) AS item
),
hits AS (
  SELECT
    co.person_id,
    m.cancer,
    m.concept_id,
    m.mapping_set,
    co.condition_start_date
  FROM `{CDR}.condition_occurrence` AS co
  JOIN roster USING (person_id)
  JOIN mapping AS m ON m.concept_id = co.condition_concept_id
),
original_people AS (
  SELECT DISTINCT person_id, cancer
  FROM hits
  WHERE mapping_set = 'original'
)
SELECT
  h.cancer,
  h.concept_id,
  h.mapping_set,
  COUNT(*) AS records,
  COUNT(DISTINCT h.person_id) AS participants,
  COUNTIF(h.condition_start_date IS NULL) AS undated_records,
  COUNT(DISTINCT IF(
    h.condition_start_date IS NOT NULL, h.person_id, NULL
  )) AS participants_with_dated_hit,
  COUNT(DISTINCT IF(
    o.person_id IS NULL, h.person_id, NULL
  )) AS participants_without_any_original_group_hit
FROM hits AS h
LEFT JOIN original_people AS o
  ON o.person_id = h.person_id AND o.cancer = h.cancer
GROUP BY 1,2,3
ORDER BY 1,3,2
"""


def birth_year_baseline(CDR):
    """Codex msg 2554, 2026-10-21T15:53Z; executed as job 46c494d2-... (msg 2564).

    Preliminary counts by sex and birth-year band; no age, sex-specific or
    death restriction. Not a SEER-comparable result.
    """
    return f"""
WITH roster AS (
  SELECT CAST(person_id AS INT64) AS person_id
  FROM UNNEST(SPLIT(@wgs_ids, '\\n')) AS person_id
),
mapping AS (
  SELECT
    JSON_VALUE(item, '$.cancer') AS cancer,
    CAST(JSON_VALUE(item, '$.concept_id') AS INT64) AS concept_id
  FROM UNNEST(JSON_QUERY_ARRAY(@mapping_json)) AS item
),
per_person AS (
  SELECT
    co.person_id,
    COUNT(DISTINCT co.condition_start_date) AS condition_dates,
    MIN(co.condition_start_date) AS first_condition_date,
    MAX(co.condition_start_date) AS last_condition_date,
    ARRAY_AGG(DISTINCT m.cancer IGNORE NULLS) AS cancers
  FROM `{CDR}.condition_occurrence` AS co
  JOIN roster USING (person_id)
  LEFT JOIN mapping AS m ON m.concept_id = co.condition_concept_id
  WHERE co.condition_start_date IS NOT NULL
  GROUP BY co.person_id
),
demographics AS (
  SELECT
    p.person_id,
    p.year_of_birth,
    c.concept_name AS sex_at_birth
  FROM `{CDR}.person` AS p
  JOIN roster USING (person_id)
  LEFT JOIN `{CDR}.concept` AS c
    ON c.concept_id = p.sex_at_birth_concept_id
)
SELECT
  d.sex_at_birth,
  CASE
    WHEN d.year_of_birth IS NULL THEN 'Missing birth year'
    WHEN d.year_of_birth < 1940 THEN 'Before 1940'
    WHEN d.year_of_birth < 1950 THEN '1940–1949'
    WHEN d.year_of_birth < 1960 THEN '1950–1959'
    WHEN d.year_of_birth < 1970 THEN '1960–1969'
    WHEN d.year_of_birth < 1980 THEN '1970–1979'
    WHEN d.year_of_birth < 1990 THEN '1980–1989'
    WHEN d.year_of_birth < 2000 THEN '1990–1999'
    ELSE '2000 or later'
  END AS birth_year_band,
  COUNT(*) AS participants_with_dated_condition,
  COUNTIF(e.condition_dates >= 2) AS participants_with_ge2_dates,
  MIN(e.first_condition_date) AS earliest_condition_date,
  MAX(e.last_condition_date) AS latest_condition_date,
  COUNTIF('breast' IN UNNEST(e.cancers)) AS breast,
  COUNTIF('prostate' IN UNNEST(e.cancers)) AS prostate,
  COUNTIF('colorectal' IN UNNEST(e.cancers)) AS colorectal,
  COUNTIF('melanoma' IN UNNEST(e.cancers)) AS melanoma,
  COUNTIF('lung' IN UNNEST(e.cancers)) AS lung,
  COUNTIF('kidney' IN UNNEST(e.cancers)) AS kidney,
  COUNTIF('ovarian' IN UNNEST(e.cancers)) AS ovarian,
  COUNTIF('pancreatic' IN UNNEST(e.cancers)) AS pancreatic,
  COUNTIF('stomach' IN UNNEST(e.cancers)) AS stomach
FROM per_person AS e
LEFT JOIN demographics AS d USING (person_id)
GROUP BY 1,2
ORDER BY 1,2
"""


def prevalence_v9_cutoff(CDR):
    """Codex msg 2594, 2026-10-21T15:57Z; executed with @reference_date
    2025-01-01 as job b51b114b-... (msg 2604). Diagnoses ON OR BEFORE the date.
    """
    cancer_counts_sql = ",\n".join(
        f"""COUNTIF('{cancer}' IN UNNEST(e.cancers)) AS {cancer},
    COUNTIF(
      '{cancer}' IN UNNEST(e.cancers) AND e.condition_dates >= 2
    ) AS {cancer}_ge2_dates"""
        for cancer in CANCERS
    )
    return f"""
WITH roster AS (
  SELECT CAST(person_id AS INT64) AS person_id
  FROM UNNEST(SPLIT(@wgs_ids, '\\n')) AS person_id
),
mapping AS (
  SELECT
    JSON_VALUE(item, '$.cancer') AS cancer,
    CAST(JSON_VALUE(item, '$.concept_id') AS INT64) AS concept_id
  FROM UNNEST(JSON_QUERY_ARRAY(@mapping_json)) AS item
),
per_person AS (
  SELECT
    co.person_id,
    COUNT(DISTINCT co.condition_start_date) AS condition_dates,
    ARRAY_AGG(DISTINCT m.cancer IGNORE NULLS) AS cancers
  FROM `{CDR}.condition_occurrence` AS co
  JOIN roster USING (person_id)
  LEFT JOIN mapping AS m ON m.concept_id = co.condition_concept_id
  WHERE co.condition_start_date <= @reference_date
  GROUP BY co.person_id
),
deaths AS (
  SELECT person_id, MIN(death_date) AS death_date
  FROM `{CDR}.aou_death`
  WHERE primary_death_record = TRUE
  GROUP BY person_id
),
demographics AS (
  SELECT
    r.person_id,
    DATE(p.birth_datetime) AS birth_date,
    c.concept_name AS sex_at_birth,
    d.death_date,
    DATE_DIFF(@reference_date, DATE(p.birth_datetime), YEAR)
      - IF(
          FORMAT_DATE('%m%d', @reference_date)
            < FORMAT_DATE('%m%d', DATE(p.birth_datetime)),
          1, 0
        ) AS age
  FROM roster AS r
  LEFT JOIN `{CDR}.person` AS p USING (person_id)
  LEFT JOIN `{CDR}.concept` AS c
    ON c.concept_id = p.sex_at_birth_concept_id
  LEFT JOIN deaths AS d USING (person_id)
),
classified AS (
  SELECT *,
    CASE
      WHEN birth_date IS NULL THEN 'missing_birth_date'
      WHEN age < 20 THEN 'under_20'
      WHEN death_date <= @reference_date THEN 'recorded_deceased_by_reference'
      ELSE 'adult_without_recorded_death_by_reference'
    END AS demographic_status,
    CASE
      WHEN age IS NULL THEN 'Missing'
      WHEN age < 20 THEN 'Under 20'
      WHEN age < 40 THEN '20–39'
      WHEN age < 50 THEN '40–49'
      WHEN age < 60 THEN '50–59'
      WHEN age < 70 THEN '60–69'
      WHEN age < 80 THEN '70–79'
      ELSE '80+'
    END AS age_band
  FROM demographics
)
SELECT
  d.demographic_status,
  d.sex_at_birth,
  d.age_band,
  COUNT(*) AS wgs_participants,
  COUNTIF(e.person_id IS NOT NULL) AS primary_coverage_denominator,
  COUNTIF(e.condition_dates >= 2) AS sensitivity_coverage_denominator,
  {cancer_counts_sql}
FROM classified AS d
LEFT JOIN per_person AS e USING (person_id)
GROUP BY 1,2,3
ORDER BY 1,2,3
"""


OLD_AGE_CASE = """CASE
      WHEN age IS NULL THEN 'Missing'
      WHEN age < 20 THEN 'Under 20'
      WHEN age < 40 THEN '20–39'
      WHEN age < 50 THEN '40–49'
      WHEN age < 60 THEN '50–59'
      WHEN age < 70 THEN '60–69'
      WHEN age < 80 THEN '70–79'
      ELSE '80+'
    END AS age_band"""

NEW_AGE_CASE = """CASE
      WHEN age IS NULL THEN 'Missing'
      WHEN age < 20 THEN 'Under 20'
      WHEN age < 40 THEN '20–39'
      WHEN age < 65 THEN '40–64'
      WHEN age < 75 THEN '65–74'
      ELSE '75+'
    END AS age_band"""


def prevalence_seer_aligned(CDR):
    """Codex msg 2725, 2026-10-21T16:16Z; executed with @reference_date
    2023-01-01 as job 7645e039-... (msg 2735). Diagnoses STRICTLY BEFORE the
    date, SEER-compatible bands. Derived from the 2025 query exactly as then.
    """
    prevalence_query = prevalence_v9_cutoff(CDR)
    assert prevalence_query.count(OLD_AGE_CASE) == 1
    assert prevalence_query.count(
        "co.condition_start_date <= @reference_date"
    ) == 1
    return prevalence_query.replace(
        OLD_AGE_CASE, NEW_AGE_CASE
    ).replace(
        "co.condition_start_date <= @reference_date",
        "co.condition_start_date < @reference_date",
    )


def cancer_date_sensitivity(CDR):
    """Codex msg 3187, 2026-10-22T14:23Z; executed as job 4ee8fb8a-... (msg 3199).

    Numerator sensitivity: >=2 distinct dates within the same cancer group.
    The denominator is NOT computed here; it is the fixed primary denominator
    from the saved 2023 comparison.
    """
    return f"""
WITH roster AS (
  SELECT CAST(person_id AS INT64) AS person_id
  FROM UNNEST(SPLIT(@wgs_ids, '\\n')) AS person_id
),
mapping AS (
  SELECT
    JSON_VALUE(item, '$.cancer') AS cancer,
    CAST(JSON_VALUE(item, '$.concept_id') AS INT64) AS concept_id
  FROM UNNEST(JSON_QUERY_ARRAY(@mapping_json)) AS item
),
cancer_dates AS (
  SELECT
    co.person_id,
    m.cancer,
    COUNT(DISTINCT co.condition_start_date) AS distinct_cancer_dates
  FROM `{CDR}.condition_occurrence` AS co
  JOIN roster USING (person_id)
  JOIN mapping AS m ON m.concept_id = co.condition_concept_id
  WHERE co.condition_start_date < @reference_date
  GROUP BY 1,2
),
deaths AS (
  SELECT person_id, MIN(death_date) AS death_date
  FROM `{CDR}.aou_death`
  WHERE primary_death_record = TRUE
  GROUP BY person_id
),
demographics AS (
  SELECT
    r.person_id,
    c.concept_name AS sex_at_birth,
    DATE_DIFF(@reference_date, DATE(p.birth_datetime), YEAR)
      - IF(
          FORMAT_DATE('%m%d', @reference_date)
            < FORMAT_DATE('%m%d', DATE(p.birth_datetime)),
          1, 0
        ) AS age,
    d.death_date
  FROM roster AS r
  LEFT JOIN `{CDR}.person` AS p USING (person_id)
  LEFT JOIN `{CDR}.concept` AS c
    ON c.concept_id = p.sex_at_birth_concept_id
  LEFT JOIN deaths AS d USING (person_id)
)
SELECT
  h.cancer,
  d.sex_at_birth,
  CASE
    WHEN d.age < 65 THEN '40–64'
    WHEN d.age < 75 THEN '65–74'
    ELSE '75+'
  END AS age_band,
  COUNT(*) AS cases_ge1_cancer_date,
  COUNTIF(h.distinct_cancer_dates >= 2) AS cases_ge2_cancer_dates,
  COUNTIF(h.distinct_cancer_dates = 1) AS cases_exactly1_cancer_date
FROM cancer_dates AS h
JOIN demographics AS d USING (person_id)
WHERE d.age >= 40
  AND (d.death_date IS NULL OR d.death_date > @reference_date)
  AND d.sex_at_birth IN ('Female', 'Male')
  AND (h.cancer != 'breast' OR d.sex_at_birth = 'Female')
  AND (h.cancer != 'prostate' OR d.sex_at_birth = 'Male')
  AND (h.cancer != 'ovarian' OR d.sex_at_birth = 'Female')
GROUP BY 1,2,3
ORDER BY 1,2,3
"""


def ovarian_scope(CDR):
    """Codex msg 3305, 2026-10-22T14:38Z; executed as job 6b7200ee-... (msg 3317).

    The concept-ID arrays were literals in the historical cell; here they are
    query parameters filled from the external OVARY_SCOPE_MAPPING file so the
    private mapping is not embedded in source code. Query text is unchanged.
    """
    return f"""
WITH roster AS (
  SELECT CAST(person_id AS INT64) AS person_id
  FROM UNNEST(SPLIT(@wgs_ids, '\\n')) AS person_id
),
evidence AS (
  SELECT
    co.person_id,
    COUNT(DISTINCT co.condition_start_date) AS original_dates,
    COUNT(DISTINCT IF(
      co.condition_concept_id IN UNNEST(@ovary_ids),
      co.condition_start_date, NULL
    )) AS ovarian_dates,
    COUNTIF(co.condition_concept_id IN UNNEST(@fallopian_ids)) AS fallopian_rows,
    COUNTIF(co.condition_concept_id = @adnexal_id) AS adnexal_rows,
    COUNTIF(co.condition_concept_id = @lesion_id) AS lesion_rows
  FROM `{CDR}.condition_occurrence` AS co
  JOIN roster USING (person_id)
  WHERE co.condition_concept_id IN UNNEST(@original_ids)
    AND co.condition_start_date < @reference_date
  GROUP BY person_id
),
deaths AS (
  SELECT person_id, MIN(death_date) AS death_date
  FROM `{CDR}.aou_death`
  WHERE primary_death_record = TRUE
  GROUP BY person_id
),
demographics AS (
  SELECT
    p.person_id,
    c.concept_name AS sex_at_birth,
    DATE_DIFF(@reference_date, DATE(p.birth_datetime), YEAR)
      - IF(
          FORMAT_DATE('%m%d', @reference_date)
            < FORMAT_DATE('%m%d', DATE(p.birth_datetime)),
          1, 0
        ) AS age,
    d.death_date
  FROM `{CDR}.person` AS p
  JOIN roster USING (person_id)
  LEFT JOIN `{CDR}.concept` AS c
    ON c.concept_id = p.sex_at_birth_concept_id
  LEFT JOIN deaths AS d USING (person_id)
)
SELECT
  CASE
    WHEN d.age < 65 THEN '40–64'
    WHEN d.age < 75 THEN '65–74'
    ELSE '75+'
  END AS age_band,
  COUNT(*) AS original_cases,
  COUNTIF(e.original_dates >= 2) AS original_cases_ge2_cancer_dates,
  COUNTIF(e.ovarian_dates > 0) AS explicitly_ovarian_cases,
  COUNTIF(e.ovarian_dates >= 2) AS explicitly_ovarian_cases_ge2_dates,
  COUNTIF(e.ovarian_dates = 0) AS without_explicit_ovarian_evidence,
  COUNTIF(
    e.ovarian_dates = 0 AND e.fallopian_rows > 0
  ) AS no_ovarian_with_fallopian_cancer,
  COUNTIF(
    e.ovarian_dates = 0 AND e.fallopian_rows = 0
    AND e.adnexal_rows > 0
  ) AS no_ovarian_or_fallopian_with_adnexal_cancer,
  COUNTIF(
    e.ovarian_dates = 0 AND e.fallopian_rows = 0
    AND e.adnexal_rows = 0 AND e.lesion_rows > 0
  ) AS lesion_only
FROM evidence AS e
JOIN demographics AS d USING (person_id)
WHERE d.sex_at_birth = 'Female'
  AND d.age >= 40
  AND (d.death_date IS NULL OR d.death_date > @reference_date)
GROUP BY 1
ORDER BY 1
"""
