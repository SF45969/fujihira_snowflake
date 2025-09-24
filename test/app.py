################################
# Import python packages
################################
import streamlit as st
import pandas as pd
from snowflake.snowpark.context import get_active_session
from snowflake.cortex import Complete as CompleteText
from snowflake.core import Root
################################
################################
# 環境設定
################################
st.set_page_config(
    page_title="Data Catalog",
    layout="wide",
    initial_sidebar_state="auto"
    )

st.markdown(
    """
    <style>
        table {
            white-space:nowrap;
            font-size:14px;
            width: 100%;
        }

        th {
            text-align: left;
        }
        
        .table-container {
            max-height: 400px;
            overflow:scroll;
        }
        
    </style>
    """
, unsafe_allow_html=True)


################################
# セッション構築
################################
# Get the current credentials
session = get_active_session()

################################
# ロール別アクセス制御
################################
# roleの取得
role = session.get_current_role().replace('"', "")
if role in ("ACCOUNTADMIN", "SYSADMIN", "DIM_DCR_OWNER"):  # 全部見れてよいロール
    role = "developer"
elif "DCM" in role:
    role = "docomo_role"
elif "DIM003" in role:
    role = "dim003_role"
elif "DIM" in role:
    role = "dim_role"
elif "ITG" in role:
    role = "intage_role"
else:
    role = "other"
    st.error("別のロールを選択してください。")

db_dict = {
  "developer": {
    "選択しない": ["選択しない"],
    "DICEFORDIM": ["選択しない", "USER_DMTP_03"],
    "ITG_DATA_TO_DIM":["選択しない", "CM", "CODE", "DNA", "MP", "SUB"],
    "DIM_DATA": ["選択しない", "DI_PINK"],
    "PROCESSING": ["選択しない", "COM_DCR", "DCM_WRK", "DIM_PRC", "DIM_WRK", "ITG_WRK", "PUBLIC"],
    "DIM_DCR": ["選択しない", "PUBLIC"],
    "DCM_DATA": ["選択しない", "APP", "AREA", "BASIC", "IDPOS", "SEGMENT", "SERVICE_USE", "SETTLEMENT", "USER_DMTP_03"],
    "ITG_DATA": ["選択しない", "CM", "CODE", "DNA", "MP", "SUB"],
    "DI_SCHOP": ["選択しない", "COMMON", "DATALAKE", "DATAMART"]
  },
    "dim_role": {
    "選択しない": ["選択しない"],
    "DCM_DATA": ["選択しない", "APP", "AREA", "BASIC", "IDPOS", "SEGMENT", "SERVICE_USE", "SETTLEMENT"],
    "ITG_DATA":["選択しない", "CM", "CODE", "DNA", "MP", "SUB"],
    "DIM_DATA": ["選択しない", "DI_PINK"],
    "PROCESSING": ["選択しない", "COM_DCR", "DIM_PRC", "DIM_WRK"],
    "DICEFORDIM": ["選択しない", "USER_DMTP_03"]
    # "DIM_DCR": ["選択しない", "PUBLIC"],
    "dim003_role": {
    "選択しない": ["選択しない"],
    "DCM_DATA": ["選択しない", "APP", "AREA", "BASIC", "IDPOS", "SEGMENT", "SERVICE_USE", "SETTLEMENT"],
    "DIM_DATA": ["選択しない", "DI_PINK"],
    "DI_SCHOP": ["選択しない", "COMMON", "DATALAKE", "DATAMART"]
    }
  },
  "intage_role": {
    "選択しない": ["選択しない"],
    "DCM_DATA": ["選択しない", "APP", "AREA", "BASIC", "IDPOS", "SEGMENT", "SERVICE_USE", "SETTLEMENT"],
    "ITG_DATA":["選択しない", "CM", "CODE", "DNA", "MP", "SUB"],
    "DIM_DATA": ["選択しない", "DI_PINK"],
    "PROCESSING": ["選択しない", "ITG_WRK"],
    # "DIM_DCR": ["選択しない", "PUBLIC"]
  },
  "docomo_role":{
    "選択しない": ["選択しない"],
    "DCM_DATA": ["選択しない", "APP", "AREA", "BASIC", "IDPOS", "SEGMENT", "SERVICE_USE", "SETTLEMENT"],
    "ITG_DATA":["選択しない", "CM", "CODE", "DNA", "MP", "SUB"],
    "DIM_DATA": ["選択しない", "DI_PINK"],
    "PROCESSING": ["選択しない", "DCM_WRK"],
    # "DIM_DCR": ["選択しない", "PUBLIC"]
  },
  "other":{}
}

