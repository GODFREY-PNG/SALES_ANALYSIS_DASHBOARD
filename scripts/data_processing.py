import zipfile
import os
import pandas as pd
import numpy as np

def load_extract_data(zip_path):
    """Extract and load data from zip file"""
    
    with zipfile.ZipFile(zip_path, "r") as zip_file:
        print("Files in zip:", zip_file.namelist())
        zip_file.extractall(".")

    df = pd.read_excel("Online Retail.xlsx")
    print(f"Loaded {len(df):,} rows")

    return df
def clean_data(df):
    """Clean and preprocess the dataframe"""
    # Fill missing values
    df["Description"] = df["Description"].fillna("Unknown Product")
    df["CustomerID"] = df["CustomerID"].fillna("Unknown")
    
    # Convert data types for efficiency
    df["InvoiceNo"] = df["InvoiceNo"].astype("category")
    df["CustomerID"] = df["CustomerID"].astype("category")
    df["Country"] = df["Country"].astype("category")
    df["Quantity"] = pd.to_numeric(df["Quantity"], downcast="integer")
    df["Description"] = df["Description"].astype("string")
    df["StockCode"] = df["StockCode"].astype("string")
    
    # Convert InvoiceDate to datetime
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])

    #REmoving Duplicates
    df = df.drop_duplicates()
    
    return df

def handle_quantity_and_price(df):
    """Process quantity and price columns"""
    # Separate returns from sales
    df["Return_Qty"] = df["Quantity"].where(df["Quantity"] < 0, 0).abs()
    df["Sale_Qty"] = df["Quantity"].where(df["Quantity"] > 0, 0)
    
    # Remove negative prices
    df = df[df["UnitPrice"] >= 0].copy()

    
    # Create price-related columns
    df["Paid_UnitPrice"] = df["UnitPrice"].where(df["UnitPrice"] > 0, 0)
    df["Is_Free_Item"] = df["UnitPrice"].apply(lambda x: "Yes" if x == 0 else "No")
    
    return df
def calculate_revenue_metrics(df):
    """Calculate revenue and related metrics"""
    # Row-wise revenue calculations
    df["Revenue"] = df["Sale_Qty"] * df["Paid_UnitPrice"]
    df["Net_Revenue"] = (df["Sale_Qty"] - df["Return_Qty"]) * df["Paid_UnitPrice"]
    df["Total_Items"] = df["Sale_Qty"] + df["Return_Qty"]
    
    return df