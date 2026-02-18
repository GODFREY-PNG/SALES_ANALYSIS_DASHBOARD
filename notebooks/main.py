# main.py
import importlib
import utils
importlib.reload(utils)  # Force reload of utils module
from data_processing import (
    load_extract_data,
    clean_data,
    handle_quantity_and_price,
    calculate_revenue_metrics
)
from analyze_products import analyze_products
from customer_analysis import analyze_customers
from utils import save_results  

def main():
    """Main execution function (pipeline orchestrator)"""

    # Configuration
    ZIP_PATH = "../data/online+retail.zip"
    OUTPUT_DIR = "output"

    print("Starting Online Retail Pipeline...\n" + "="*50)

    # Load data 
    df = load_extract_data(ZIP_PATH)

    # Clean data 
    df = clean_data(df)

    # Handle quantity and price safely 
    df = handle_quantity_and_price(df)

    #  Calculate revenue metrics 
    df = calculate_revenue_metrics(df)

    # Analyze products 
    product_results = analyze_products(df)

    # Analyze customers 
    customer_summary = analyze_customers(df)

    #  High-level summary prints 
    print("\nPIPELINE SUMMARY")
    print("="*50)
    print(f"Total rows processed: {len(df):,}")
    print(f"Total revenue: ${df['Revenue'].sum():,.2f}")
    print(f"Net revenue: ${df['Net_Revenue'].sum():,.2f}")
    print(f"Total customers: {customer_summary.shape[0]:,}")
    print(f"Top customer revenue: ${customer_summary['Total_Net_Revenue'].iloc[0]:,.2f}")
    print(f"Number of profitable products: {product_results['counts']['profitable']}")
    print(f"Number of loss products: {product_results['counts']['loss']}")

    # --- Save results ---
    save_results(df, customer_summary, OUTPUT_DIR)

    print("\nPipeline executed successfully!")

if __name__ == "__main__":
    main()
