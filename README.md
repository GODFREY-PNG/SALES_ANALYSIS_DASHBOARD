# 📊 Sales Analytics Dashboard

An end-to-end data pipeline and interactive analytics dashboard built on the [UCI Online Retail dataset(541K+ transactions).  
This project transforms raw transactional data into real-time, production-ready business intelligence.

---

## 🧩 Problem

Retail businesses often struggle with:

- Fragmented transactional data
- Poor visibility into revenue drivers
- Manual reporting processes
- Limited understanding of customer value
- Inability to track revenue growth accurately

Without a structured analytics system, decision-making remains reactive rather than data-driven.

---

## 🛠️ Solution

This project implements a full analytics stack:

1. Data cleaning and transformation
2. Revenue and feature engineering
3. Customer-level aggregation and segmentation
4. PostgreSQL database integration
5. Interactive Dash + Plotly dashboard
6. Automated KPI reporting

The system moves from raw CSV data to a deployed production dashboard.

---

## ⚙️ Data Pipeline

### Data Cleaning & Feature Engineering

- Removed duplicates and invalid price records
- Separated returns from sales
- Engineered key metrics:
  - Revenue
  - Net Revenue
  - Return Rate
  - Purchase Frequency
  - Recency (days since last purchase)
  - Customer lifetime metrics

### Database Layer

- PostgreSQL relational schema:
  - `sales_data` (transaction-level)
  - `customer_summary` (customer-level metrics)
- Uploads data in chunks for scalability
- Data validation and integrity checks
- Environment-variable-based database configuration

---

## 📈 Dashboard Features

Built using Dash, Plotly, SQLAlchemy, and PostgreSQL.

### Core KPIs

- Total Revenue
- Revenue Growth
- Average Order Value
- Return Rate
- Revenue per Customer
- Total Customers
- Total Transactions

### Interactive Filters

- Date range selection
- Country filter
- Product-level drill-down
- Period comparison logic
- Real-time recalculation of KPIs

### Visualizations

- Monthly revenue trends
- Sales by day of week
- Hour vs Day heatmap
- Top products by revenue
- Geographic revenue distribution
- Customer value segmentation

---

## 🏗️ Tech Stack

**Data Processing**

- Python
- Pandas
- NumPy

**Backend**

- PostgreSQL
- SQLAlchemy
- psycopg2

**Visualization**

- Dash
- Plotly
- Dash Bootstrap Components

**Deployment**

- Gunicorn
- Render
- Environment-based configuration

---

## 🚀 Installation & Setup

### 1️⃣ Clone and set up environment

```bash
git clone https://github.com/GODFREY-PNG/SALES_ANALYSIS_DASHBOARD.git
cd SALES_ANALYSIS_DASHBOARD

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

pip install -r requirements.txt


export DB_HOST=your_host
export DB_NAME=your_db
export DB_USER=your_user
export DB_PASSWORD=your_password
export DB_PORT=5432

├── data/                   # Raw and processed data files
├── notebooks/              # Jupyter notebooks for exploration and prototyping
│   └── output/             # Output files like cleaned CSVs and summaries
├── reports/                # Generated reports and charts
├── scripts/                # Core Python scripts for data processing and analysis
├── src/                    # Utility modules and reusable functions
├── venv/                   # Virtual environment (excluded from repo)
├── app.py                  # Optional application entry point
├── pipeline_main.py        # Main data pipeline script
├── report_main.py          # Script for database upload and dashboard generation
├── requirements.txt        # Python dependencies
├── sql_utils.py            # SQL helper functions
└── README.md               # This documentation file

python pipeline_main.py
python report_main.py