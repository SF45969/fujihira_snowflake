################################
# Import python packages
################################
import streamlit as st
import pandas as pd
from snowflake.snowpark.context import get_active_session

################################
################################
# 環境設定
################################
st.set_page_config(
    page_title="Data Catalog",
    layout="wide",
    initial_sidebar_state="auto"
    )

st.write("hello SiS")