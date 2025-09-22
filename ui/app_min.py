import os
import pandas as pd
import streamlit as st
from data.storage.storage_core import connect

DB_PATH = os.getenv("DATABASE_PATH", "data/trading_bot.db")
conn = connect(DB_PATH, check_same_thread=False)

st.title("TradingBot DB")

tables = pd.read_sql_query(
    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;", conn
)
selected = st.selectbox("Table", tables["name"].tolist())
if selected:
    st.dataframe(
        pd.read_sql_query(f"SELECT * FROM {selected} LIMIT 1000", conn),
        use_container_width=True,
    )
    
