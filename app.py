# app.py - Interactive Sales Dashboard
import pandas as pd
from dash import Dash, dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from sql_utils import get_engine, run_query

# Initialize database connection
engine = get_engine()

# Get date range for filters
date_range_df = run_query("SELECT MIN(invoicedate) as min_date, MAX(invoicedate) as max_date FROM sales_data", engine)
min_date = pd.to_datetime(date_range_df['min_date'].iloc[0])
max_date = pd.to_datetime(date_range_df['max_date'].iloc[0])

# Load initial data for dropdowns
countries_df = run_query("SELECT DISTINCT country FROM sales_data WHERE country IS NOT NULL AND country != '' ORDER BY country", engine)
country_options = [{'label': c, 'value': c} for c in countries_df['country'].tolist()]

products_df = run_query("SELECT DISTINCT description FROM sales_data WHERE description IS NOT NULL AND description != '' ORDER BY description", engine)
product_options = [{'label': p, 'value': p} for p in products_df['description'].tolist()]

# Initialize Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Enhanced Sales Dashboard"

# Custom CSS for card styling
CARD_STYLE = {
    'padding': '15px',
    'margin': '10px',
    'border-radius': '8px',
    'box-shadow': '2px 2px 10px rgba(0,0,0,0.1)',
    'background-color': 'white'
}

# Layout
app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col(html.H1("📊  Sales Analytics Dashboard", className="text-center mb-4"), width=12)
    ]),
    
    # Date Range Filter
    dbc.Row([
        dbc.Col(
            dbc.Card([
                html.Label("📅 Select Date Range:", className="fw-bold"),
                dcc.DatePickerRange(
                    id='date-range',
                    start_date=min_date,
                    end_date=max_date,
                    min_date_allowed=min_date,
                    max_date_allowed=max_date,
                    display_format='YYYY-MM-DD',
                    className="mt-2"
                )
            ], style=CARD_STYLE),
            md=6
        ),
        dbc.Col(
            dbc.Card([
                html.Label(" Quick Filters:", className="fw-bold"),
                dbc.RadioItems(
                    id='quick-filter',
                    options=[
                        {'label': 'Last 30 Days', 'value': '30d'},
                        {'label': 'Last Quarter', 'value': 'quarter'},
                        {'label': 'Last Year', 'value': 'year'},
                        {'label': 'All Time', 'value': 'all'}
                    ],
                    value='all',
                    inline=True,
                    className="mt-2"
                )
            ], style=CARD_STYLE),
            md=6
        )
    ], className="mb-3"),
    
    # Main KPIs Row 1
    dbc.Row([
        dbc.Col(html.Div(id='total-revenue-card', style=CARD_STYLE), md=3),
        dbc.Col(html.Div(id='total-transactions-card', style=CARD_STYLE), md=3),
        dbc.Col(html.Div(id='avg-order-card', style=CARD_STYLE), md=3),
        dbc.Col(html.Div(id='total-customers-card', style=CARD_STYLE), md=3)
    ], className="mb-3"),
    
    # Main KPIs Row 2 
    dbc.Row([
        dbc.Col(html.Div(id='return-rate-card', style=CARD_STYLE), md=3),
        dbc.Col(html.Div(id='items-per-trans-card', style=CARD_STYLE), md=3),
        dbc.Col(html.Div(id='revenue-growth-card', style=CARD_STYLE), md=3),
        dbc.Col(html.Div(id='revenue-per-customer-card', style=CARD_STYLE), md=3)
    ], className="mb-3"),
    
    # Filters Row
    dbc.Row([
        dbc.Col(
            dbc.Card([
                html.Label("🌍 Country:", className="fw-bold"),
                dcc.Dropdown(
                    id='country-dropdown',
                    options=country_options,
                    value='United Kingdom' if 'United Kingdom' in [c['value'] for c in country_options] else country_options[0]['value'] if country_options else None,
                    clearable=False,
                    className="mt-2"
                )
            ], style=CARD_STYLE),
            md=4
        ),
        dbc.Col(
            dbc.Card([
                html.Label("📦 Products:", className="fw-bold"),
                dcc.Dropdown(
                    id='product-dropdown',
                    options=product_options,
                    multi=True,
                    placeholder="Select products...",
                    className="mt-2"
                )
            ], style=CARD_STYLE),
            md=4
        ),
        dbc.Col(
            dbc.Card([
                html.Label("📈 Compare with:", className="fw-bold"),
                dcc.Dropdown(
                    id='compare-dropdown',
                    options=[
                        {'label': 'Previous Period', 'value': 'prev'},
                        {'label': 'Same Period Last Year', 'value': 'yoy'},
                        {'label': 'No Comparison', 'value': 'none'}
                    ],
                    value='none',
                    clearable=False,
                    className="mt-2"
                )
            ], style=CARD_STYLE),
            md=4
        )
    ], className="mb-3"),
    
    # Charts Row 1
    dbc.Row([
        dbc.Col(dcc.Graph(id='monthly-revenue-graph'), md=6),
        dbc.Col(dcc.Graph(id='sales-by-day-graph'), md=6)  # NEW
    ], className="mb-3"),
    
    # Charts Row 2
    dbc.Row([
        dbc.Col(dcc.Graph(id='top-products-bar'), md=6),
        dbc.Col(dcc.Graph(id='sales-heatmap'), md=6)  # NEW
    ], className="mb-3"),
    
    # Charts Row 3
    dbc.Row([
        dbc.Col(dcc.Graph(id='customer-segments'), md=6),  # NEW
        dbc.Col(dcc.Graph(id='geographic-map'), md=6)  # NEW
    ], className="mb-3"),
    
    # Download Section
    dbc.Row([
        dbc.Col(
            dbc.Card([
                html.Label("📥 Download Report:", className="fw-bold"),
                dbc.Button("Download Filtered Data", id="download-button", color="primary", className="mt-2"),
                dcc.Download(id="download-dataframe-csv")
            ], style=CARD_STYLE),
            md=4
        )
    ], className="mb-3")
], fluid=True, style={'background-color': '#f8f9fa', 'padding': '20px'})

