import os
import re
import pandas as pd
import streamlit as st
from data.storage.storage_core import connect

def _friendly_table_name(raw_name: str) -> str:
    """Convert raw table names like `price_data` into `Price Data`."""
    cleaned = re.sub(r"[^0-9A-Za-z]+", " ", raw_name)
    cleaned = " ".join(cleaned.split())
    return cleaned.title() if cleaned else raw_name

def fetch_table_names(conn) -> list[str]:
    df = pd.read_sql_query(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;", conn
    )
    return df["name"].tolist()


def build_display_map(names: list[str]) -> dict[str, str]:
    display_to_table: dict[str, str] = {}
    for raw in names:
        label = _friendly_table_name(raw)
        if label in display_to_table:
            label = f"{label} ({raw})"
        display_to_table[label] = raw
    return display_to_table

st.set_page_config(
    page_title="TradingBot DB",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_PATH = os.getenv("DATABASE_PATH", "data/trading_bot.db")
conn = connect(DB_PATH, check_same_thread=False)

table_names = fetch_table_names(conn)

if not table_names:
    st.sidebar.info("No tables found in the database.")
    selected = None
else:
    display_to_table = build_display_map(table_names)
    selected_label = st.sidebar.radio("Tables", list(display_to_table), index=0)
    selected = display_to_table[selected_label]

st.header("TradingBot DB")

if selected:
    st.dataframe(
        pd.read_sql_query(f"SELECT * FROM {selected} LIMIT 1000", conn),
        use_container_width=True,
        height=500,
    )
