# main.py

import os
import matplotlib.pyplot as plt
from datetime import datetime
import pandas as pd

from sql_utils import (
    get_engine,
    load_csv_data,
    create_tables,
    clear_table,
    load_data_to_db,
    run_query
)

# ==========================================================
# GLOBAL CONFIGURATION
# ==========================================================

REPORT_FOLDER = "reports"
os.makedirs(REPORT_FOLDER, exist_ok=True)

RUN_TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")


# ==========================================================
# HELPER FUNCTIONS
# ==========================================================

def print_section(title):
    """Print formatted section header."""
    print("\n" + "=" * 50)
    print(f" {title}")
    print("=" * 50)


def save_with_latest(df, base_name):
    """
    Save dataframe with timestamp AND overwrite latest version.
    Example:
        base_name = "monthly_revenue"
        → monthly_revenue_20260101.csv
        → monthly_revenue_latest.csv
    """
    if df.empty:
        return

    timestamp_path = f"{REPORT_FOLDER}/{base_name}_{RUN_TIMESTAMP}.csv"
    latest_path = f"{REPORT_FOLDER}/{base_name}_latest.csv"

    df.to_csv(timestamp_path, index=False)
    df.to_csv(latest_path, index=False)

    print(f"Saved: {timestamp_path}")
    print(f"Updated latest: {latest_path}")


# ==========================================================
# PLOTTING
# ==========================================================

def plot_monthly_sales(monthly_sales, top_countries):
    """Create revenue trend + top countries plot."""

    if monthly_sales.empty or top_countries.empty:
        print("No data available for plotting.")
        return

    plt.style.use("seaborn-v0_8-darkgrid")
    fig, axes = plt.subplots(1, 2, figsize=(15, 5))

    # Format month column
    monthly_sales["month_str"] = monthly_sales["month"].dt.strftime("%b %Y")

    # Line chart – Monthly revenue
    axes[0].plot(
        monthly_sales["month_str"],
        monthly_sales["monthly_revenue"],
        marker="o",
        linewidth=2
    )
    axes[0].set_title("Monthly Revenue Trend", fontweight="bold")
    axes[0].tick_params(axis="x", rotation=45)

    # Horizontal bar – Top countries
    axes[1].barh(
        top_countries["country"],
        top_countries["revenue"]
    )
    axes[1].set_title("Top 8 Countries by Revenue", fontweight="bold")

    plt.tight_layout()

    # Save plot (timestamp + latest)
    plot_path = f"{REPORT_FOLDER}/sales_analysis_{RUN_TIMESTAMP}.png"
    plt.savefig(plot_path, dpi=300)
    plt.savefig(f"{REPORT_FOLDER}/sales_analysis_latest.png", dpi=300)

    print(f"Plot saved: {plot_path}")
    plt.show()


# ==========================================================
# DASHBOARD
# ==========================================================

def format_value(value, fmt):
    """Format metric value for display."""
    if value is None:
        return "0"

    if fmt == "currency":
        return f"${value:,.2f}"
    if fmt == "count":
        return f"{int(value):,}"
    if fmt == "percent":
        return f"{value:.1f}%"
    if fmt == "days":
        return f"{int(value)} days"

    return f"{value:.2f}"


def generate_dashboard(engine):
    """Run dashboard KPI queries and print results."""

    print_section("SALES PERFORMANCE DASHBOARD")

    metrics = [
        ("Total Revenue", "SELECT SUM(net_revenue) FROM sales_data WHERE net_revenue > 0", "currency"),
        ("Avg Order Value", "SELECT AVG(net_revenue) FROM sales_data WHERE net_revenue > 0", "currency"),
        ("Total Customers", "SELECT COUNT(DISTINCT customerid) FROM sales_data", "count"),
        ("Total Transactions", "SELECT COUNT(*) FROM sales_data WHERE total_items > 0", "count"),
    ]

    dashboard_data = []

    for name, query, fmt in metrics:
        df = run_query(query, engine)
        value = df.iloc[0, 0] if not df.empty else 0
        display = format_value(value, fmt)

        print(f"{name:<25} {display}")

        dashboard_data.append({
            "metric": name,
            "value": value,
            "display": display,
            "format": fmt,
            "run_timestamp": RUN_TIMESTAMP
        })

    # Save dashboard report
    dashboard_df = pd.DataFrame(dashboard_data)
    save_with_latest(dashboard_df, "dashboard_metrics")


# ==========================================================
# MAIN WORKFLOW
# ==========================================================

def main():

    print_section(f"RUN STARTED: {RUN_TIMESTAMP}")

    # ------------------------------------------------------
    # 1. Connect to database
    # ------------------------------------------------------
    engine = get_engine()

    # ------------------------------------------------------
    # 2. Load cleaned CSV files
    # ------------------------------------------------------
    cleaned_data, customer_summary = load_csv_data(
        "notebooks/output/cleaned_retail_data.csv",
        "notebooks/output/customer_summary.csv"
    )

    # Remove duplicates safely
    cleaned_data = cleaned_data.drop_duplicates(
        subset=["invoiceno", "stockcode", "customerid"]
    )

    # ------------------------------------------------------
    # 3. Prepare database tables
    # ------------------------------------------------------
    create_tables(engine)
    clear_table(engine, "customer_summary")
    clear_table(engine, "sales_data")

    load_data_to_db(cleaned_data, customer_summary, engine)

    # ------------------------------------------------------
    # 4. Duplicate check
    # ------------------------------------------------------
    duplicate_check = run_query("""
        SELECT COUNT(*) AS total_rows,
               COUNT(DISTINCT invoiceno || '-' || stockcode || '-' || customerid) AS unique_rows
        FROM sales_data
    """, engine)

    save_with_latest(duplicate_check, "duplicate_check")

    # ------------------------------------------------------
    # 5. Monthly revenue query
    # ------------------------------------------------------
    monthly_sales = run_query("""
        SELECT DATE_TRUNC('month', invoicedate) AS month,
               SUM(net_revenue) AS monthly_revenue
        FROM sales_data
        WHERE net_revenue > 0
        GROUP BY 1
        ORDER BY 1
    """, engine)

    save_with_latest(monthly_sales, "monthly_revenue")

    # ------------------------------------------------------
    # 6. Top countries query
    # ------------------------------------------------------
    top_countries = run_query("""
        SELECT country,
               SUM(net_revenue) AS revenue
        FROM sales_data
        WHERE net_revenue > 0
          AND country IS NOT NULL
          AND country <> 'Unspecified'
        GROUP BY country
        ORDER BY revenue DESC
        LIMIT 8
    """, engine)

    save_with_latest(top_countries, "top_countries")

    # ------------------------------------------------------
    # 7. Visualizations
    # ------------------------------------------------------
    plot_monthly_sales(monthly_sales, top_countries)

    # ------------------------------------------------------
    # 8. Dashboard KPIs
    # ------------------------------------------------------
    generate_dashboard(engine)

    # ------------------------------------------------------
    # 9. Final Summary
    # ------------------------------------------------------
    print_section("REPORT SUMMARY")

    files = os.listdir(REPORT_FOLDER)
    new_files = [f for f in files if RUN_TIMESTAMP in f]

    print(f"Total files in folder: {len(files)}")
    print(f"New files this run: {len(new_files)}")


# ==========================================================
# ENTRY POINT
# ==========================================================

if __name__ == "__main__":
    main()
