# dbt_datavault_ah モデル定義書

## データフロー概要

```
S45969_DBT_RAW（ソース）
  │
  ▼
raw_stage（VIEW）── ソースに LOAD_DATE, RECORD_SOURCE を付与
  │
  ▼
stage（VIEW）── ハッシュキー（PK）、HASHDIFF を自動生成
  │
  ▼
raw_vault（TABLE / incremental）── Data Vault 本体（Hub / Link / Sat / T-Link）
```

---

## ソース定義（schema.yml）

データベース: `S45969_DBT_DB` / スキーマ: `S45969_DBT_RAW`

| ソーステーブル | 説明 | カラム |
|-------------|------|--------|
| EMPLOYEE | 社員テーブル | EMP_CD, EMP_NM, SEX, BIRTHDAY, ENTRY_DATE |
| ORGANIZATION | 組織テーブル | ORG_CD, ORG_NM |
| EMPLOYEE_ORGANIZATION | 社員所属テーブル | EMP_CD, ORG_CD |
| COMPANY | 取引先テーブル | COMPANY_CD, COMPANY_NM |
| SALES | 売上テーブル | EMP_CD, COMPANY_CD, SALES_MONTH, SALES_AMT |

---

## 1. raw_stage（VIEW）

ソーステーブルのカラムをそのまま SELECT し、Data Vault 共通のメタデータ列を追加する。

- `LOAD_DATE`: `var("load_date")`（dbt_project.yml で `2026-03-24` に設定）
- `RECORD_SOURCE`: ソーステーブル名を固定文字列で付与

### raw_company.sql

```sql
{{ config(materialized='view') }}

SELECT
    COMPANY_CD,
    COMPANY_NM,
    '{{ var("load_date") }}'::DATE AS LOAD_DATE,
    'COMPANY' AS RECORD_SOURCE
FROM {{ source('raw', 'COMPANY') }}
```

### raw_employee.sql

```sql
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
```

### raw_organization.sql

```sql
{{ config(materialized='view') }}

SELECT
    ORG_CD,
    ORG_NM,
    '{{ var("load_date") }}'::DATE AS LOAD_DATE,
    'ORGANIZATION' AS RECORD_SOURCE
FROM {{ source('raw', 'ORGANIZATION') }}
```

### raw_employee_organization.sql

```sql
{{ config(materialized='view') }}

SELECT
    EMP_CD,
    ORG_CD,
    '{{ var("load_date") }}'::DATE AS LOAD_DATE,
    'EMPLOYEE_ORGANIZATION' AS RECORD_SOURCE
FROM {{ source('raw', 'EMPLOYEE_ORGANIZATION') }}
```

### raw_sales.sql

```sql
{{ config(materialized='view') }}

SELECT
    EMP_CD,
    COMPANY_CD,
    SALES_MONTH,
    SALES_AMT,
    '{{ var("load_date") }}'::DATE AS LOAD_DATE,
    'SALES' AS RECORD_SOURCE
FROM {{ source('raw', 'SALES') }}
```

---

## 2. stage（VIEW）

`automate_dv.stage()` マクロで raw_stage のデータに以下を自動生成する。

- **ハッシュキー（PK）**: ビジネスキーの MD5 ハッシュ → Hub / Link の主キーになる
- **HASHDIFF**: 属性列のハッシュ → Satellite で変更検知に使う
- **EFFECTIVE_FROM**: 有効開始日（= LOAD_DATE）

### v_stg_company.sql

```sql
{{ config(materialized='view') }}

{%- set yaml_metadata -%}
source_model: 'raw_company'
derived_columns:
  RECORD_SOURCE: 'RECORD_SOURCE'
  LOAD_DATE: 'LOAD_DATE'
  EFFECTIVE_FROM: 'LOAD_DATE'
hashed_columns:
  COMPANY_PK: 'COMPANY_CD'
  COMPANY_HASHDIFF:
    is_hashdiff: true
    columns:
      - 'COMPANY_NM'
{%- endset -%}

{% set metadata_dict = fromyaml(yaml_metadata) %}

{{ automate_dv.stage(include_source_columns=true,
                     source_model=metadata_dict['source_model'],
                     derived_columns=metadata_dict['derived_columns'],
                     hashed_columns=metadata_dict['hashed_columns'],
                     ranked_columns=none) }}
```