# マスキングカラムの設定
if role == "docomo_role":
    masking_columns = ["USER_ID", "CODE_ID", "MONITOR_CODE"]
elif role == "intage_role":
    masking_columns = ["CONTRACT_ID", "D_PT_NUMBER"]
else:
    masking_columns = []

################################
# 関数
################################
def get_table_query(db):
    """INFOMATION_SCHEMAからテーブル情報取得クエリ作成関数
    Args:
        db (Str): USE DATABASE dbだと上手く行かなかったので引数で渡す

    Returns:
        str: クエリ
    """
    query = (f"""
        SELECT
            T.TABLE_SCHEMA,
            T.TABLE_NAME,
            ---T.TABLE_TYPE,
            T.COMMENT AS TABLE_COMMENT,
            C.COLUMN_NAME,
            C.COMMENT AS COLUMN_COMMENT
        FROM
            {db}.INFORMATION_SCHEMA.TABLES T
            LEFT JOIN {db}.INFORMATION_SCHEMA.COLUMNS C ON T.TABLE_NAME = C.TABLE_NAME
            AND T.TABLE_SCHEMA = C.TABLE_SCHEMA
            AND T.TABLE_CATALOG = C.TABLE_CATALOG
        WHERE
            T.TABLE_SCHEMA != 'INFORMATION_SCHEMA'
        ORDER BY
            T.TABLE_NAME;
    """)
    return query


def display_and_get_table(df, db, schema):
    """テーブル一覧を表示し、選択したテーブル名を返す関数
    Args:
        df (DataFrame): テーブル一覧のデータフレーム
        db (str): データベース名
        schema(str): スキーマ名
    Returns:
        str: selectionしたテーブル名のリスト
    """
    # 整形
    df_filtered = df.drop(columns=['TABLE_SCHEMA', 'COLUMN_NAME', 'COLUMN_COMMENT'])
    df_filtered = df_filtered.drop_duplicates().reset_index(drop=True)

    # 詳細表示用のチェックボックス列を追加
    df_filtered["詳細表示"] = False

    # データフレームの表示設定
    edited_df = st.data_editor(
        df_filtered,
        column_config={
            "詳細表示": st.column_config.CheckboxColumn(label="詳細表示", default=False, width="small", help="選択するとカラム情報とプレビューが確認できます"),
            "TABLE_NAME": st.column_config.TextColumn(label="テーブル名", width="medium"),
            # "TABLE_TYPE": st.column_config.TextColumn(label="タイプ", width="small"),
            "TABLE_COMMENT": st.column_config.TextColumn(label="概要", width="large")
        },
        column_order=["詳細表示", "TABLE_NAME", "TABLE_TYPE", "TABLE_COMMENT"],
        key=f"{db}_{schema}",
        disabled=["TABLE_NAME", "TABLE_TYPE", "TABLE_COMMENT"],  # 編集不可の設定
        hide_index=True,
        use_container_width=True
    )

    # チェックされた行の処理
    selected_rows = edited_df.loc[edited_df["詳細表示"], 'TABLE_NAME']
    selected_table = selected_rows.to_frame().assign(DB=db, SCHEMA=schema)
    return selected_table


def filter_tables(df, keyword_search):
    """テーブル一覧からキーワードに基づいてフィルタリングを行う関数
    Args:
        df (DataFrame): テーブル一覧のデータフレーム
        keyword_search (str): キーワード検索に入力した文字列
    Returns:
        DataFrame: フィルター後のテーブル一覧
    """
    if keyword_search:  # キーワードがある場合はフィルタリング
        df_t_name = df[df['TABLE_NAME'].str.contains(keyword_search, case=False, na=False)]
        df_t_comment = df[df['TABLE_COMMENT'].str.contains(keyword_search, case=False, na=False)]
        df_c_name = df[df['COLUMN_NAME'].str.contains(keyword_search, case=False, na=False)]
        df_c_comment = df[df['COLUMN_COMMENT'].str.contains(keyword_search, case=False, na=False)]
        # 各検索結果をUNIONする
        return pd.concat([df_t_name, df_t_comment, df_c_name, df_c_comment])
    else:
        return df


