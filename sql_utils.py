# sql_utils.py
# Utility module for database connection, querying, and data loading

import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# CONFIGURATION
# Load environment variables from .env file (for local development)
# On Render, these are set directly in the dashboard environment settings

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Stop app immediately if DATABASE_URL is missing
if not DATABASE_URL:
    raise EnvironmentError("DATABASE_URL environment variable is not set!")

# SQLAlchemy requires 'postgresql+psycopg2://' prefix instead of 'postgres://'
# Render sometimes provides 'postgres://' so we fix it here
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)

# DATABASE CONNECTION


def get_engine():
    """
    Create and return a SQLAlchemy engine using the DATABASE_URL.
    Called once at app startup in app.py.
    """
    return create_engine(DATABASE_URL)  # Fixed: was incorrectly referencing DB_URI


def run_query(query, engine, params=None):
    """
    Execute a SQL query and return results as a pandas DataFrame.
    
    Args:
        query  : SQL query string
        engine : SQLAlchemy engine from get_engine()
        params : Optional query parameters (not currently used)
    
    Returns:
        pandas DataFrame with query results
    """
    with engine.connect() as conn:
        return pd.read_sql(query, conn)

# CSV DATA LOADING
# Used when initially uploading data to the database


def load_csv_data(cleaned_path, customer_path):
    """
    Load and format cleaned CSV files for database insertion.
    
    Args:
        cleaned_path  : Path to the cleaned sales data CSV
        customer_path : Path to the customer summary CSV
    
    Returns:
        Tuple of (cleaned_data, customer_summary) as DataFrames
    """
    cleaned_data = pd.read_csv(cleaned_path)
    customer_summary = pd.read_csv(customer_path)

    # Convert InvoiceDate column to datetime format
    cleaned_data['InvoiceDate'] = pd.to_datetime(cleaned_data['InvoiceDate'])

    # Lowercase all column names to match PostgreSQL conventions
    cleaned_data.columns = [c.lower() for c in cleaned_data.columns]
    customer_summary.columns = [c.lower() for c in customer_summary.columns]

    return cleaned_data, customer_summary



# TABLE CREATION
# Creates tables in PostgreSQL if they don't already exist


def create_tables(engine):
    """
    Create sales_data and customer_summary tables if they don't exist.
    Safe to run multiple times — uses IF NOT EXISTS.
    
    Args:
        engine : SQLAlchemy engine from get_engine()
    """
    with engine.connect() as conn:

        # Main sales transactions table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS sales_data (
                InvoiceNo       VARCHAR(20),
                StockCode       VARCHAR(50),
                Description     TEXT,
                Quantity        INTEGER,
                InvoiceDate     TIMESTAMP,
                UnitPrice       NUMERIC(10,2),
                CustomerID      VARCHAR(20),
                Country         VARCHAR(100),
                Return_Qty      INTEGER,
                Sale_Qty        INTEGER,
                Paid_UnitPrice  NUMERIC(10,2),
                Is_Free_Item    VARCHAR(3),
                Revenue         NUMERIC(12,2),
                Net_Revenue     NUMERIC(12,2),
                Total_Items     INTEGER
            );
        """))

        # Customer-level summary table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS customer_summary (
                CustomerID                  VARCHAR(20) PRIMARY KEY,
                Total_Purchases             INTEGER,
                Total_Net_Revenue           NUMERIC(12,2),
                Total_Sale_Qty              INTEGER,
                Total_Return_Qty            INTEGER,
                Avg_Order_Value             NUMERIC(12,2),
                RecencyDays                 INTEGER,
                Return_Rate                 NUMERIC(10,6),
                Net_Qty                     INTEGER,
                Purchase_Frequency_Monthly  NUMERIC(10,2),
                Customer_Value              VARCHAR(20)
            );
        """))

        conn.commit()

# TABLE UTILITIES


def clear_table(engine, table_name):
    """
    Remove all rows from a table without dropping its structure.
    
    Args:
        engine     : SQLAlchemy engine from get_engine()
        table_name : Name of the table to truncate
    """
    with engine.connect() as conn:
        conn.execute(text(f"TRUNCATE TABLE {table_name}"))
        conn.commit()


def load_data_to_db(cleaned_data, customer_summary, engine):
    """
    Insert cleaned DataFrames into their respective PostgreSQL tables.
    Uses append mode so existing data is not overwritten.
    
    Args:
        cleaned_data     : Sales data DataFrame
        customer_summary : Customer summary DataFrame
        engine           : SQLAlchemy engine from get_engine()
    """
    cleaned_data.to_sql(
        'sales_data', engine,
        if_exists='append',
        index=False,
        chunksize=1000,
        method='multi'
    )
    customer_summary.to_sql(
        'customer_summary', engine,
        if_exists='append',
        index=False,
        chunksize=1000,
        method='multi'
    )
