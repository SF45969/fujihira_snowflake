{{ config(materialized='view') }}

SELECT
    COMPANY_CD,
    COMPANY_NM,
    '{{ var("load_date") }}'::DATE AS LOAD_DATE,
    'COMPANY' AS RECORD_SOURCE
FROM {{ source('raw', 'COMPANY') }}