# Helper function to get date filter condition
def get_date_condition(start_date, end_date):
    if start_date and end_date:
        return f"AND invoicedate BETWEEN '{start_date}' AND '{end_date}'"
    return ""

# 1️ Update all KPIs with date filter
@app.callback(
    Output('total-revenue-card', 'children'),
    Output('total-transactions-card', 'children'),
    Output('avg-order-card', 'children'),
    Output('total-customers-card', 'children'),
    Output('return-rate-card', 'children'),
    Output('items-per-trans-card', 'children'),
    Output('revenue-growth-card', 'children'),
    Output('revenue-per-customer-card', 'children'),
    Input('country-dropdown', 'value'),
    Input('date-range', 'start_date'),
    Input('date-range', 'end_date')
)
def update_all_kpis(selected_country, start_date, end_date):
    if not selected_country:
        return [([html.H5("N/A"), html.H4("$0")]) * 8]
    
    date_condition = get_date_condition(start_date, end_date)
    country_escaped = selected_country.replace("'", "''")
    
    # Main KPIs query
    query = f"""
        SELECT 
            COALESCE(SUM(net_revenue), 0) as total_revenue,
            COUNT(*) as total_transactions,
            COALESCE(AVG(net_revenue), 0) as avg_order,
            COUNT(DISTINCT customerid) as total_customers,
            COALESCE(SUM(sale_qty), 0) as total_qty,
            COALESCE(SUM(return_qty), 0) as return_qty,
            COALESCE(AVG(total_items), 0) as avg_items
        FROM sales_data
        WHERE country = '{country_escaped}' {date_condition}
    """
    df = run_query(query, engine)
    
    # Previous period query for growth
    if start_date and end_date:
        days_diff = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days
        prev_start = pd.to_datetime(start_date) - timedelta(days=days_diff)
        prev_end = pd.to_datetime(start_date) - timedelta(days=1)
        
        # First, check if previous period has sufficient data
        data_quality_query = f"""
            SELECT COUNT(DISTINCT DATE(invoicedate)) as days_with_data,
                   COUNT(*) as total_records
            FROM sales_data
            WHERE country = '{country_escaped}'
            AND invoicedate BETWEEN '{prev_start}' AND '{prev_end}'
        """
        quality_df = run_query(data_quality_query, engine)  # ← This is a DIFFERENT df
        days_with_data = int(quality_df['days_with_data'].iloc[0])
        
        # Now get the revenue
        growth_query = f"""
            SELECT COALESCE(SUM(net_revenue), 0) as prev_revenue
            FROM sales_data
            WHERE country = '{country_escaped}'
            AND invoicedate BETWEEN '{prev_start}' AND '{prev_end}'
        """
        prev_df = run_query(growth_query, engine)  # ← This is ANOTHER df
        prev_revenue = float(prev_df['prev_revenue'].iloc[0])
        
        # Check if we have at least 80% of expected days
        expected_days = days_diff
        data_completeness = (days_with_data / expected_days) * 100 if expected_days > 0 else 0
    else:
        prev_revenue = 0
        data_completeness = 0
    
    #  main metrics from the original df
    total_revenue = float(df['total_revenue'].iloc[0])  # ← Your original df
    total_transactions = int(df['total_transactions'].iloc[0])
    avg_order = float(df['avg_order'].iloc[0])
    total_customers = int(df['total_customers'].iloc[0])
    return_rate = (float(df['return_qty'].iloc[0]) / float(df['total_qty'].iloc[0]) * 100) if float(df['total_qty'].iloc[0]) > 0 else 0
    avg_items = round(float(df['avg_items'].iloc[0]))
    
    # Calculate growth with data quality warning
    if prev_revenue > 0:
        growth = ((total_revenue - prev_revenue) / prev_revenue) * 100
        # Add asterisk if data is incomplete
        if data_completeness < 80:  # Less than 80% of expected days
            growth_display = f"{growth:+.1f}%*"  # Asterisk indicates incomplete data
            growth_color = "orange"
        else:
            growth_display = f"{growth:+.1f}%"
            growth_color = "green" if growth >= 0 else "red"
    else:
        growth_display = "N/A"
        growth_color = "gray"
    
    revenue_per_customer = total_revenue / total_customers if total_customers > 0 else 0
    
    return (
        [html.H5("💰 Total Revenue", className="card-title"), html.H4(f"${total_revenue:,.2f}")],
        [html.H5("📊 Transactions", className="card-title"), html.H4(f"{total_transactions:,}")],
        [html.H5("🛒 Avg Order", className="card-title"), html.H4(f"${avg_order:,.2f}")],
        [html.H5("👥 Customers", className="card-title"), html.H4(f"{total_customers:,}")],
        [html.H5("↩️ Return Rate", className="card-title"), html.H4(f"{return_rate:.1f}%")],
        [html.H5("📦 Items/Trans", className="card-title"), html.H4(f"{avg_items:.1f}")],
        [html.H5("📈 Revenue Growth", className="card-title"), html.H4(growth_display, style={'color': growth_color})],
        [html.H5("💵 Revenue/Customer", className="card-title"), html.H4(f"${revenue_per_customer:,.2f}")]
    )

