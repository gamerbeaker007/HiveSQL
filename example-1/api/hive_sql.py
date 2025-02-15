import datetime
import logging
from contextlib import closing
from decimal import Decimal

import pandas as pd
import pypyodbc
import streamlit as st

log = logging.getLogger("Hive SQL")

SERVER = "vip.hivesql.io"
DB = "DBHive"
USERNAME = st.secrets["database"]["username"]
PASSWORD = st.secrets["database"]["password"]


def find_valid_connection_string():
    """Finds a valid SQL connection string by testing available ODBC drivers."""
    driver_names = [f"ODBC Driver {x} for SQL Server" for x in [17, 18]]
    for driver_name in driver_names:
        conn_str = (
            f"Driver={driver_name};"
            f"Server={SERVER};"
            f"Database={DB};"
            f"UID={USERNAME};"
            f"PWD={PASSWORD};"
            f"TrustServerCertificate=yes;"
            f"Encrypt=yes"
        )
        try:
            with closing(pypyodbc.connect(conn_str)) as connection, closing(connection.cursor()):
                log.info(f"Connected successfully using {driver_name}")
                return conn_str
        except pypyodbc.Error as e:
            log.warning(f"Failed with {driver_name}: {e}")
    log.error("No working ODBC driver found.")
    return None


@st.cache_resource
def get_cached_connection_string():
    """Caches the SQL connection string to avoid redundant computations."""
    return find_valid_connection_string()


def convert_dataframe_types(df, cursor_descriptions):
    """
    Converts DataFrame columns to appropriate types based on SQL column types.

    Parameters:
    - df (pd.DataFrame): The DataFrame to be converted.
    - cursor_description (list): The cursor.description containing column names and types.

    Returns:
    - pd.DataFrame: DataFrame with converted column types.
    """
    type_map = {
        str: "string",
        int: "Int64",  # Pandas nullable integer type
        float: "float64",
        bool: "boolean",  # Pandas nullable boolean type
        Decimal: "float64",  # Convert Decimal to float for Pandas compatibility
        datetime.date: "datetime64[ns]",  # Convert to Pandas datetime format
        datetime.datetime: "datetime64[ns]",
    }

    for column_name, slq_type, *rest in cursor_descriptions:
        sample_value = df[column_name].dropna().iloc[0] if not df[column_name].dropna().empty else None
        python_type = type(sample_value)

        if python_type in type_map:
            df[column_name] = df[column_name].astype(type_map[python_type])

    return df


def execute_query_df(query, params=None):
    """
    Executes a SQL query with optional parameters and returns a Pandas DataFrame.

    Parameters:
    - query: str, the SQL query to execute.
    - params: list or tuple, optional, the parameters for the query.

    Returns:
    - pd.DataFrame with query results or an empty DataFrame on failure/no results.
    """
    conn_string = get_cached_connection_string()
    if conn_string is None:
        log.error("No valid database connection string found.")
        return pd.DataFrame()

    try:
        with closing(pypyodbc.connect(conn_string)) as connection, closing(connection.cursor()) as cursor:
            cursor.execute(query, params or ())
            columns = [column[0] for column in cursor.description] if cursor.description else []
            rows = cursor.fetchall()

            if not rows:
                return pd.DataFrame(columns=columns)

            # Convert rows to dict with proper types
            df = pd.DataFrame(rows, columns=columns)

            # Convert DataFrame columns to correct types
            df = convert_dataframe_types(df, cursor.description)

            return df
    except pypyodbc.Error as e:
        log.error(f"Database error: {e}")
        return pd.DataFrame()
