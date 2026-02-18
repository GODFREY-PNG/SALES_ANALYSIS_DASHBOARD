# sql_utils.py
import os
import pandas as pd
import urllib.parse
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# CONFIGURATION
load_dotenv()
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST     = os.getenv("DB_HOST")
DB_PORT     = os.getenv("DB_PORT")
DB_NAME     = os.getenv("DB_NAME")

DB_PASSWORD_ENCODED = urllib.parse.quote_plus(DB_PASSWORD)
DB_URI = f"postgresql+psycopg2://{DB_USERNAME}:{DB_PASSWORD_ENCODED}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# DATABASE CONNECTION
def get_engine():
    """Return a SQLAlchemy engine"""
    return create_engine(DB_URI)

def run_query(query, engine,params=None):
    """Run SQL query and return a pandas DataFrame"""
    with engine.connect() as conn:
        return pd.read_sql(query, conn)

# CSV DATA LOADING
def load_csv_data(cleaned_path, customer_path):
    """Load cleaned CSV files and format them for DB insertion"""
    cleaned_data = pd.read_csv(cleaned_path)
    customer_summary = pd.read_csv(customer_path)

    # Convert InvoiceDate to datetime
    cleaned_data['InvoiceDate'] = pd.to_datetime(cleaned_data['InvoiceDate'])

    # Lowercase columns for PostgreSQL
    cleaned_data.columns = [c.lower() for c in cleaned_data.columns]
    customer_summary.columns = [c.lower() for c in customer_summary.columns]

    return cleaned_data, customer_summary

# TABLE CREATION
def create_tables(engine):
    """Create sales_data and customer_summary tables if they don't exist"""
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS sales_data (
                InvoiceNo VARCHAR(20),
                StockCode VARCHAR(50),
                Description TEXT,
                Quantity INTEGER,
                InvoiceDate TIMESTAMP,
                UnitPrice NUMERIC(10,2),
                CustomerID VARCHAR(20),
                Country VARCHAR(100),
                Return_Qty INTEGER,
                Sale_Qty INTEGER,
                Paid_UnitPrice NUMERIC(10,2),
                Is_Free_Item VARCHAR(3),
                Revenue NUMERIC(12,2),
                Net_Revenue NUMERIC(12,2),
                Total_Items INTEGER
            );
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS customer_summary (
                CustomerID VARCHAR(20) PRIMARY KEY,
                Total_Purchases INTEGER,
                Total_Net_Revenue NUMERIC(12,2),
                Total_Sale_Qty INTEGER,
                Total_Return_Qty INTEGER,
                Avg_Order_Value NUMERIC(12,2),
                RecencyDays INTEGER,
                Return_Rate NUMERIC(10,6),
                Net_Qty INTEGER,
                Purchase_Frequency_Monthly NUMERIC(10,2),
                Customer_Value VARCHAR(20)
            );
        """))
        conn.commit()

def clear_table(engine, table_name):
    """Truncate a table"""
    with engine.connect() as conn:
        conn.execute(text(f"TRUNCATE TABLE {table_name}"))
        conn.commit()

def load_data_to_db(cleaned_data, customer_summary, engine):
    """Load cleaned data into PostgreSQL tables"""
    cleaned_data.to_sql('sales_data', engine, if_exists='append', index=False, chunksize=1000, method='multi')
    customer_summary.to_sql('customer_summary', engine, if_exists='append', index=False, chunksize=1000, method='multi')
