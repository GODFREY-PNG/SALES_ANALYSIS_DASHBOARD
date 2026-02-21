# analyze_products.py
import pandas as pd
import numpy as np

def analyze_products(df):
    """Analyze product performance"""

    # Filter out non-product stock codes
    non_products_list = ["S", "D", "BANK CHARGES", "CRUK", "M", "AMAZONFEE"]

    # Aggregate revenue per product
    revenue_per_product = (
        df.groupby("StockCode")["Net_Revenue"]
        .sum()
        .sort_values(ascending=False)
    )

    real_products_revenue = revenue_per_product[
        ~revenue_per_product.index.isin(non_products_list)
    ]

    # Categorize products
    profitable_products = real_products_revenue[real_products_revenue > 0]
    loss_products = real_products_revenue[real_products_revenue < 0]

    # Return structured result
    return {
        "top_profitable": profitable_products.head(10),
        "top_losses": loss_products.head(10),
        "counts": {
            "profitable": len(profitable_products),
            "loss": len(loss_products),
        }
    }
