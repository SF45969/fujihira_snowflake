# この会話で実施した作業一覧

## 概要

dbt_datavault_ah プロジェクト（以前の会話で作成済み）を Snowflake 上で動かすために、
インフラ構築・設定修正・権限付与・トラブルシュートを実施した。

---

## 1. SQL 提案（ユーザーが手動実行）

以下の SQL を提案し、ユーザーが Snowflake 上で実行した。

### 1.1 Database / Schema / Warehouse / Role の作成

```sql
CREATE DATABASE IF NOT EXISTS S45969_DBT_DB;
CREATE SCHEMA IF NOT EXISTS S45969_DBT_DB.S45969_DBT_SCHEMA;
CREATE WAREHOUSE IF NOT EXISTS S45969_DBT_WH
  WAREHOUSE_SIZE = 'XSMALL' AUTO_SUSPEND = 60 AUTO_RESUME = TRUE;
CREATE ROLE IF NOT EXISTS S45969_DBT_ROLE;

GRANT USAGE ON DATABASE S45969_DBT_DB TO ROLE S45969_DBT_ROLE;
GRANT USAGE ON SCHEMA S45969_DBT_DB.S45969_DBT_SCHEMA TO ROLE S45969_DBT_ROLE;
GRANT ALL ON SCHEMA S45969_DBT_DB.S45969_DBT_SCHEMA TO ROLE S45969_DBT_ROLE;
GRANT USAGE ON WAREHOUSE S45969_DBT_WH TO ROLE S45969_DBT_ROLE;
GRANT ROLE S45969_DBT_ROLE TO USER SYS_45969;
```

### 1.2 スキーマ競合回避用スキーマの作成

```sql
CREATE SCHEMA IF NOT EXISTS S45969_DBT_DB.S45969_DBT_AH_SCHEMA;
GRANT ALL ON SCHEMA S45969_DBT_DB.S45969_DBT_AH_SCHEMA TO ROLE S45969_DBT_ROLE;
```

### 1.3 Git Integration の Secret 許可修正

```sql
ALTER API INTEGRATION S45969_GIT_INTEGRATION
  SET ALLOWED_AUTHENTICATION_SECRETS = (S45969_DBT_DB.PUBLIC."s45969_git_PAT");
```

---

## 2. Cortex Code が直接実行した SQL

### 2.1 Network Rule + External Access Integration の作成

```sql
CREATE OR REPLACE NETWORK RULE S45969_DBT_DB.PUBLIC.S45969_DBT_NETWORK_RULE
  MODE = EGRESS TYPE = HOST_PORT
  VALUE_LIST = ('hub.getdbt.com', 'codeload.github.com');

CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION S45969_DBT_EXT_ACCESS
  ALLOWED_NETWORK_RULES = (S45969_DBT_DB.PUBLIC.S45969_DBT_NETWORK_RULE)
  ENABLED = TRUE;
```

目的: Workspace 上で `dbt deps`（パッケージ取得）を実行可能にするため。

### 2.2 S45969_DBT_RAW スキーマへの権限付与

```sql
GRANT USAGE ON SCHEMA S45969_DBT_DB.S45969_DBT_RAW TO ROLE S45969_DBT_ROLE;
GRANT SELECT ON ALL TABLES IN SCHEMA S45969_DBT_DB.S45969_DBT_RAW TO ROLE S45969_DBT_ROLE;
```

目的: `dbt run` 時にソーステーブルを参照できるようにするため。

---

## 3. ファイル編集

### 3.1 `/45969_dbt_vault/dbt_project.yml`（別プロジェクト）

| 変更箇所 | 変更前 | 変更後 | 理由 |
|---------|--------|--------|------|
| `name` | `45969_dbt_vault` | `s45969_dbt_vault` | dbt プロジェクト名は英字始まり必須 |
| `profile` | `45969_dbt_vault` | `s45969_dbt_vault` | 同上 |
| `models` キー | `45969_dbt_vault:` | `s45969_dbt_vault:` | 同上 |

### 3.2 `/dbt_datavault_ah/profiles.yml`

| 変更箇所 | 変更前 | 変更後 | 理由 |
|---------|--------|--------|------|
| `schema` | `S45969_DBT_SCHEMA` | `S45969_DBT_AH_SCHEMA` | 他プロジェクトとのスキーマ競合回避 |

---

## 4. ファイル作成

| ファイル | 内容 |
|---------|------|
| `/dbt_datavault_ah_summary.md` | プロジェクト全体のサマリー資料（前回生成） |
| `/dbt_datavault_ah_work_log.md` | **このファイル**（作業ログ） |

---

## 5. トラブルシュート対応

| 問題 | 原因 | 解決策 |
|------|------|--------|
| `dbt_project.yml` で `does not match '^[^\d\W]\w*$'` | プロジェクト名が数字始まり | 先頭に `s` を付与 |
| `dbt deps` で `hub.getdbt.com` に接続不可 | External Access Integration 未設定 | Network Rule + Integration を作成 |
| `pip install` が Workspace で失敗 | Snowflake 上では pip は使えない | ローカルで仮想環境を作成して実行 |
| ローカルで `pip install -r requirements.txt` 失敗 | Python 3.12 と古いパッケージの非互換 | `pip install dbt-snowflake` のみで OK |
| `.gitignore` で `dbt_packages` が除外 | デフォルトの .gitignore 設定 | `git add -f` で強制追加 |
| Git push 時に author 不明 | git config 未設定 | `git config user.name/email` を設定 |
| Secret が見つからないエラー | 小文字で作成された Secret を大文字参照 | ダブルクォートで正確な名前を指定 |
| `dbt run` で Schema not authorized | `S45969_DBT_ROLE` に RAW スキーマの権限なし | USAGE + SELECT を GRANT |
| `dbt run` でテーブル未生成 | profiles.yml 変更後に Redeploy していない | Redeploy して再実行 |
| Workspace compile で deps エラー | Workspace は DBT PROJECT の Integration を使わない | Deploy → Execute で実行 |

---

## 6. ユーザーへのガイダンス

- dbt コマンド一覧（compile, run, test, build, deps 等）の説明
- Workspace での開発フロー（compile で確認 → Deploy → Execute）
- automate_dv マクロ（hub, bridge, as_of_date_window）の解説
- `dbt_packages` フォルダを Git に入れる方法 vs External Access Integration の比較
