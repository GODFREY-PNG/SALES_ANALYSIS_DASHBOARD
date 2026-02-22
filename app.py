# app.py - Interactive Sales Dashboard (Mobile Optimized)
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
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], meta_tags=[
    {"name": "viewport", "content": "width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no"}
])
app.title = "Enhanced Sales Dashboard"

# Custom CSS for card styling + mobile responsiveness
CARD_STYLE = {
    'padding': '12px',
    'margin': '6px',
    'border-radius': '8px',
    'box-shadow': '2px 2px 10px rgba(0,0,0,0.1)',
    'background-color': 'white'
}

MOBILE_CSS = """
/* ── Global mobile resets ── */
* { box-sizing: border-box; }

body {
    -webkit-text-size-adjust: 100%;
    overflow-x: hidden;
}

/* ── Viewport meta already injected; ensure no horizontal scroll ── */
.container-fluid { padding-left: 8px !important; padding-right: 8px !important; }

/* ── KPI cards: stack 2-per-row on small screens ── */
@media (max-width: 575px) {

    /* Two KPI columns side-by-side */
    .kpi-col {
        flex: 0 0 50% !important;
        max-width: 50% !important;
        padding: 3px !important;
    }

    /* Smaller headings inside KPI cards */
    .kpi-col h5 { font-size: 0.72rem !important; margin-bottom: 2px; }
    .kpi-col h4 { font-size: 1rem !important; margin: 0; }

    /* Full-width filter & chart columns */
    .filter-col, .chart-col {
        flex: 0 0 100% !important;
        max-width: 100% !important;
        padding: 3px !important;
    }

    /* Reduce card padding on mobile */
    .card { padding: 10px !important; margin: 4px !important; }

    /* Date picker: prevent overflow */
    .DateRangePickerInput { flex-wrap: wrap; }
    .DateInput { width: 100% !important; }

    /* Plotly graphs: allow full width */
    .js-plotly-plot, .plotly { width: 100% !important; }

    /* Radio items: stack vertically */
    .form-check-inline { display: block !important; margin-bottom: 4px; }

    /* Dashboard title */
    h1 { font-size: 1.3rem !important; }

    /* Download button full width */
    #download-button { width: 100%; }
}

/* ── Medium screens (tablets): 2-column KPI grid ── */
@media (min-width: 576px) and (max-width: 767px) {
    .kpi-col {
        flex: 0 0 50% !important;
        max-width: 50% !important;
    }
    .filter-col, .chart-col {
        flex: 0 0 100% !important;
        max-width: 100% !important;
    }
    h1 { font-size: 1.5rem !important; }
}

/* ── Plotly modebar: hide on touch to save space ── */
@media (max-width: 767px) {
    .modebar { display: none !important; }
    .plotly .main-svg { border-radius: 6px; }
}

/* ── Touch-friendly dropdowns & inputs ── */
.Select-control, .DateInput_input {
    min-height: 44px !important;
    font-size: 1rem !important;
}

/* ── Scrollable product dropdown on mobile ── */
.Select-menu-outer { max-height: 200px !important; overflow-y: auto; }
"""

