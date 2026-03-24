# dbt_datavault_ah プロジェクト構築サマリー

## 概要

Snowflake Workspace 上で dbt + automate_dv（Data Vault 2.0）を用いた Data Vault プロジェクトを構築した。
ソースデータ（社員・組織・取引先・売上）から Hub / Link / Satellite / T-Link を自動生成している。

---

## 1. Snowflake インフラストラクチャ

### Database

| オブジェクト | 説明 |
|------------|------|
| `S45969_DBT_DB` | dbt プロジェクト用データベース |

### Schema

| スキーマ | 用途 |
|---------|------|
| `S45969_DBT_DB.S45969_DBT_RAW` | ソースデータ（生テーブル）格納先 |
| `S45969_DBT_DB.S45969_DBT_SCHEMA` | DBT PROJECT オブジェクト格納先 |
| `S45969_DBT_DB.S45969_DBT_AH_SCHEMA` | dbt run で生成された Data Vault テーブル/ビューの格納先 |
| `S45969_DBT_DB.PUBLIC` | Network Rule 格納先 |

### Warehouse

| オブジェクト | サイズ | 説明 |
|------------|--------|------|
| `S45969_DBT_WH` | X-Small | dbt 実行用ウェアハウス（AUTO_SUSPEND=60s） |

### Role / 権限

| オブジェクト | 説明 |
|------------|------|
| `S45969_DBT_ROLE` | dbt 実行用ロール。ユーザー `SYS_45969` に付与済み |

付与済み権限:
- `S45969_DBT_DB` への USAGE
- `S45969_DBT_SCHEMA`, `S45969_DBT_AH_SCHEMA` への USAGE / ALL
- `S45969_DBT_RAW` への USAGE / SELECT（全テーブル）
- `S45969_DBT_WH` への USAGE

---

## 2. External Access（外部アクセス）

dbt deps（パッケージ取得）を Snowflake 上で実行するために作成。

| オブジェクト | 種類 | 説明 |
|------------|------|------|
| `S45969_DBT_DB.PUBLIC.S45969_DBT_NETWORK_RULE` | Network Rule | `hub.getdbt.com`, `codeload.github.com` への EGRESS を許可 |
| `S45969_DBT_EXT_ACCESS` | External Access Integration | 上記 Network Rule を束ねた Integration |

---

## 3. DBT PROJECT オブジェクト

| オブジェクト | 説明 |
|------------|------|
| `S45969_DBT_DB.S45969_DBT_SCHEMA.AH_DBT_TEST` | dbt_datavault_ah の Deploy 先。External Access Integration 紐づけ済み |

実行方法:
```sql
-- Workspace の Connect → Execute dbt project から実行
-- Args: run --target dev
```

---

## 4. ソーステーブル（S45969_DBT_RAW）

| テーブル | 行数 | 説明 |
|---------|------|------|
| `EMPLOYEE` | 5 | 社員テーブル（EMP_CD, EMP_NM, SEX, BIRTHDAY, ENTRY_DATE） |
| `ORGANIZATION` | 3 | 組織テーブル（ORG_CD, ORG_NM） |
| `EMPLOYEE_ORGANIZATION` | 5 | 社員所属テーブル（EMP_CD, ORG_CD） |
| `COMPANY` | 3 | 取引先テーブル（COMPANY_CD, COMPANY_NM） |
| `SALES` | 8 | 売上テーブル（EMP_CD, COMPANY_CD, SALES_MONTH, SALES_AMT） |

---

## 5. dbt モデル構成（S45969_DBT_AH_SCHEMA）

### 5.1 Raw Stage（VIEW）— ソースから LOAD_DATE, RECORD_SOURCE を付与

| モデル | ソーステーブル |
|--------|------------|
| `RAW_COMPANY` | COMPANY |
| `RAW_EMPLOYEE` | EMPLOYEE |
| `RAW_ORGANIZATION` | ORGANIZATION |
| `RAW_EMPLOYEE_ORGANIZATION` | EMPLOYEE_ORGANIZATION |
| `RAW_SALES` | SALES |

### 5.2 Stage（VIEW）— ハッシュキー・HASHDIFF を生成

| モデル | 元モデル |
|--------|---------|
| `V_STG_COMPANY` | raw_company |
| `V_STG_EMPLOYEE` | raw_employee |
| `V_STG_ORGANIZATION` | raw_organization |
| `V_STG_EMPLOYEE_ORGANIZATION` | raw_employee_organization |
| `V_STG_SALES` | raw_sales |

### 5.3 Hub（TABLE / incremental）— ビジネスキーを一意に蓄積

| モデル | ビジネスキー |
|--------|-----------|
| `HUB_COMPANY` | COMPANY_CD |
| `HUB_EMPLOYEE` | EMP_CD |
| `HUB_ORGANIZATION` | ORG_CD |

### 5.4 Link（TABLE / incremental）— エンティティ間の関係を記録

| モデル | 関係 |
|--------|------|
| `LINK_EMP_ORG` | 社員 ↔ 組織 |
| `LINK_EMP_COMPANY_SALES` | 社員 ↔ 取引先（売上経由） |

### 5.5 Satellite（TABLE / incremental）— 属性データの変更履歴

| モデル | 対象 |
|--------|------|
| `SAT_COMPANY` | 取引先の属性（COMPANY_NM） |
| `SAT_EMPLOYEE` | 社員の属性（EMP_NM, SEX, BIRTHDAY, ENTRY_DATE） |
| `SAT_ORGANIZATION` | 組織の属性（ORG_NM） |

### 5.6 T-Link（TABLE / incremental）— トランザクションデータ

| モデル | 説明 |
|--------|------|
| `T_LINK_SALES` | 売上トランザクション（EMP_CD, COMPANY_CD, SALES_MONTH, SALES_AMT） |

---

## 6. dbt プロジェクトファイル構成

```
dbt_datavault_ah/
├── dbt_project.yml          # プロジェクト定義
├── profiles.yml             # Snowflake 接続情報（target: dev）
├── packages.yml             # automate_dv 0.9.7
├── dbt_packages/            # dbt deps で取得されたパッケージ
├── models/
│   ├── schema.yml           # ソース定義（S45969_DBT_RAW）
│   ├── raw_stage/           # Raw Stage ビュー（5モデル）
│   ├── stage/               # Stage ビュー（5モデル）
│   └── raw_vault/
│       ├── hubs/            # Hub テーブル（3モデル）
│       ├── links/           # Link テーブル（2モデル）
│       ├── sats/            # Satellite テーブル（3モデル）
│       └── t_links/         # T-Link テーブル（1モデル）
└── logs/
```

---

## 7. 構築時のポイント・注意事項

1. **dbt プロジェクト名は英字始まり** — `45969_dbt_vault` はエラーになるため `s45969_dbt_vault` に変更
2. **profiles.yml に `password` / `env_var()` は不要** — Snowflake 内部で実行されるため
3. **dbt deps の実行** — External Access Integration を設定するか、ローカルで実行して Git 経由で反映
4. **dev/prod のスキーマ分離** — 複数プロジェクトが同じスキーマを使うと上書きリスクあり
5. **Workspace の変更は Redeploy が必要** — Deploy 後に profiles.yml 等を変更した場合、Redeploy しないと反映されない