# 2️ Update Monthly Revenue (existing)
@app.callback(
    Output('monthly-revenue-graph', 'figure'),
    Input('country-dropdown', 'value'),
    Input('date-range', 'start_date'),
    Input('date-range', 'end_date'),
    Input('compare-dropdown', 'value')
)
def update_monthly_revenue(selected_country, start_date, end_date, compare):
    if not selected_country:
        return px.line(title="No country selected")
    
    date_condition = get_date_condition(start_date, end_date)
    country_escaped = selected_country.replace("'", "''")
    
    query = f"""
        SELECT DATE_TRUNC('month', invoicedate) as month,
               COALESCE(SUM(net_revenue), 0) as revenue
        FROM sales_data
        WHERE country = '{country_escaped}' {date_condition}
        GROUP BY month
        ORDER BY month
    """
    df = run_query(query, engine)
    
    if df.empty:
        return px.line(title=f"No data for {selected_country}")
    
    df['month_str'] = df['month'].dt.strftime('%b %Y')
    fig = px.line(df, x='month_str', y='revenue', markers=True, title=f'Monthly Revenue - {selected_country}')
    fig.update_layout(xaxis_title='Month', yaxis_title='Revenue ($)', template='plotly_white')
    
    # Add comparison if selected
    if compare == 'yoy' and start_date and end_date:
        # Add YoY comparison logic here
        pass
    
    return fig

