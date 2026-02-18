
# customer_analysis.py
import pandas as pd
import numpy as np

def analyze_customers(df):
    """Analyze customer behavior and value"""
    # Customer summary metrics
    customer_summary = df.groupby("CustomerID",observed=False).agg(
        Total_Purchases=("InvoiceNo", "nunique"),
        Total_Net_Revenue=("Net_Revenue", "sum"),
        Total_Sale_Qty=("Sale_Qty", "sum"),
        Total_Return_Qty=("Return_Qty", "sum")
    ).reset_index()
    
    # Calculate additional metrics
    customer_summary["Avg_Order_Value"] = (
        customer_summary["Total_Net_Revenue"] / customer_summary["Total_Purchases"]
    )
    
    # Calculate recency
    latest_date = df['InvoiceDate'].max()
    customer_recency = df.groupby('CustomerID',observed=False)['InvoiceDate'].max().reset_index()
    customer_recency['RecencyDays'] = (latest_date - customer_recency['InvoiceDate']).dt.days
    customer_summary = customer_summary.merge(
        customer_recency[['CustomerID', 'RecencyDays']], 
        on='CustomerID'
    )
    
    # Calculate return rate
    customer_summary['Return_Rate'] = (
        customer_summary['Total_Return_Qty'] /
        customer_summary['Total_Sale_Qty'].replace(0, np.nan)
    )
    
    # Calculate net quantity
    customer_summary['Net_Qty'] = (
        customer_summary['Total_Sale_Qty'] - customer_summary['Total_Return_Qty']
    )
    
    # Calculate purchase frequency
    customer_summary['Purchase_Frequency_Monthly'] = (
        customer_summary['Total_Purchases'] /
        ((customer_summary['RecencyDays'] + 1) / 30)
    )
    
    # Categorize customer value
    customer_summary['Customer_Value'] = np.where(
        customer_summary['Total_Net_Revenue'] > 0,
        'Positive',
        'Negative'
    )
    
    # Filter out unknown customers
    known_customers = customer_summary[customer_summary['CustomerID'] != 'Unknown'].copy()
    
    return known_customers.sort_values(by="Total_Net_Revenue", ascending=False)