| 生成列 | 元カラム | 用途 |
|--------|---------|------|
| COMPANY_PK | COMPANY_CD | Hub の主キー |
| COMPANY_HASHDIFF | COMPANY_NM | Satellite の変更検知 |

### v_stg_employee.sql

```sql
{{ config(materialized='view') }}

{%- set yaml_metadata -%}
source_model: 'raw_employee'
derived_columns:
  RECORD_SOURCE: 'RECORD_SOURCE'
  LOAD_DATE: 'LOAD_DATE'
  EFFECTIVE_FROM: 'LOAD_DATE'
hashed_columns:
  EMPLOYEE_PK: 'EMP_CD'
  EMPLOYEE_HASHDIFF:
    is_hashdiff: true
    columns:
      - 'EMP_NM'
      - 'SEX'
      - 'BIRTHDAY'
{%- endset -%}

{% set metadata_dict = fromyaml(yaml_metadata) %}

{{ automate_dv.stage(include_source_columns=true,
                     source_model=metadata_dict['source_model'],
                     derived_columns=metadata_dict['derived_columns'],
                     hashed_columns=metadata_dict['hashed_columns'],
                     ranked_columns=none) }}
```

| 生成列 | 元カラム | 用途 |
|--------|---------|------|
| EMPLOYEE_PK | EMP_CD | Hub の主キー |
| EMPLOYEE_HASHDIFF | EMP_NM, SEX, BIRTHDAY | Satellite の変更検知 |

### v_stg_organization.sql

```sql
{{ config(materialized='view') }}

{%- set yaml_metadata -%}
source_model: 'raw_organization'
derived_columns:
  RECORD_SOURCE: 'RECORD_SOURCE'
  LOAD_DATE: 'LOAD_DATE'
  EFFECTIVE_FROM: 'LOAD_DATE'
hashed_columns:
  ORGANIZATION_PK: 'ORG_CD'
  ORGANIZATION_HASHDIFF:
    is_hashdiff: true
    columns:
      - 'ORG_NM'
{%- endset -%}

{% set metadata_dict = fromyaml(yaml_metadata) %}

{{ automate_dv.stage(include_source_columns=true,
                     source_model=metadata_dict['source_model'],
                     derived_columns=metadata_dict['derived_columns'],
                     hashed_columns=metadata_dict['hashed_columns'],
                     ranked_columns=none) }}
```

| 生成列 | 元カラム | 用途 |
|--------|---------|------|
| ORGANIZATION_PK | ORG_CD | Hub の主キー |
| ORGANIZATION_HASHDIFF | ORG_NM | Satellite の変更検知 |

### v_stg_employee_organization.sql

```sql
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
```

| 生成列 | 元カラム | 用途 |
|--------|---------|------|
| EMPLOYEE_PK | EMP_CD | Link の FK |
| ORGANIZATION_PK | ORG_CD | Link の FK |
| LINK_EMP_ORG_PK | EMP_CD + ORG_CD | Link の主キー（複合ハッシュ） |

### v_stg_sales.sql

```sql
{{ config(materialized='view') }}

{%- set yaml_metadata -%}
source_model: 'raw_sales'
derived_columns:
  RECORD_SOURCE: 'RECORD_SOURCE'
  LOAD_DATE: 'LOAD_DATE'
  EFFECTIVE_FROM: 'LOAD_DATE'
hashed_columns:
  EMPLOYEE_PK: 'EMP_CD'
  COMPANY_PK: 'COMPANY_CD'
  LINK_EMP_COMPANY_SALES_PK:
    - 'EMP_CD'
    - 'COMPANY_CD'
    - 'SALES_MONTH'
{%- endset -%}

{% set metadata_dict = fromyaml(yaml_metadata) %}

{{ automate_dv.stage(include_source_columns=true,
                     source_model=metadata_dict['source_model'],
                     derived_columns=metadata_dict['derived_columns'],
                     hashed_columns=metadata_dict['hashed_columns'],
                     ranked_columns=none) }}
```