def display_detail_info(table_input):
    """選択したテーブルの詳細情報を表示する関数
    Args:
        table_input(str): database.schema.tableの形式
    """
    try:
        # カラム情報の表示
        columns_details = session.sql(f"DESC TABLE {table_input}").collect()
        column_detail_df = pd.DataFrame(columns_details).loc[:, ["name", "type", "comment"]]

        st.caption(table_input.replace(".", " > "))
        st.markdown(F"###### カラム情報 ({len(column_detail_df)}件)")
        
        column_detail_df = column_detail_df.rename(columns={'name': 'カラム名', 'type': 'データタイプ', 'comment': '概要'})
        st.markdown('<div class="table-container">'+ column_detail_df.to_html(index=False) +'</div>',unsafe_allow_html=True)

        # データプレビュー
        st.write(" ")
        st.markdown("###### プレビュー")
        query = f"SELECT * FROM {table_input} WHERE RANDOM() < 0.001  LIMIT 10;"
        preview = pd.DataFrame(session.sql(query).collect())
        for col in masking_columns:
            if col in preview.columns:
                preview[col] = "***masked***"

        st.markdown('<div class="table-container">'+ preview.to_html(index=False) +'</div>',unsafe_allow_html=True)

    except Exception:
        st.error("テーブル情報取得中に問題が発生しました。")

################################
# chatbot構築
################################
def call_chatbot(key):

    chat_container = st.container(height=500)
    # セッション状態の初期化
    if "rag_messages" not in st.session_state:
        st.session_state.rag_messages = []
        st.session_state.rag_chat_history = ""

    root = Root(session)
    my_service = (root
    	.databases["PROCESSING"]
    	.schemas["APP_WRK"]
    	.cortex_search_services["TEST_CORTEX_SEARCH"]
    )
    # model =  left.selectbox("modelを選択", [ 'mistral-large2','llama3.1-70b','llama3.1-8b','mistral-7b',], key=f"model_{key}")
    # チャット履歴のクリア
    if st.button("チャット履歴をクリア", key=f"button_{key}"):
        st.session_state.rag_messages = []
        st.session_state.rag_chat_history = ""
        st.rerun()
    # チャット履歴の表示
    for message in st.session_state.rag_messages:
        with chat_container.chat_message(message["role"]):
            st.markdown(message["content"])
    #        if "relevant_docs" in message:
    #            st.write(relevant_docs)
    #            with st.expander("参考ドキュメント"):
    #                for doc in message["relevant_docs"]:
    #                   with chat_container.markdown(f"**description**: {doc['CHUNK_TEXT']}")
    # ユーザー入力の処理
    if prompt := st.chat_input("質問を入力してください", key=f"chat_input_{key}"):
        st.session_state.rag_messages.append({"role": "user", "content": prompt})
        st.session_state.rag_chat_history += f"User: {prompt}\n"
        with chat_container.chat_message("user"):
            st.markdown(prompt)
        try:
            search_response = my_service.search(
                query=prompt,
                columns=["DB_NAME", "SCHEMA_NAME", "CHUNK_TEXT", "TABLE_NAME"],
                limit=5
            )
            response_dict = search_response.to_dict()
            relevant_docs = response_dict["results"]
            context = "参考文書:\n"
            for doc in relevant_docs:
                db = doc.get("DB_NAME", "不明なDB")
                schema = doc.get("SCHEMA_NAME", "不明なスキーマ") 
                table = doc.get("TABLE_NAME", "不明なテーブル")
                chunk = doc.get("CHUNK_TEXT", "").strip()
                context += f"""
            database: 「{db}」
            schema: 「{schema}」
            table: 「{table}」
            semantic model:
            {chunk}
            ---
            """
            # Cortex Complete による応答生成
            prompt_template = f"""
    あなたは、Snowflake上のデータカタログアプリに搭載されたデータ探索の補助AIチャットボットです。

    以下に示す「文脈」には、各テーブルに関するSemanticModel（テーブルの用途、カラム、内容など）が含まれています。
    この情報を基に、ユーザーの質問に対して最も関連性の高いテーブルを特定し、
    以下の方針に従って、日本語で丁寧に文章形式で回答してください：

    - 回答には必ず、**データベース名・スキーマ名・テーブル名（形式: DB.SCHEMA.TABLE）**を明記してください。
    - 質問の意図から、関連しそうな**カラム名やその用途**にも触れてください（文脈に含まれている場合）。
    - 質問に直接該当するテーブルが複数ある場合は、用途の違いも簡潔に説明してください。
    -  わからない場合は、その旨を正直に伝えてください。

    【文脈】
    {context}

    【質問】
    {prompt}
    """
            complete_model = "mistral-large2"
            response = CompleteText(complete_model, prompt_template)

            # 応答の表示と履歴への追加
            with chat_container.chat_message("assistant"):
                st.markdown(response)
        #            with st.expander("参考ドキュメント"):
        #                for doc in relevant_docs:
        #                    st.markdown(f"**description**: {doc['CHUNK_TEXT']}")

            st.session_state.rag_messages.append({
                "role": "assistant",
                "content": response,
                "relevant_docs": relevant_docs
            })
            st.session_state.rag_chat_history += f"AI: {response}\n"

        except Exception as e:
            st.error(f"応答の生成中にエラーが発生しました: {str(e)}")
            st.code(str(e))