# 3️ NEW: Sales by Day of Week
@app.callback(
    Output('sales-by-day-graph', 'figure'),
    Input('country-dropdown', 'value'),
    Input('date-range', 'start_date'),
    Input('date-range', 'end_date')
)
def sales_by_day(selected_country, start_date, end_date):
    date_condition = get_date_condition(start_date, end_date)
    country_escaped = selected_country.replace("'", "''") if selected_country else ""
    
    query = f"""
        SELECT EXTRACT(DOW FROM invoicedate) as day_num,
               TO_CHAR(invoicedate, 'Day') as day_name,
               COALESCE(SUM(net_revenue), 0) as revenue,
               COUNT(*) as transactions
        FROM sales_data
        WHERE country = '{country_escaped}' {date_condition}
        GROUP BY day_num, day_name
        ORDER BY day_num
    """
    df = run_query(query, engine)
    
    if df.empty:
        return px.bar(title="No data available")
    
    fig = px.bar(df, x='day_name', y='revenue', title=f'Sales by Day of Week - {selected_country}', text_auto='.2s')
    fig.update_layout(xaxis_title='Day', yaxis_title='Revenue ($)')
    return fig

# 4️ FIXED: Sales Heatmap (Hour vs Day)
@app.callback(
    Output('sales-heatmap', 'figure'),
    Input('country-dropdown', 'value'),
    Input('date-range', 'start_date'),
    Input('date-range', 'end_date')
)
def sales_heatmap(selected_country, start_date, end_date):
    try:
        date_condition = get_date_condition(start_date, end_date)
        country_escaped = selected_country.replace("'", "''") if selected_country else ""
        
        # First check if hour extraction works
        query = f"""
            SELECT EXTRACT(DOW FROM invoicedate) as day_num,
                   EXTRACT(HOUR FROM invoicedate) as hour,
                   COALESCE(SUM(net_revenue), 0) as revenue
            FROM sales_data
            WHERE country = '{country_escaped}' {date_condition}
            GROUP BY day_num, hour
            ORDER BY day_num, hour
        """
        df = run_query(query, engine)
        
        if df.empty or len(df) == 0:
            # Return empty figure with message
            fig = go.Figure()
            fig.add_annotation(
                text="No data available for heatmap",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False
            )
            fig.update_layout(title=f'Sales Heatmap - {selected_country} (No Data)')
            return fig
        
        # Check if we have valid data for pivot
        if df['hour'].isna().all() or df['day_num'].isna().all():
            fig = go.Figure()
            fig.add_annotation(
                text="Time data not available",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False
            )
            return fig
        
        # Create pivot table with error handling
        try:
            pivot = df.pivot_table(index='hour', columns='day_num', values='revenue', fill_value=0)
            # Ensure we have all days
            day_labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            fig = px.imshow(pivot,
                           labels=dict(x="Day", y="Hour", color="Revenue"),
                           x=day_labels[:len(pivot.columns)],
                           title=f'Sales Heatmap (Hour vs Day) - {selected_country}',
                           aspect="auto",
                           color_continuous_scale="Viridis")
            return fig
        except Exception as pivot_error:
            print(f"Pivot error: {pivot_error}")
            fig = go.Figure()
            fig.add_annotation(
                text="Error creating heatmap",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False
            )
            return fig
    except Exception as e:
        print(f"Error in sales_heatmap: {str(e)}")
        fig = go.Figure()
        fig.add_annotation(
            text=f"Error: {str(e)[:50]}",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False
        )
        return fig

# 5️ NEW: Customer Segments (RFM-style)
@app.callback(
    Output('customer-segments', 'figure'),
    Input('country-dropdown', 'value'),
    Input('date-range', 'start_date'),
    Input('date-range', 'end_date')
)
def customer_segments(selected_country, start_date, end_date):
    date_condition = get_date_condition(start_date, end_date)
    country_escaped = selected_country.replace("'", "''") if selected_country else ""
    
    query = f"""
        SELECT customerid,
               COUNT(*) as frequency,
               COALESCE(SUM(net_revenue), 0) as monetary,
               MAX(invoicedate) as last_purchase
        FROM sales_data
        WHERE country = '{country_escaped}' {date_condition}
        GROUP BY customerid
    """
    df = run_query(query, engine)
    
    if df.empty:
        return px.scatter(title="No customer data")
    
    # Create segments
    df['segment'] = pd.qcut(df['monetary'], q=4, labels=['Bronze', 'Silver', 'Gold', 'Platinum'])
    segment_summary = df.groupby('segment').agg({
        'customerid': 'count',
        'monetary': 'mean'
    }).reset_index()
    
    fig = px.bar(segment_summary, x='segment', y='monetary', title=f'Customer Segments by Value - {selected_country}', text_auto='.2s')
    return fig

