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

st.subheader("Simple quick query")

if st.button("Run Top 100 query"):
    log.info("Run Top 100 query")
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

st.subheader("More advanced query")

number_of_communities = hive_sql.execute_query_df("SELECT COUNT(name) as count FROM Communities").iloc[0]['count']
st.markdown(f"""
Now, we are going to build a query that analyzes Hive communities. \n
Out of {number_of_communities} total communities, we will identify the top 10 with the highest number of subscribers.\n
We will then retrieve the community name (title) and gather all subscribers' vesting shares, 
converting them into Hive Power (HP). This will allow us to see which community holds the most HP based on its subscribed members.
""")

if st.button("Run Top 10 Communities query"):
    log.info("Run Top 10 Communities query")

    with st.spinner("Loading data... this can take a while"):
        df = hive_sql.execute_query_df("""
        WITH TopCommunities AS (
            SELECT TOP 10 community, COUNT(subscriber) AS subscriber_count
            FROM CommunitiesSubscribers
            GROUP BY community
            ORDER BY subscriber_count DESC
        ),
        CommunityMembers AS (
            SELECT cs.community, cs.subscriber AS account_name
            FROM CommunitiesSubscribers cs
            JOIN TopCommunities tc ON cs.community = tc.community
        )
        SELECT cm.account_name, cm.community, c.title, a.vesting_shares
        FROM CommunityMembers cm
        JOIN Communities c ON cm.community = c.name
        JOIN Accounts a ON cm.account_name = a.name;
        """)

        conversion_factor = hive_sql.get_hive_per_mvest() / 1e6
        df["hp"] = conversion_factor * df["vesting_shares"]

        df = df.groupby('title', as_index=False)['hp'].sum()
        df = df.sort_values(by='hp', ascending=False).reset_index(drop=True)

        fig = px.bar(df, x='title', y='hp', title="Top 10 Communities and there HP")
        st.plotly_chart(fig, theme="streamlit")

