{{ config(materialized='view') }}

SELECT
    ORG_CD,
    ORG_NM,
    '{{ var("load_date") }}'::DATE AS LOAD_DATE,
    'ORGANIZATION' AS RECORD_SOURCE
FROM {{ source('raw', 'ORGANIZATION') }}