# 6️ Geographic Map - with warning suppressed
@app.callback(
    Output('geographic-map', 'figure'),
    Input('date-range', 'start_date'),
    Input('date-range', 'end_date')
)
def geographic_map(start_date, end_date):
    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    
    try:
        date_condition = get_date_condition(start_date, end_date)
        
        query = f"""
            SELECT country,
                   COALESCE(SUM(net_revenue), 0) as revenue,
                   COUNT(DISTINCT customerid) as customers
            FROM sales_data
            WHERE country != 'Unspecified' AND country IS NOT NULL {date_condition}
            GROUP BY country
            ORDER BY revenue DESC
        """
        df = run_query(query, engine)
        
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No geographic data available",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False
            )
            fig.update_layout(title='Global Revenue Distribution (No Data)')
            return fig
        
        fig = px.choropleth(df,
                           locations='country',
                           locationmode='country names',
                           color='revenue',
                           hover_name='country',
                           title='Global Revenue Distribution',
                           color_continuous_scale='Viridis')
        return fig
    except Exception as e:
        print(f"Error in geographic_map: {str(e)}")
        return go.Figure()

# 7️ Update Top Products Bar (enhanced)
@app.callback(
    Output('top-products-bar', 'figure'),
    Input('country-dropdown', 'value'),
    Input('product-dropdown', 'value'),
    Input('date-range', 'start_date'),
    Input('date-range', 'end_date')
)
def update_top_products(selected_country, selected_products, start_date, end_date):
    date_condition = get_date_condition(start_date, end_date)
    country_escaped = selected_country.replace("'", "''") if selected_country else ""
    
    if not selected_products:
        query = f"""
            SELECT description,
                   COALESCE(SUM(net_revenue), 0) as revenue,
                   COUNT(*) as transactions
            FROM sales_data
            WHERE country = '{country_escaped}' {date_condition}
            AND description IS NOT NULL
            GROUP BY description
            ORDER BY revenue DESC
            LIMIT 10
        """
    else:
        product_list = "', '".join([p.replace("'", "''") for p in selected_products])
        query = f"""
            SELECT description,
                   COALESCE(SUM(net_revenue), 0) as revenue,
                   COUNT(*) as transactions
            FROM sales_data
            WHERE country = '{country_escaped}' {date_condition}
            AND description IN ('{product_list}')
            GROUP BY description
            ORDER BY revenue DESC
        """
    
    df = run_query(query, engine)
    
    if df.empty:
        return px.bar(title="No product data available")
    
    fig = px.bar(df, x='revenue', y='description', orientation='h', title=f'Top Products by Revenue - {selected_country}', text_auto='.2s')
    fig.update_layout(xaxis_title='Revenue ($)', yaxis_title='Product')
    return fig

# 8️ Quick filter callback
@app.callback(
    Output('date-range', 'start_date'),
    Output('date-range', 'end_date'),
    Input('quick-filter', 'value')
)
def update_date_range(quick_filter):
    end_date = max_date
    
    if quick_filter == '30d':
        start_date = end_date - timedelta(days=30)
    elif quick_filter == 'quarter':
        start_date = end_date - timedelta(days=90)
    elif quick_filter == 'year':
        start_date = end_date - timedelta(days=365)
    else:  # all
        start_date = min_date
    
    return start_date, end_date

# 9️ Download CSV callback (enhanced)
@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("download-button", "n_clicks"),
    State('country-dropdown', 'value'),
    State('date-range', 'start_date'),
    State('date-range', 'end_date'),
    prevent_initial_call=True
)
def download_csv(n_clicks, selected_country, start_date, end_date):
    if not selected_country:
        return None
    
    date_condition = get_date_condition(start_date, end_date)
    country_escaped = selected_country.replace("'", "''")
    
    query = f"""
        SELECT *
        FROM sales_data
        WHERE country = '{country_escaped}' {date_condition}
        ORDER BY invoicedate DESC
    """
    df = run_query(query, engine)
    
    # Add summary stats
    filename = f"sales_data_{selected_country}_{start_date[:10]}_to_{end_date[:10]}.csv"
    return dcc.send_data_frame(df.to_csv, filename, index=False)
# For local development - simpler settings

server = app.server   #
if __name__ == "__main__":
    import os
    
    # Get settings from environment variables with defaults
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.getenv('PORT', 10000))
    host = os.getenv('HOST', '0.0.0.0')
    
    app.run(debug=debug_mode, host=host, port=port)