| 生成列 | 元カラム | 用途 |
|--------|---------|------|
| EMPLOYEE_PK | EMP_CD | T-Link の FK |
| COMPANY_PK | COMPANY_CD | T-Link の FK |
| LINK_EMP_COMPANY_SALES_PK | EMP_CD + COMPANY_CD + SALES_MONTH | T-Link の主キー（複合ハッシュ） |

---

## 3. raw_vault（TABLE / incremental）

`dbt_project.yml` で `+materialized: incremental` に設定。
automate_dv のマクロにより、既存データとの重複を排除して新規レコードのみ INSERT される。

### 3.1 Hub — ビジネスキーの一意リスト

`automate_dv.hub()` マクロ: 既に存在する PK は INSERT しない。

#### hub_company.sql

```sql
{%- set source_model = "v_stg_company" -%}
{%- set src_pk = "COMPANY_PK" -%}
{%- set src_nk = "COMPANY_CD" -%}
{%- set src_ldts = "LOAD_DATE" -%}
{%- set src_source = "RECORD_SOURCE" -%}

{{ automate_dv.hub(src_pk=src_pk, src_nk=src_nk, src_ldts=src_ldts,
                   src_source=src_source, source_model=source_model) }}
```

| パラメータ | 値 | 説明 |
|-----------|-----|------|
| src_pk | COMPANY_PK | ハッシュキー（主キー） |
| src_nk | COMPANY_CD | ナチュラルキー（ビジネスキー） |
| src_ldts | LOAD_DATE | ロード日時 |
| src_source | RECORD_SOURCE | データソース識別子 |

#### hub_employee.sql

| パラメータ | 値 |
|-----------|-----|
| src_pk | EMPLOYEE_PK |
| src_nk | EMP_CD |
| source_model | v_stg_employee |

#### hub_organization.sql

| パラメータ | 値 |
|-----------|-----|
| src_pk | ORGANIZATION_PK |
| src_nk | ORG_CD |
| source_model | v_stg_organization |

### 3.2 Link — エンティティ間の関係

`automate_dv.link()` マクロ: Hub 同士の関係を記録。FK は各 Hub の PK を参照。

#### link_emp_org.sql

```sql
{%- set source_model = "v_stg_employee_organization" -%}
{%- set src_pk = "LINK_EMP_ORG_PK" -%}
{%- set src_fk = ["EMPLOYEE_PK", "ORGANIZATION_PK"] -%}
{%- set src_ldts = "LOAD_DATE" -%}
{%- set src_source = "RECORD_SOURCE" -%}

{{ automate_dv.link(src_pk=src_pk, src_fk=src_fk, src_ldts=src_ldts,
                    src_source=src_source, source_model=source_model) }}
```

| パラメータ | 値 | 説明 |
|-----------|-----|------|
| src_pk | LINK_EMP_ORG_PK | Link のハッシュキー（EMP_CD + ORG_CD の複合） |
| src_fk | EMPLOYEE_PK, ORGANIZATION_PK | 参照する Hub の PK |

#### link_emp_company_sales.sql

| パラメータ | 値 |
|-----------|-----|
| src_pk | LINK_EMP_COMPANY_SALES_PK |
| src_fk | EMPLOYEE_PK, COMPANY_PK |
| source_model | v_stg_sales |

### 3.3 Satellite — 属性の変更履歴

`automate_dv.sat()` マクロ: HASHDIFF が前回と異なる場合のみ新レコードを INSERT。

#### sat_company.sql

```sql
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
```

| パラメータ | 値 | 説明 |
|-----------|-----|------|
| src_pk | COMPANY_PK | 親 Hub の PK |
| src_hashdiff | COMPANY_HASHDIFF | 変更検知用ハッシュ |
| src_payload | COMPANY_NM | 追跡する属性列 |

#### sat_employee.sql

