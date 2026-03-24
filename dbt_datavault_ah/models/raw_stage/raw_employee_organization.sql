{{ config(materialized='view') }}

SELECT
    EMP_CD,
    ORG_CD,
    '{{ var("load_date") }}'::DATE AS LOAD_DATE,
    'EMPLOYEE_ORGANIZATION' AS RECORD_SOURCE
FROM {{ source('raw', 'EMPLOYEE_ORGANIZATION') }}
