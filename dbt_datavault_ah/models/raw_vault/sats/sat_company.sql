{%- set source_model = "v_stg_company" -%}
{%- set src_pk = "COMPANY_PK" -%}
{%- set src_hashdiff = "COMPANY_HASHDIFF" -%}
{%- set src_payload = ["COMPANY_NM"] -%}
{%- set src_eff = "EFFECTIVE_FROM" -%}
{%- set src_ldts = "LOAD_DATE" -%}
{%- set src_source = "RECORD_SOURCE" -%}

{{ automate_dv.sat(src_pk=src_pk, src_hashdiff=src_hashdiff,
                   src_payload=src_payload, src_eff=src_eff,
                   src_ldts=src_ldts, src_source=src_source,
                   source_model=source_model) }}