# Layout
app.layout = dbc.Container([

    # Inject mobile CSS
    html.Style(MOBILE_CSS),

    # Header
    dbc.Row([
        dbc.Col(html.H1("📊 Sales Dashboard", className="text-center mb-3 mt-2"), width=12)
    ]),

    # Date Range Filter + Quick Filters
    dbc.Row([
        dbc.Col(
            dbc.Card([
                html.Label("📅 Date Range:", className="fw-bold"),
                dcc.DatePickerRange(
                    id='date-range',
                    start_date=min_date,
                    end_date=max_date,
                    min_date_allowed=min_date,
                    max_date_allowed=max_date,
                    display_format='YYYY-MM-DD',
                    className="mt-2",
                    style={'width': '100%'}
                )
            ], style=CARD_STYLE),
            xs=12, md=6, className="filter-col"
        ),
        dbc.Col(
            dbc.Card([
                html.Label("⚡ Quick Filters:", className="fw-bold"),
                dbc.RadioItems(
                    id='quick-filter',
                    options=[
                        {'label': '30d', 'value': '30d'},
                        {'label': 'Quarter', 'value': 'quarter'},
                        {'label': 'Year', 'value': 'year'},
                        {'label': 'All', 'value': 'all'}
                    ],
                    value='all',
                    inline=True,
                    className="mt-2"
                )
            ], style=CARD_STYLE),
            xs=12, md=6, className="filter-col"
        )
    ], className="mb-2 g-1"),

    # Main KPIs Row 1 — 2 cols on mobile, 4 on desktop
    dbc.Row([
        dbc.Col(html.Div(id='total-revenue-card',     style=CARD_STYLE), xs=6, md=3, className="kpi-col"),
        dbc.Col(html.Div(id='total-transactions-card', style=CARD_STYLE), xs=6, md=3, className="kpi-col"),
        dbc.Col(html.Div(id='avg-order-card',          style=CARD_STYLE), xs=6, md=3, className="kpi-col"),
        dbc.Col(html.Div(id='total-customers-card',    style=CARD_STYLE), xs=6, md=3, className="kpi-col"),
    ], className="mb-1 g-1"),

    # Main KPIs Row 2
    dbc.Row([
        dbc.Col(html.Div(id='return-rate-card',         style=CARD_STYLE), xs=6, md=3, className="kpi-col"),
        dbc.Col(html.Div(id='items-per-trans-card',     style=CARD_STYLE), xs=6, md=3, className="kpi-col"),
        dbc.Col(html.Div(id='revenue-growth-card',      style=CARD_STYLE), xs=6, md=3, className="kpi-col"),
        dbc.Col(html.Div(id='revenue-per-customer-card', style=CARD_STYLE), xs=6, md=3, className="kpi-col"),
    ], className="mb-2 g-1"),

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
            xs=12, md=4, className="filter-col"
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
            xs=12, md=4, className="filter-col"
        ),
        dbc.Col(
            dbc.Card([
                html.Label("📈 Compare:", className="fw-bold"),
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
            xs=12, md=4, className="filter-col"
        )
    ], className="mb-2 g-1"),

    # Charts Row 1 — full width on mobile
    dbc.Row([
        dbc.Col(dcc.Graph(id='monthly-revenue-graph', config={'displayModeBar': False, 'responsive': True}),
                xs=12, md=6, className="chart-col"),
        dbc.Col(dcc.Graph(id='sales-by-day-graph', config={'displayModeBar': False, 'responsive': True}),
                xs=12, md=6, className="chart-col"),
    ], className="mb-2 g-1"),

    # Charts Row 2
    dbc.Row([
        dbc.Col(dcc.Graph(id='top-products-bar', config={'displayModeBar': False, 'responsive': True}),
                xs=12, md=6, className="chart-col"),
        dbc.Col(dcc.Graph(id='sales-heatmap', config={'displayModeBar': False, 'responsive': True}),
                xs=12, md=6, className="chart-col"),
    ], className="mb-2 g-1"),

    # Charts Row 3
    dbc.Row([
        dbc.Col(dcc.Graph(id='customer-segments', config={'displayModeBar': False, 'responsive': True}),
                xs=12, md=6, className="chart-col"),
        dbc.Col(dcc.Graph(id='geographic-map', config={'displayModeBar': False, 'responsive': True}),
                xs=12, md=6, className="chart-col"),
    ], className="mb-2 g-1"),

    # Download Section
    dbc.Row([
        dbc.Col(
            dbc.Card([
                html.Label("📥 Download Report:", className="fw-bold"),
                dbc.Button("Download Filtered Data", id="download-button", color="primary",
                           className="mt-2 w-100"),
                dcc.Download(id="download-dataframe-csv")
            ], style=CARD_STYLE),
            xs=12, md=4, className="filter-col"
        )
    ], className="mb-3 g-1")

], fluid=True, style={'background-color': '#f8f9fa', 'padding': '8px'})


