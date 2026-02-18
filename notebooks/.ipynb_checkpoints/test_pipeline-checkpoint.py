print("TEST SCRIPT STARTED")
# test_pipeline.py
from data_processing import (
    load_extract_data,
    clean_data,
    handle_quantity_and_price,
    calculate_revenue_metrics
)
from analyze_products import analyze_products
from customer_analysis import analyze_customers

# Step 0: Set your ZIP path
ZIP_PATH = "../data/online+retail.zip"

# 1️⃣ Load data
df = load_extract_data(ZIP_PATH)
print("Data loaded. Shape:", df.shape)

# 2️⃣ Clean data
df = clean_data(df)
print("Data cleaned. Shape:", df.shape)

# 3️⃣ Handle quantity and price
df = handle_quantity_and_price(df)
print("Quantity & price processed.")

# 4️⃣ Calculate revenue metrics
df = calculate_revenue_metrics(df)
print("Revenue metrics calculated.")

# 5️⃣ Test product analysis
product_results = analyze_products(df)
print("Product analysis results keys:", product_results.keys())

# 6️⃣ Test customer analysis
customer_summary = analyze_customers(df)
print("Customer summary shape:", customer_summary.shape)

# Optional: inspect top few rows
print("\nSample customer summary:")
print(customer_summary.head())

print("\nPipeline functions seem to be working!")