| パラメータ | 値 |
|-----------|-----|
| src_pk | EMPLOYEE_PK |
| src_hashdiff | EMPLOYEE_HASHDIFF |
| src_payload | EMP_NM, SEX, BIRTHDAY |
| source_model | v_stg_employee |

#### sat_organization.sql

| パラメータ | 値 |
|-----------|-----|
| src_pk | ORGANIZATION_PK |
| src_hashdiff | ORGANIZATION_HASHDIFF |
| src_payload | ORG_NM |
| source_model | v_stg_organization |

### 3.4 T-Link — トランザクションデータ

`automate_dv.t_link()` マクロ: Link + ペイロード（金額・日付等）を一体で記録。
通常の Link と異なり、同じ関係でも異なるトランザクションは別レコードとして保持。

#### t_link_sales.sql

```sql
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
```

| パラメータ | 値 | 説明 |
|-----------|-----|------|
| src_pk | LINK_EMP_COMPANY_SALES_PK | T-Link の PK（EMP_CD + COMPANY_CD + SALES_MONTH の複合ハッシュ） |
| src_fk | EMPLOYEE_PK, COMPANY_PK | 参照する Hub の PK |
| src_payload | SALES_MONTH, SALES_AMT | トランザクションデータ（ペイロード） |

---

## モデル一覧サマリー

| レイヤー | ファイル | 種別 | マテリアライズ | 概要 |
|---------|---------|------|-------------|------|
| raw_stage | raw_company.sql | VIEW | view | COMPANY に LOAD_DATE, RECORD_SOURCE を付与 |
| raw_stage | raw_employee.sql | VIEW | view | EMPLOYEE に LOAD_DATE, RECORD_SOURCE を付与 |
| raw_stage | raw_organization.sql | VIEW | view | ORGANIZATION に LOAD_DATE, RECORD_SOURCE を付与 |
| raw_stage | raw_employee_organization.sql | VIEW | view | EMPLOYEE_ORGANIZATION に LOAD_DATE, RECORD_SOURCE を付与 |
| raw_stage | raw_sales.sql | VIEW | view | SALES に LOAD_DATE, RECORD_SOURCE を付与 |
| stage | v_stg_company.sql | VIEW | view | COMPANY_PK, COMPANY_HASHDIFF を生成 |
| stage | v_stg_employee.sql | VIEW | view | EMPLOYEE_PK, EMPLOYEE_HASHDIFF を生成 |
| stage | v_stg_organization.sql | VIEW | view | ORGANIZATION_PK, ORGANIZATION_HASHDIFF を生成 |
| stage | v_stg_employee_organization.sql | VIEW | view | EMPLOYEE_PK, ORGANIZATION_PK, LINK_EMP_ORG_PK を生成 |
| stage | v_stg_sales.sql | VIEW | view | EMPLOYEE_PK, COMPANY_PK, LINK_EMP_COMPANY_SALES_PK を生成 |
| raw_vault/hubs | hub_company.sql | TABLE | incremental | 取引先のビジネスキー（COMPANY_CD）を一意に蓄積 |
| raw_vault/hubs | hub_employee.sql | TABLE | incremental | 社員のビジネスキー（EMP_CD）を一意に蓄積 |
| raw_vault/hubs | hub_organization.sql | TABLE | incremental | 組織のビジネスキー（ORG_CD）を一意に蓄積 |
| raw_vault/links | link_emp_org.sql | TABLE | incremental | 社員 ↔ 組織の関係を記録 |
| raw_vault/links | link_emp_company_sales.sql | TABLE | incremental | 社員 ↔ 取引先の関係を記録 |
| raw_vault/sats | sat_company.sql | TABLE | incremental | 取引先の属性変更履歴（COMPANY_NM） |
| raw_vault/sats | sat_employee.sql | TABLE | incremental | 社員の属性変更履歴（EMP_NM, SEX, BIRTHDAY） |
| raw_vault/sats | sat_organization.sql | TABLE | incremental | 組織の属性変更履歴（ORG_NM） |
| raw_vault/t_links | t_link_sales.sql | TABLE | incremental | 売上トランザクション（SALES_MONTH, SALES_AMT） |