# Helper function to get date filter condition
def get_date_condition(start_date, end_date):
    if start_date and end_date:
        return f"AND invoicedate BETWEEN '{start_date}' AND '{end_date}'"
    return ""


# ── Mobile-friendly chart layout helper ──
def mobile_layout(fig, title=""):
    fig.update_layout(
        title=dict(text=title, font=dict(size=13)),
        margin=dict(l=8, r=8, t=36, b=8),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=10)),
        font=dict(size=11),
        autosize=True,
        template='plotly_white',
    )
    return fig


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

    if start_date and end_date:
        days_diff = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days
        prev_start = pd.to_datetime(start_date) - timedelta(days=days_diff)
        prev_end = pd.to_datetime(start_date) - timedelta(days=1)

        data_quality_query = f"""
            SELECT COUNT(DISTINCT DATE(invoicedate)) as days_with_data,
                   COUNT(*) as total_records
            FROM sales_data
            WHERE country = '{country_escaped}'
            AND invoicedate BETWEEN '{prev_start}' AND '{prev_end}'
        """
        quality_df = run_query(data_quality_query, engine)
        days_with_data = int(quality_df['days_with_data'].iloc[0])

        growth_query = f"""
            SELECT COALESCE(SUM(net_revenue), 0) as prev_revenue
            FROM sales_data
            WHERE country = '{country_escaped}'
            AND invoicedate BETWEEN '{prev_start}' AND '{prev_end}'
        """
        prev_df = run_query(growth_query, engine)
        prev_revenue = float(prev_df['prev_revenue'].iloc[0])

        expected_days = days_diff
        data_completeness = (days_with_data / expected_days) * 100 if expected_days > 0 else 0
    else:
        prev_revenue = 0
        data_completeness = 0

    total_revenue = float(df['total_revenue'].iloc[0])
    total_transactions = int(df['total_transactions'].iloc[0])
    avg_order = float(df['avg_order'].iloc[0])
    total_customers = int(df['total_customers'].iloc[0])
    return_rate = (float(df['return_qty'].iloc[0]) / float(df['total_qty'].iloc[0]) * 100) if float(df['total_qty'].iloc[0]) > 0 else 0
    avg_items = round(float(df['avg_items'].iloc[0]))

    if prev_revenue > 0:
        growth = ((total_revenue - prev_revenue) / prev_revenue) * 100
        if data_completeness < 80:
            growth_display = f"{growth:+.1f}%*"
            growth_color = "orange"
        else:
            growth_display = f"{growth:+.1f}%"
            growth_color = "green" if growth >= 0 else "red"
    else:
        growth_display = "N/A"
        growth_color = "gray"

    revenue_per_customer = total_revenue / total_customers if total_customers > 0 else 0

    # Compact KPI card helper
    def kpi(icon, label, value, color=None):
        val_style = {'margin': 0, 'color': color} if color else {'margin': 0}
        return [
            html.P(f"{icon} {label}", style={'fontSize': '0.72rem', 'marginBottom': '2px', 'color': '#555', 'fontWeight': '600'}),
            html.H4(value, style=val_style)
        ]

    return (
        kpi("💰", "Revenue",     f"${total_revenue:,.0f}"),
        kpi("📊", "Transactions", f"{total_transactions:,}"),
        kpi("🛒", "Avg Order",   f"${avg_order:,.0f}"),
        kpi("👥", "Customers",   f"{total_customers:,}"),
        kpi("↩️", "Return Rate", f"{return_rate:.1f}%"),
        kpi("📦", "Items/Trans", f"{avg_items:.1f}"),
        kpi("📈", "Growth",      growth_display, growth_color),
        kpi("💵", "Rev/Customer", f"${revenue_per_customer:,.0f}"),
    )


# 2️ Update Monthly Revenue
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

    df['month_str'] = df['month'].dt.strftime('%b %y')
    fig = px.line(df, x='month_str', y='revenue', markers=True)
    fig = mobile_layout(fig, f'Monthly Revenue — {selected_country}')
    fig.update_layout(xaxis_title='', yaxis_title='Revenue ($)')

    if compare == 'yoy' and start_date and end_date:
        pass

    return fig


