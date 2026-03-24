{{ config(materialized='view') }}

{%- set yaml_metadata -%}
source_model: 'raw_employee_organization'
derived_columns:
  RECORD_SOURCE: 'RECORD_SOURCE'
  LOAD_DATE: 'LOAD_DATE'
  EFFECTIVE_FROM: 'LOAD_DATE'
hashed_columns:
  EMPLOYEE_PK: 'EMP_CD'
  ORGANIZATION_PK: 'ORG_CD'
  LINK_EMP_ORG_PK:
    - 'EMP_CD'
    - 'ORG_CD'
{%- endset -%}

{% set metadata_dict = fromyaml(yaml_metadata) %}

{{ automate_dv.stage(include_source_columns=true,
                     source_model=metadata_dict['source_model'],
                     derived_columns=metadata_dict['derived_columns'],
                     hashed_columns=metadata_dict['hashed_columns'],
                     ranked_columns=none) }}
