{%- set source_model = "v_stg_sales" -%}
{%- set src_pk = "LINK_EMP_COMPANY_SALES_PK" -%}
{%- set src_fk = ["EMPLOYEE_PK", "COMPANY_PK"] -%}
{%- set src_payload = ["SALES_MONTH", "SALES_AMT"] -%}
{%- set src_eff = "EFFECTIVE_FROM" -%}
{%- set src_ldts = "LOAD_DATE" -%}
{%- set src_source = "RECORD_SOURCE" -%}

{{ automate_dv.t_link(src_pk=src_pk, src_fk=src_fk,
                      src_payload=src_payload, src_eff=src_eff,
                      src_ldts=src_ldts, src_source=src_source,
                      source_model=source_model) }}
