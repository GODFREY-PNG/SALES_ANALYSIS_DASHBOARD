# utils.py
import os
import pandas as pd

def save_results(df, customer_summary, output_dir="output"):
    """Save processed data to files"""
    os.makedirs(output_dir, exist_ok=True)
    
    # Save cleaned data
    df.to_csv(f"{output_dir}/cleaned_retail_data.csv", index=False)
    
    # Save customer summary
    customer_summary.to_csv(f"{output_dir}/customer_summary.csv",index=False)
    
    print(f"\nResults saved to {output_dir}/ directory")