# 3️ Sales by Day of Week
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

    # Trim whitespace from day names for mobile
    df['day_name'] = df['day_name'].str.strip().str[:3]
    fig = px.bar(df, x='day_name', y='revenue', text_auto='.2s')
    fig = mobile_layout(fig, f'Sales by Day — {selected_country}')
    fig.update_layout(xaxis_title='', yaxis_title='Revenue ($)')
    return fig


# 4️ Sales Heatmap (Hour vs Day)
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

        def empty_fig(msg):
            fig = go.Figure()
            fig.add_annotation(text=msg, xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            fig = mobile_layout(fig, f'Sales Heatmap — {selected_country}')
            return fig

        if df.empty or len(df) == 0:
            return empty_fig("No data available for heatmap")

        if df['hour'].isna().all() or df['day_num'].isna().all():
            return empty_fig("Time data not available")

        try:
            pivot = df.pivot_table(index='hour', columns='day_num', values='revenue', fill_value=0)
            day_labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            fig = px.imshow(pivot,
                            labels=dict(x="Day", y="Hour", color="Revenue"),
                            x=day_labels[:len(pivot.columns)],
                            aspect="auto",
                            color_continuous_scale="Viridis")
            fig = mobile_layout(fig, f'Heatmap: Hour vs Day — {selected_country}')
            return fig
        except Exception as pivot_error:
            print(f"Pivot error: {pivot_error}")
            return empty_fig("Error creating heatmap")
    except Exception as e:
        print(f"Error in sales_heatmap: {str(e)}")
        fig = go.Figure()
        fig.add_annotation(text=f"Error: {str(e)[:50]}", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig


# 5️ Customer Segments (RFM-style)
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

    df['segment'] = pd.qcut(df['monetary'], q=4, labels=['Bronze', 'Silver', 'Gold', 'Platinum'])
    segment_summary = df.groupby('segment').agg({
        'customerid': 'count',
        'monetary': 'mean'
    }).reset_index()

    fig = px.bar(segment_summary, x='segment', y='monetary', text_auto='.2s')
    fig = mobile_layout(fig, f'Customer Segments — {selected_country}')
    fig.update_layout(xaxis_title='', yaxis_title='Avg Revenue ($)')
    return fig


# 6️ Geographic Map
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
            fig.add_annotation(text="No geographic data available", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            fig = mobile_layout(fig, 'Global Revenue Distribution (No Data)')
            return fig

        fig = px.choropleth(df,
                            locations='country',
                            locationmode='country names',
                            color='revenue',
                            hover_name='country',
                            color_continuous_scale='Viridis')
        fig = mobile_layout(fig, 'Global Revenue Distribution')
        # Compact geo projection for mobile
        fig.update_geos(
            showframe=False,
            showcoastlines=True,
            projection_type='natural earth'
        )
        fig.update_layout(
            coloraxis_colorbar=dict(thickness=10, len=0.5, title=dict(text='$', side='right'))
        )
        return fig
    except Exception as e:
        print(f"Error in geographic_map: {str(e)}")
        return go.Figure()


# 7️ Top Products Bar
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

    # Truncate long product names for mobile
    df['description'] = df['description'].str[:30]
    fig = px.bar(df, x='revenue', y='description', orientation='h', text_auto='.2s')
    fig = mobile_layout(fig, f'Top Products — {selected_country}')
    fig.update_layout(xaxis_title='Revenue ($)', yaxis_title='')
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
    else:
        start_date = min_date

    return start_date, end_date


# 9️ Download CSV callback
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

    filename = f"sales_data_{selected_country}_{start_date[:10]}_to_{end_date[:10]}.csv"
    return dcc.send_data_frame(df.to_csv, filename, index=False)


server = app.server
if __name__ == "__main__":
    import os

    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.getenv('PORT', 10000))
    host = os.getenv('HOST', '0.0.0.0')

    app.run(debug=debug_mode, host=host, port=port)
