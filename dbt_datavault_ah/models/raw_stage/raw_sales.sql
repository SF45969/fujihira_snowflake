{{ config(materialized='view') }}

SELECT
    EMP_CD,
    COMPANY_CD,
    SALES_MONTH,
    SALES_AMT,
    '{{ var("load_date") }}'::DATE AS LOAD_DATE,
    'SALES' AS RECORD_SOURCE
FROM {{ source('raw', 'SALES') }}
