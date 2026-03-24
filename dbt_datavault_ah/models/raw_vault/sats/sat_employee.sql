{%- set source_model = "v_stg_employee" -%}
{%- set src_pk = "EMPLOYEE_PK" -%}
{%- set src_hashdiff = "EMPLOYEE_HASHDIFF" -%}
{%- set src_payload = ["EMP_NM", "SEX", "BIRTHDAY"] -%}
{%- set src_eff = "EFFECTIVE_FROM" -%}
{%- set src_ldts = "LOAD_DATE" -%}
{%- set src_source = "RECORD_SOURCE" -%}

{{ automate_dv.sat(src_pk=src_pk, src_hashdiff=src_hashdiff,
                   src_payload=src_payload, src_eff=src_eff,
                   src_ldts=src_ldts, src_source=src_source,
                   source_model=source_model) }}