################################
# サイドバー構築
################################
with st.sidebar:
    # キーワード検索入力欄
    keyword_search = None
    st.markdown("## キーワード検索")
    keyword_search = st.text_input("キーワードを入力してください")

    # 権限のあるDBのみ表示
    db_option = list(db_dict[role].keys())

    st.markdown("## フィルター")
    selected_db = st.selectbox("データベースを選択してください", db_option)

    schema_option = db_dict[role][selected_db]
    selected_schema = st.selectbox("スキーマを選択してください", schema_option)
    st.markdown("# ")

    # 検索ボタン
    research_trigger = st.button("検索", use_container_width=True)

################################
# メインページ
################################
# title
tab1, tab2 = st.tabs(["データカタログ", "AIチャットに聞く"])
with tab1:
    st.markdown("<h1 style=' font-weight: bold;'>Data Catalog</h1>", unsafe_allow_html=True)
    st.caption("詳細表示のチェックボックスを選択するとカラム情報が表示されます。")
    with st.spinner('検索結果を読み込み中です...少々お待ちください...'):
        # 表示するデータベースの決定
        if selected_db == "選択しない":
            dbs = [item for item in db_option if item != "選択しない"]
        else:
            dbs = [selected_db]

        for db in dbs:
            st.subheader(f"{db} データベース", divider="gray")
            if f"df_all_{db}" not in st.session_state:  # セッション最初にDB内全てのテーブルを取得
                get_table_df = get_table_query(db)
                st.session_state[f"df_all_{db}"] = pd.DataFrame(session.sql(get_table_df).collect())

            # 表示するスキーマの決定
            if selected_schema == "選択しない":
                schemas = [item for item in db_dict[role][db] if item != "選択しない"]
            else:
                schemas = [selected_schema]
            for schema in schemas:
                st.markdown(f"##### {db} > {schema} スキーマ")
                # スキーマのみに絞り込む
                if f"df_{db}_{schema}" not in st.session_state:
                    st.session_state[f"df_{schema}"] = st.session_state[f"df_all_{db}"][st.session_state[f"df_all_{db}"]['TABLE_SCHEMA'] == schema]
                # キーワード検索
                if keyword_search:
                    df_tables = filter_tables(st.session_state[f"df_{schema}"], keyword_search)
                else:
                    df_tables = st.session_state[f"df_{schema}"]

                # テーブル一覧の表示と選択の取得
                select_table = display_and_get_table(df_tables, db, schema)

                # 選択テーブルがある場合、詳細を表示
                if not select_table.empty:
                    for _, row in select_table.iterrows():
                        table_input = f"{row['DB']}.{row['SCHEMA']}.{row['TABLE_NAME']}"
                        with st.expander(f"{row['TABLE_NAME']}の詳細情報を表示", expanded=True):
                            display_detail_info(table_input)
with tab2:
    call_chatbot("tab_chatbot")