import logging

import plotly.express as px
import streamlit as st

from api import hive_sql
from util import log_util

log_util.config_logger()
log = logging.getLogger("Example 1")

st.set_page_config(layout="wide")

st.title("Lets start with Example 1 Streamlit 🎉")

st.markdown("""
In this first example, we will combine the previous tutorial 
on your first query with building a simple single-page application\n
We'll also demonstrate how easy it is to deploy using Streamlit.  
""")

if st.button("Run Top 100 query"):
    df = hive_sql.execute_query_df("""
    SELECT TOP 100 name, balance
    FROM Accounts
    WHERE balance > 1000
    ORDER BY balance DESC;
    """)

    if df.empty:
        log.error("No query result")
    else:
        log.info(f"Query result rows: {df.index.size}")
        fig = px.bar(df, x='name', y='balance', title="Top 100 Hive Accounts by Balance")
        st.plotly_chart(fig, theme="streamlit")
