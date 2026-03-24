{%- set source_model = "v_stg_employee_organization" -%}
{%- set src_pk = "LINK_EMP_ORG_PK" -%}
{%- set src_fk = ["EMPLOYEE_PK", "ORGANIZATION_PK"] -%}
{%- set src_ldts = "LOAD_DATE" -%}
{%- set src_source = "RECORD_SOURCE" -%}

{{ automate_dv.link(src_pk=src_pk, src_fk=src_fk, src_ldts=src_ldts,
                    src_source=src_source, source_model=source_model) }}
