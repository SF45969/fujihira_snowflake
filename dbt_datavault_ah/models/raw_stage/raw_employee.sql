{{ config(materialized='view') }}

SELECT
    EMP_CD,
    EMP_NM,
    SEX,
    BIRTHDAY,
    ENTRY_DATE,
    '{{ var("load_date") }}'::DATE AS LOAD_DATE,
    'EMPLOYEE' AS RECORD_SOURCE
FROM {{ source('raw', 'EMPLOYEE') }}
