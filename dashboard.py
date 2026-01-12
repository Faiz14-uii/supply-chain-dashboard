"""
Supply Chain Performance Dashboard
Business Intelligence - Professional Enterprise Dashboard
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import numpy as np
import time
import os

# ==================== CONFIG ====================
st.set_page_config(
    page_title="Supply Chain Dashboard",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CUSTOM CSS ====================
st.markdown("""
<style>
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
    }
    
    /* Card styling */
    .metric-card {
        background: rgba(42, 82, 152, 0.4);
        border-radius: 15px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
    }
    
    /* KPI cards */
    div[data-testid="stMetricValue"] {
        font-size: 32px;
        font-weight: 700;
        color: #ffffff;
    }
    
    div[data-testid="stMetricLabel"] {
        font-size: 14px;
        color: #b8d4f1;
    }
    
    /* Headers */
    h1 {
        color: #ffffff;
        font-weight: 700;
        text-align: center;
        margin-bottom: 5px;
    }
    
    h3 {
        color: #e8f1ff;
        font-weight: 600;
        font-size: 18px;
    }
    
    /* Subtitle */
    .subtitle {
        text-align: center;
        color: #b8d4f1;
        font-size: 16px;
        margin-bottom: 30px;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: rgba(30, 60, 114, 0.95);
    }
    
    section[data-testid="stSidebar"] .stSelectbox label {
        color: #ffffff;
    }
    
    /* Remove padding */
    .block-container {
        padding-top: 1rem;
    }
    
    /* Pulse animation for live indicator */
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    .live-indicator {
        animation: pulse 2s infinite;
    }
</style>

<script>
    // Auto-refresh every 5 minutes
    setTimeout(function() {
        window.location.reload();
    }, 300000); // 300000ms = 5 minutes
</script>
""", unsafe_allow_html=True)

# ==================== LOAD DATA ====================
@st.cache_data(ttl=300)  # Cache for 5 minutes (300 seconds)
def load_data():
    """Load all data files - refreshes every 5 minutes"""
    # Check all required files
    required_files = [
        'outputs/dashboard_ready.csv',
        'outputs/supplier_clusters.csv',
        'outputs/time_series_forecast_arima.csv',
        'outputs/supplier_cluster_features.csv'
    ]
    missing = [f for f in required_files if not os.path.exists(f)]
    if missing:
        st.error(f"File berikut tidak ditemukan: {', '.join(missing)}.\n\nPastikan file sudah ada di GitHub dan path benar.")
        st.stop()

    df = pd.read_csv('outputs/dashboard_ready.csv')
    df['order_date'] = pd.to_datetime(df['order_date'])

    supplier_clusters = pd.read_csv('outputs/supplier_clusters.csv')

    # Load time series forecast
    forecast_df = pd.read_csv('outputs/time_series_forecast_arima.csv')
    forecast_df['date'] = pd.to_datetime(forecast_df['date'])

    # Load cluster features
    cluster_features = pd.read_csv('outputs/supplier_cluster_features.csv')

    return df, supplier_clusters, forecast_df, cluster_features, datetime.now()

df, supplier_clusters, forecast_df, cluster_features, last_update = load_data()

# ==================== SIDEBAR FILTERS ====================
st.sidebar.title("🔍 Filters")

# Date range filter
min_date = df['order_date'].min().date()
max_date = df['order_date'].max().date()

date_range = st.sidebar.date_input(
    "Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Supplier filter
suppliers = ['All'] + sorted(df['supplier_name'].unique().tolist())
selected_supplier = st.sidebar.selectbox("Supplier", suppliers)

# Cluster filter
clusters = ['All'] + sorted(df['cluster_label'].unique().tolist())
selected_cluster = st.sidebar.selectbox("Cluster", clusters)

# Transportation mode filter
transport_modes = ['All'] + sorted(df['transportation_modes'].unique().tolist())
selected_transport = st.sidebar.selectbox("Transportation Mode", transport_modes)

# ==================== APPLY FILTERS ====================
filtered_df = df.copy()

# Date filter
if len(date_range) == 2:
    start_date, end_date = date_range
    filtered_df = filtered_df[
        (filtered_df['order_date'].dt.date >= start_date) & 
        (filtered_df['order_date'].dt.date <= end_date)
    ]

# Supplier filter
if selected_supplier != 'All':
    filtered_df = filtered_df[filtered_df['supplier_name'] == selected_supplier]

# Cluster filter
if selected_cluster != 'All':
    filtered_df = filtered_df[filtered_df['cluster_label'] == selected_cluster]

# Transport filter
if selected_transport != 'All':
    filtered_df = filtered_df[filtered_df['transportation_modes'] == selected_transport]

# ==================== HEADER ====================
st.markdown("<h1>📦 Supply Chain Performance Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Real-time insights for operational excellence</p>", unsafe_allow_html=True)

st.markdown("---")

# ==================== CHECK IF DATA IS EMPTY ====================
if len(filtered_df) == 0:
    st.warning("⚠️ No data available for the selected filters. Please adjust your filter criteria.")
    st.info("""
    **Suggestions:**
    - Expand the date range
    - Select 'All' for supplier, cluster, or transportation mode
    - Check if the selected combination has any data
    """)
    st.stop()

# ==================== KPI CARDS ====================
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    avg_shipping_time = filtered_df['shipping_times'].mean() if len(filtered_df) > 0 else 0
    min_ship = filtered_df['shipping_times'].min() if len(filtered_df) > 0 else 0
    max_ship = filtered_df['shipping_times'].max() if len(filtered_df) > 0 else 0
    st.metric(
        label="⏱️ Avg Shipping Time",
        value=f"{avg_shipping_time:.1f} days",
        delta=f"{avg_shipping_time - df['shipping_times'].mean():.1f}",
        help=f"Min: {min_ship:.0f}d | Max: {max_ship:.0f}d"
    )

with col2:
    avg_cost = filtered_df['costs'].mean() if len(filtered_df) > 0 else 0
    total_cost = filtered_df['costs'].sum() if len(filtered_df) > 0 else 0
    st.metric(
        label="💰 Avg Transport Cost",
        value=f"${avg_cost:.2f}",
        delta=f"${avg_cost - df['costs'].mean():.2f}",
        delta_color="inverse",
        help=f"Total Cost: ${total_cost:,.2f}"
    )

with col3:
    total_revenue = filtered_df['revenue_generated'].sum() if len(filtered_df) > 0 else 0
    avg_revenue = filtered_df['revenue_generated'].mean() if len(filtered_df) > 0 else 0
    total_revenue_all = df['revenue_generated'].sum()
    delta_pct = ((total_revenue / total_revenue_all - 1) * 100) if total_revenue_all > 0 else 0
    st.metric(
        label="💵 Total Revenue",
        value=f"${total_revenue:,.0f}",
        delta=f"{delta_pct:.1f}%",
        help=f"Avg per order: ${avg_revenue:,.2f}"
    )

with col4:
    total_profit = filtered_df['profit'].sum() if len(filtered_df) > 0 else 0
    profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
    st.metric(
        label="📈 Total Profit",
        value=f"${total_profit:,.0f}",
        delta=f"{profit_margin:.1f}% margin",
        help=f"Profit margin across all orders"
    )

with col5:
    total_orders = len(filtered_df)
    avg_defect = filtered_df['defect_rates'].mean() if len(filtered_df) > 0 else 0
    st.metric(
        label="📦 Total Orders",
        value=f"{total_orders:,}",
        delta=f"{avg_defect:.2f}% defect",
        delta_color="inverse",
        help=f"Average defect rate"
    )

st.markdown("<br>", unsafe_allow_html=True)

# ==================== SECOND ROW KPI ====================
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_suppliers = filtered_df['supplier_name'].nunique()
    # Safe handling for best_supplier
    if total_suppliers > 0:
        supplier_profits = filtered_df.groupby('supplier_name')['profit'].sum()
        if len(supplier_profits) > 0:
            best_supplier = supplier_profits.idxmax()
        else:
            best_supplier = "N/A"
    else:
        best_supplier = "N/A"
    
    st.metric(
        label="🏭 Active Suppliers",
        value=f"{total_suppliers}",
        help=f"Best performer: {best_supplier}"
    )

with col2:
    avg_lead_time = filtered_df['lead_times'].mean() if len(filtered_df) > 0 else 0
    st.metric(
        label="🕐 Avg Lead Time",
        value=f"{avg_lead_time:.1f} days",
        delta=f"{avg_lead_time - df['lead_times'].mean():.1f}",
        help=f"Time from order to production"
    )

with col3:
    on_time_delivery = (filtered_df['shipping_times'] <= filtered_df['shipping_times'].quantile(0.5)).sum()
    on_time_pct = (on_time_delivery / len(filtered_df) * 100) if len(filtered_df) > 0 else 0
    st.metric(
        label="✅ On-Time Delivery",
        value=f"{on_time_pct:.1f}%",
        delta=f"{on_time_delivery} orders",
        help="Orders delivered within median time"
    )

with col4:
    quality_pass = (filtered_df['inspection_results'] == 'Pass').sum()
    quality_pct = (quality_pass / len(filtered_df) * 100) if len(filtered_df) > 0 else 0
    st.metric(
        label="🎯 Quality Pass Rate",
        value=f"{quality_pct:.1f}%",
        delta=f"{quality_pass}/{len(filtered_df)}",
        help="Orders passing quality inspection"
    )

st.markdown("<br>", unsafe_allow_html=True)

# ==================== EXECUTIVE INSIGHT ====================
st.markdown("""
<div style='background: rgba(100, 181, 246, 0.15); padding: 20px; border-radius: 12px; border-left: 5px solid #64b5f6; margin-bottom: 20px;'>
    <h4 style='color: #64b5f6; margin: 0 0 10px 0;'>📊 Executive Summary</h4>
    <p style='color: #e8f1ff; font-size: 14px; line-height: 1.6; margin: 0;'>
        Dashboard ini menampilkan performa supply chain secara real-time dengan fokus pada efisiensi operasional dan profitabilitas. 
        Rata-rata waktu pengiriman saat ini menunjukkan kondisi operasional supply chain, sementara biaya transportasi dan revenue 
        memberikan gambaran kesehatan finansial. Quality pass rate dan defect rate menjadi indikator kualitas produk yang krusial 
        untuk kepuasan pelanggan. Data teragregasi dari seluruh supplier membantu identifikasi bottleneck dan peluang improvement 
        untuk optimasi supply chain yang lebih efektif.
    </p>
</div>
""", unsafe_allow_html=True)

# ==================== MAIN CHARTS SECTION ====================

# Row 1: Trend Chart (Full Width)
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 📈 Tren Waktu Pengiriman & Biaya (Per Minggu)")
    trend_data = filtered_df.groupby(filtered_df['order_date'].dt.to_period('W').astype(str)).agg({
        'shipping_times': 'mean',
        'costs': 'mean',
        'revenue_generated': 'sum',
        'profit': 'sum',
        'defect_rates': 'mean'
    }).reset_index()
    trend_data.columns = ['week', 'avg_shipping_time', 'avg_cost', 'total_revenue', 'total_profit', 'avg_defect']
    
    # Simplify week labels
    trend_data['week_short'] = trend_data['week'].str.replace('2024-', 'W').str.replace('2025-', 'W')
    
    fig_trend = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig_trend.add_trace(
        go.Scatter(
            x=trend_data['week_short'],
            y=trend_data['avg_shipping_time'],
            name="Waktu Kirim (hari)",
            fill='tozeroy',
            line=dict(color='#64b5f6', width=3),
            fillcolor='rgba(100, 181, 246, 0.3)',
            hovertemplate='<b>%{x}</b><br>Waktu Kirim: %{y:.1f} hari<extra></extra>',
            mode='lines+markers',
            marker=dict(size=6)
        ),
        secondary_y=False
    )
    
    fig_trend.add_trace(
        go.Scatter(
            x=trend_data['week_short'],
            y=trend_data['avg_cost'],
            name="Biaya Transport ($)",
            line=dict(color='#81c784', width=3),
            hovertemplate='<b>%{x}</b><br>Biaya: $%{y:.2f}<extra></extra>',
            mode='lines+markers',
            marker=dict(size=6)
        ),
        secondary_y=True
    )
    
    fig_trend.update_layout(
        height=350,
        plot_bgcolor='rgba(42, 82, 152, 0.3)',
        paper_bgcolor='rgba(42, 82, 152, 0.3)',
        font=dict(color='#ffffff', size=13),
        xaxis=dict(showgrid=False, title="Minggu", tickangle=0, tickfont=dict(size=11)),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title=dict(text="Waktu Kirim (hari)", font=dict(size=13))),
        yaxis2=dict(showgrid=False, title=dict(text="Biaya ($)", font=dict(size=13))),
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5, font=dict(size=12)),
        margin=dict(l=60, r=60, t=40, b=60)
    )
    
    st.plotly_chart(fig_trend, use_container_width=True)

with col2:
    st.markdown("### 📊 Key Insights")
    
    # Calculate insights
    best_week = trend_data.loc[trend_data['total_revenue'].idxmax(), 'week']
    best_revenue = trend_data['total_revenue'].max()
    worst_week = trend_data.loc[trend_data['avg_defect'].idxmax(), 'week']
    avg_weekly_profit = trend_data['total_profit'].mean()
    
    st.markdown(f"""
    <div style='background: rgba(42, 82, 152, 0.4); padding: 15px; border-radius: 10px; margin-bottom: 10px;'>
        <p style='color: #81c784; font-size: 14px; margin: 0;'>🏆 Best Week</p>
        <p style='color: #ffffff; font-size: 18px; font-weight: 600; margin: 5px 0;'>{best_week}</p>
        <p style='color: #b8d4f1; font-size: 12px; margin: 0;'>Revenue: ${best_revenue:,.0f}</p>
    </div>
    
    <div style='background: rgba(42, 82, 152, 0.4); padding: 15px; border-radius: 10px; margin-bottom: 10px;'>
        <p style='color: #ffb74d; font-size: 14px; margin: 0;'>💰 Avg Weekly Profit</p>
        <p style='color: #ffffff; font-size: 18px; font-weight: 600; margin: 5px 0;'>${avg_weekly_profit:,.0f}</p>
    </div>
    
    <div style='background: rgba(42, 82, 152, 0.4); padding: 15px; border-radius: 10px; margin-bottom: 10px;'>
        <p style='color: #e57373; font-size: 14px; margin: 0;'>⚠️ High Defect Week</p>
        <p style='color: #ffffff; font-size: 18px; font-weight: 600; margin: 5px 0;'>{worst_week}</p>
        <p style='color: #b8d4f1; font-size: 12px; margin: 0;'>Needs attention</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Row 2: Donut Charts
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("### 🎯 Pembagian Kategori Supplier")
    cluster_dist = filtered_df['cluster_label'].value_counts()
    
    fig_cluster = go.Figure(data=[go.Pie(
        labels=cluster_dist.index,
        values=cluster_dist.values,
        hole=0.6,
        marker=dict(colors=['#64b5f6', '#81c784', '#ffb74d', '#e57373']),
        textinfo='label+percent',
        textfont=dict(size=14, color='white', family='Arial Black'),
        hovertemplate='<b>%{label}</b><br>Jumlah: %{value} orders<br>Persentase: %{percent}<extra></extra>'
    )])
    
    fig_cluster.update_layout(
        height=300,
        plot_bgcolor='rgba(42, 82, 152, 0.3)',
        paper_bgcolor='rgba(42, 82, 152, 0.3)',
        font=dict(color='#ffffff'),
        showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10),
        annotations=[dict(text=f'<b>{cluster_dist.sum()}</b><br>Total Order', x=0.5, y=0.5, font_size=20, showarrow=False, font=dict(color='white'))]
    )
    
    st.plotly_chart(fig_cluster, use_container_width=True)

with col2:
    st.markdown("### 🚚 Moda Transportasi")
    transport_dist = filtered_df['transportation_modes'].value_counts()
    
    fig_transport = go.Figure(data=[go.Pie(
        labels=transport_dist.index,
        values=transport_dist.values,
        hole=0.6,
        marker=dict(colors=['#90caf9', '#a5d6a7', '#ffcc80', '#ef9a9a']),
        textinfo='label+percent',
        textfont=dict(size=14, color='white', family='Arial Black'),
        hovertemplate='<b>%{label}</b><br>Jumlah: %{value} pengiriman<br>Persentase: %{percent}<extra></extra>'
    )])
    
    fig_transport.update_layout(
        height=300,
        plot_bgcolor='rgba(42, 82, 152, 0.3)',
        paper_bgcolor='rgba(42, 82, 152, 0.3)',
        font=dict(color='#ffffff'),
        showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10),
        annotations=[dict(text=f'<b>{transport_dist.sum()}</b><br>Pengiriman', x=0.5, y=0.5, font_size=20, showarrow=False, font=dict(color='white'))]
    )
    
    st.plotly_chart(fig_transport, use_container_width=True)

with col3:
    st.markdown("### ✅ Status Kualitas")
    inspection_dist = filtered_df['inspection_results'].value_counts()
    
    fig_inspection = go.Figure(data=[go.Pie(
        labels=inspection_dist.index,
        values=inspection_dist.values,
        hole=0.6,
        marker=dict(colors=['#66bb6a', '#ffa726', '#ef5350']),
        textinfo='label+percent',
        textfont=dict(size=14, color='white', family='Arial Black'),
        hovertemplate='<b>%{label}</b><br>Jumlah: %{value} produk<br>Persentase: %{percent}<extra></extra>'
    )])
    
    fig_inspection.update_layout(
        height=300,
        plot_bgcolor='rgba(42, 82, 152, 0.3)',
        paper_bgcolor='rgba(42, 82, 152, 0.3)',
        font=dict(color='#ffffff'),
        showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10),
        annotations=[dict(text=f'<b>{inspection_dist.sum()}</b><br>Inspeksi', x=0.5, y=0.5, font_size=20, showarrow=False, font=dict(color='white'))]
    )
    
    st.plotly_chart(fig_inspection, use_container_width=True)

with col4:
    st.markdown("### 🌍 Lokasi Pengiriman")
    location_dist = filtered_df['location'].value_counts().head(5)
    
    fig_location = go.Figure(data=[go.Pie(
        labels=location_dist.index,
        values=location_dist.values,
        hole=0.6,
        marker=dict(colors=['#ab47bc', '#ec407a', '#5c6bc0', '#26a69a', '#ffa726']),
        textinfo='label+percent',
        textfont=dict(size=14, color='white', family='Arial Black'),
        hovertemplate='<b>%{label}</b><br>Jumlah Order: %{value}<br>Persentase: %{percent}<extra></extra>'
    )])
    
    fig_location.update_layout(
        height=300,
        plot_bgcolor='rgba(42, 82, 152, 0.3)',
        paper_bgcolor='rgba(42, 82, 152, 0.3)',
        font=dict(color='#ffffff'),
        showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10),
        annotations=[dict(text=f'<b>{location_dist.sum()}</b><br>Order', x=0.5, y=0.5, font_size=20, showarrow=False, font=dict(color='white'))]
    )
    
    st.plotly_chart(fig_location, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# Row 3: Revenue & Profit Analysis
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 💰 Pendapatan vs Keuntungan Per Supplier (Top 8)")
    supplier_finance = filtered_df.groupby('supplier_name').agg({
        'revenue_generated': 'sum',
        'profit': 'sum',
        'costs': 'sum'
    }).reset_index().sort_values('revenue_generated', ascending=False).head(8)
    
    fig_finance = go.Figure()
    
    fig_finance.add_trace(go.Bar(
        name='Pendapatan',
        x=supplier_finance['supplier_name'],
        y=supplier_finance['revenue_generated'],
        marker=dict(color='#64b5f6'),
        text=[f'${x/1000:.0f}K' for x in supplier_finance['revenue_generated']],
        textposition='outside',
        textfont=dict(size=13, color='white'),
        hovertemplate='<b>%{x}</b><br>Pendapatan: $%{y:,.0f}<extra></extra>'
    ))
    
    fig_finance.add_trace(go.Bar(
        name='Keuntungan',
        x=supplier_finance['supplier_name'],
        y=supplier_finance['profit'],
        marker=dict(color='#81c784'),
        text=[f'${x/1000:.0f}K' for x in supplier_finance['profit']],
        textposition='outside',
        textfont=dict(size=13, color='white'),
        hovertemplate='<b>%{x}</b><br>Keuntungan: $%{y:,.0f}<extra></extra>'
    ))
    
    fig_finance.update_layout(
        height=380,
        plot_bgcolor='rgba(42, 82, 152, 0.3)',
        paper_bgcolor='rgba(42, 82, 152, 0.3)',
        font=dict(color='#ffffff', size=13),
        xaxis=dict(showgrid=False, title="Supplier", tickangle=0, tickfont=dict(size=12)),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title=dict(text="Jumlah ($)", font=dict(size=14))),
        barmode='group',
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5, font=dict(size=13)),
        margin=dict(l=60, r=50, t=60, b=80)
    )
    
    st.plotly_chart(fig_finance, use_container_width=True)

with col2:
    st.markdown("### 📊 Volume Penjualan Per Jenis Produk")
    product_volume = filtered_df.groupby('product_type').agg({
        'order_quantity': 'sum',
        'revenue_generated': 'sum'
    }).reset_index().sort_values('order_quantity', ascending=False)
    
    fig_product = go.Figure()
    
    fig_product.add_trace(go.Bar(
        x=product_volume['product_type'],
        y=product_volume['order_quantity'],
        marker=dict(
            color=product_volume['order_quantity'],
            colorscale='Teal',
            showscale=False
        ),
        text=[f'{x:,} unit' for x in product_volume['order_quantity']],
        textposition='outside',
        textfont=dict(size=13, color='white'),
        hovertemplate='<b>%{x}</b><br>Terjual: %{y:,} unit<extra></extra>'
    ))
    
    fig_product.update_layout(
        height=380,
        plot_bgcolor='rgba(42, 82, 152, 0.3)',
        paper_bgcolor='rgba(42, 82, 152, 0.3)',
        font=dict(color='#ffffff', size=13),
        xaxis=dict(showgrid=False, title="Jenis Produk", tickfont=dict(size=12)),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title=dict(text="Unit Terjual", font=dict(size=14))),
        margin=dict(l=60, r=50, t=40, b=80)
    )
    
    st.plotly_chart(fig_product, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# Row 4: Bar Charts
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 💵 Cost Breakdown by Supplier")
    supplier_cost_detail = filtered_df.groupby('supplier_name').agg({
        'costs': 'sum',
        'shipping_costs': 'sum',
        'manufacturing_costs': 'sum'
    }).sort_values('costs', ascending=False).head(8)
    
    fig_supplier_cost = go.Figure()
    
    fig_supplier_cost.add_trace(go.Bar(
        name='Transport Cost',
        y=supplier_cost_detail.index,
        x=supplier_cost_detail['costs'],
        orientation='h',
        marker=dict(color='#64b5f6'),
        text=[f'${x:,.0f}' for x in supplier_cost_detail['costs']],
        textposition='outside',
        hovertemplate='Transport: $%{x:,.2f}<extra></extra>'
    ))
    
    fig_supplier_cost.add_trace(go.Bar(
        name='Shipping Cost',
        y=supplier_cost_detail.index,
        x=supplier_cost_detail['shipping_costs'],
        orientation='h',
        marker=dict(color='#81c784'),
        hovertemplate='Shipping: $%{x:,.2f}<extra></extra>'
    ))
    
    fig_supplier_cost.add_trace(go.Bar(
        name='Manufacturing Cost',
        y=supplier_cost_detail.index,
        x=supplier_cost_detail['manufacturing_costs'],
        orientation='h',
        marker=dict(color='#ffb74d'),
        hovertemplate='Manufacturing: $%{x:,.2f}<extra></extra>'
    ))
    
    fig_supplier_cost.update_layout(
        height=350,
        plot_bgcolor='rgba(42, 82, 152, 0.3)',
        paper_bgcolor='rgba(42, 82, 152, 0.3)',
        font=dict(color='#ffffff', size=11),
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title="Total Cost ($)"),
        yaxis=dict(showgrid=False, title=""),
        barmode='stack',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=100, r=50, t=50, b=50)
    )
    
    st.plotly_chart(fig_supplier_cost, use_container_width=True)

with col2:
    st.markdown("### ⚠️ Defect Rate & Quality Metrics")
    quality_metrics = filtered_df.groupby('supplier_name').agg({
        'defect_rates': 'mean',
        'inspection_results': lambda x: (x == 'Pass').sum() / len(x) * 100
    }).sort_values('defect_rates', ascending=False).head(8)
    quality_metrics.columns = ['avg_defect_rate', 'pass_rate']
    
    fig_quality = go.Figure()
    
    fig_quality.add_trace(go.Bar(
        name='Defect Rate',
        x=quality_metrics['avg_defect_rate'],
        y=quality_metrics.index,
        orientation='h',
        marker=dict(color='#e57373'),
        text=[f'{x:.2f}%' for x in quality_metrics['avg_defect_rate']],
        textposition='outside',
        hovertemplate='Defect Rate: %{x:.2f}%<extra></extra>'
    ))
    
    fig_quality.add_trace(go.Bar(
        name='Pass Rate',
        x=quality_metrics['pass_rate'],
        y=quality_metrics.index,
        orientation='h',
        marker=dict(color='#81c784'),
        text=[f'{x:.1f}%' for x in quality_metrics['pass_rate']],
        textposition='outside',
        hovertemplate='Pass Rate: %{x:.1f}%<extra></extra>',
        visible='legendonly'
    ))
    
    fig_quality.update_layout(
        height=350,
        plot_bgcolor='rgba(42, 82, 152, 0.3)',
        paper_bgcolor='rgba(42, 82, 152, 0.3)',
        font=dict(color='#ffffff', size=11),
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title="Percentage (%)"),
        yaxis=dict(showgrid=False, title=""),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=100, r=50, t=50, b=50)
    )
    
    st.plotly_chart(fig_quality, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ==================== PERFORMANCE SCORE ====================
st.markdown("### 📈 Performance Score")
    
# Calculate performance scores
perf_scores = filtered_df.groupby('supplier_name').apply(lambda x: pd.Series({
    'efficiency': 100 - (x['shipping_times'].mean() / filtered_df['shipping_times'].max() * 100),
    'quality': 100 - (x['defect_rates'].mean() / filtered_df['defect_rates'].max() * 100),
    'cost': 100 - (x['costs'].mean() / filtered_df['costs'].max() * 100),
    'overall': 0
})).reset_index()

perf_scores['overall'] = (perf_scores['efficiency'] + perf_scores['quality'] + perf_scores['cost']) / 3
perf_scores = perf_scores.sort_values('overall', ascending=False).head(5)

for idx, row in perf_scores.iterrows():
    supplier = row['supplier_name']
    score = row['overall']
    
    if score >= 70:
        color = '#81c784'
        icon = '🌟'
    elif score >= 50:
        color = '#ffb74d'
        icon = '⚡'
    else:
        color = '#e57373'
        icon = '⚠️'
    
    st.markdown(f"""
    <div style='background: rgba(42, 82, 152, 0.4); padding: 10px; border-radius: 8px; margin-bottom: 8px;'>
        <p style='color: {color}; font-size: 12px; margin: 0;'>{icon} {supplier}</p>
        <div style='background: rgba(255,255,255,0.1); border-radius: 5px; height: 8px; margin: 5px 0;'>
            <div style='background: {color}; width: {score}%; height: 100%; border-radius: 5px;'></div>
        </div>
        <p style='color: #ffffff; font-size: 14px; font-weight: 600; margin: 0;'>{score:.1f}/100</p>
    </div>
    """, unsafe_allow_html=True)
# ==================== TIME SERIES FORECAST ====================
st.markdown("### 📈 Prediksi Revenue (ARIMA Model)")
st.markdown("<p style='color: #b8d4f1; font-size: 14px;'>Forecast 4 minggu ke depan berdasarkan analisis time series</p>", unsafe_allow_html=True)

# Show only last 12 weeks actual + forecast
forecast_recent = forecast_df.tail(16)

fig_forecast = go.Figure()

# Actual data
actual_data = forecast_recent[forecast_recent['actual'] > 0]
fig_forecast.add_trace(go.Scatter(
    x=actual_data['date'],
    y=actual_data['actual'],
    name='Actual Revenue',
    mode='lines+markers',
    line=dict(color='#64b5f6', width=3),
    marker=dict(size=8),
    hovertemplate='<b>%{x|%Y-%m-%d}</b><br>Actual: $%{y:,.0f}<extra></extra>'
))

# Forecast data
fig_forecast.add_trace(go.Scatter(
    x=forecast_recent['date'],
    y=forecast_recent['forecast'],
    name='Forecast',
    mode='lines+markers',
    line=dict(color='#ffb74d', width=3, dash='dash'),
    marker=dict(size=8, symbol='diamond'),
    hovertemplate='<b>%{x|%Y-%m-%d}</b><br>Forecast: $%{y:,.0f}<extra></extra>'
))

# Confidence interval
fig_forecast.add_trace(go.Scatter(
    x=forecast_recent['date'],
    y=forecast_recent['upper_95'],
    mode='lines',
    line=dict(width=0),
    showlegend=False,
    hoverinfo='skip'
))

fig_forecast.add_trace(go.Scatter(
    x=forecast_recent['date'],
    y=forecast_recent['lower_95'],
    mode='lines',
    line=dict(width=0),
    fillcolor='rgba(255, 183, 77, 0.2)',
    fill='tonexty',
    name='95% Confidence',
    hovertemplate='Confidence Interval<extra></extra>'
))

fig_forecast.update_layout(
    height=380,
    plot_bgcolor='rgba(42, 82, 152, 0.3)',
    paper_bgcolor='rgba(42, 82, 152, 0.3)',
    font=dict(color='#ffffff', size=13),
    xaxis=dict(showgrid=False, title="Tanggal", tickangle=45, tickfont=dict(size=11)),
    yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title=dict(text="Revenue ($)", font=dict(size=14))),
    legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5, font=dict(size=12)),
    margin=dict(l=60, r=50, t=60, b=80)
)

st.plotly_chart(fig_forecast, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ==================== CLUSTER PROFILING ====================
st.markdown("### 🎯 Profil Karakteristik Cluster Supplier")
st.markdown("""
<div style='background: rgba(42, 82, 152, 0.2); padding: 12px; border-radius: 8px; margin-bottom: 15px;'>
    <p style='color: #e8f1ff; font-size: 13px; line-height: 1.5; margin: 0;'>
        Supplier dikelompokkan menggunakan algoritma K-Means clustering berdasarkan tiga metrik kunci yaitu lead time, 
        defect rate, dan total costs. Setiap cluster merepresentasikan karakteristik performa yang berbeda dan memerlukan 
        strategi management yang spesifik. Radar chart menampilkan profil multidimensi setiap cluster untuk perbandingan visual, 
        sementara tabel summary memberikan nilai rata-rata untuk setiap metrik. Cluster dengan performa terbaik ditandai 
        dengan lead time rendah, defect rate minimal, dan profitabilitas tinggi.
    </p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    # Cluster features summary
    cluster_summary = filtered_df.groupby('cluster_label').agg({
        'supplier_name': 'count',
        'lead_times': 'mean',
        'defect_rates': 'mean',
        'costs': 'mean',
        'revenue_generated': 'mean',
        'profit': 'mean'
    }).reset_index()
    
    cluster_summary.columns = ['Cluster', 'Suppliers', 'Avg Lead Time', 'Avg Defect', 'Avg Cost', 'Avg Revenue', 'Avg Profit']
    
    # Create radar chart for cluster comparison
    categories = ['Lead Time', 'Defect Rate', 'Cost', 'Revenue', 'Profit']
    
    fig_radar = go.Figure()
    
    for idx, row in cluster_summary.iterrows():
        # Normalize values (0-100 scale, inversed for negative metrics)
        lead_norm = 100 - (row['Avg Lead Time'] / filtered_df['lead_times'].max() * 100)
        defect_norm = 100 - (row['Avg Defect'] / filtered_df['defect_rates'].max() * 100)
        cost_norm = 100 - (row['Avg Cost'] / filtered_df['costs'].max() * 100)
        revenue_norm = row['Avg Revenue'] / filtered_df['revenue_generated'].max() * 100
        profit_norm = row['Avg Profit'] / filtered_df['profit'].max() * 100
        
        values = [lead_norm, defect_norm, cost_norm, revenue_norm, profit_norm]
        values.append(values[0])  # Close the circle
        
        fig_radar.add_trace(go.Scatterpolar(
            r=values,
            theta=categories + [categories[0]],
            name=row['Cluster'],
            fill='toself',
            line=dict(width=2)
        ))
    
    fig_radar.update_layout(
        height=380,
        polar=dict(
            bgcolor='rgba(42, 82, 152, 0.3)',
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                showgrid=True,
                gridcolor='rgba(255,255,255,0.2)',
                tickfont=dict(size=10, color='#ffffff')
            ),
            angularaxis=dict(
                tickfont=dict(size=12, color='#ffffff')
            )
        ),
        plot_bgcolor='rgba(42, 82, 152, 0.3)',
        paper_bgcolor='rgba(42, 82, 152, 0.3)',
        font=dict(color='#ffffff', size=13),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
        margin=dict(l=60, r=60, t=40, b=80)
    )
    
    st.plotly_chart(fig_radar, use_container_width=True)

with col2:
    st.markdown("#### 📋 Karakteristik Detail")
    
    # Display cluster details
    for idx, row in cluster_summary.iterrows():
        cluster_name = row['Cluster']
        
        # Define cluster color and interpretation
        if 'High' in cluster_name or 'Premium' in cluster_name:
            color = '#81c784'
            icon = '🌟'
        elif 'Medium' in cluster_name or 'Standard' in cluster_name:
            color = '#64b5f6'
            icon = '⚡'
        elif 'Budget' in cluster_name or 'Economy' in cluster_name:
            color = '#ffb74d'
            icon = '💰'
        else:
            color = '#e57373'
            icon = '⚠️'
        
        st.markdown(f"""
        <div style='background: rgba(42, 82, 152, 0.4); padding: 12px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid {color};'>
            <p style='color: {color}; font-size: 15px; font-weight: 600; margin: 0;'>{icon} {cluster_name}</p>
            <p style='color: #ffffff; font-size: 12px; margin: 5px 0 0 0;'>
                📦 {int(row['Suppliers'])} suppliers | 
                ⏱️ Lead: {row['Avg Lead Time']:.1f}d | 
                ❌ Defect: {row['Avg Defect']:.2f}%<br>
                💵 Avg Revenue: ${row['Avg Revenue']:,.0f} | 
                📈 Avg Profit: ${row['Avg Profit']:,.0f}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Regression Insight - Multiple Linear Regression
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 🔍 Multi-Variable Regression Model")
    st.markdown("""
    <div style='background: rgba(42, 82, 152, 0.2); padding: 12px; border-radius: 8px; margin-bottom: 12px;'>
        <p style='color: #e8f1ff; font-size: 12px; line-height: 1.5; margin: 0;'>
            Model regresi linear menganalisis hubungan antara tiga variabel operasional (shipping time, defect rate, lead time) 
            terhadap profit untuk mengidentifikasi faktor yang paling berpengaruh. Koefisien menunjukkan magnitude dampak setiap 
            variabel, sementara nilai korelasi (r) mengindikasikan kekuatan dan arah hubungan. Model ini bersifat asosiatif 
            untuk scenario planning, bukan kausal untuk decision making.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Multiple regression: profit ~ shipping_times + defect_rates + lead_times
    from sklearn.linear_model import LinearRegression
    
    # Prepare features
    X = filtered_df[['shipping_times', 'defect_rates', 'lead_times']].values
    y = filtered_df['profit'].values
    
    reg = LinearRegression()
    reg.fit(X, y)
    
    coef_ship = reg.coef_[0]
    coef_defect = reg.coef_[1]
    coef_lead = reg.coef_[2]
    intercept = reg.intercept_
    r2 = reg.score(X, y)
    
    # Calculate correlations
    corr_ship = filtered_df['shipping_times'].corr(filtered_df['profit'])
    corr_defect = filtered_df['defect_rates'].corr(filtered_df['profit'])
    corr_lead = filtered_df['lead_times'].corr(filtered_df['profit'])
    
    st.markdown(f"""
    <div style='background: rgba(42, 82, 152, 0.4); padding: 15px; border-radius: 8px;'>
        <p style='color: #64b5f6; font-size: 14px; font-weight: 600; margin: 0 0 8px 0;'>📊 Model Prediksi Profit</p>
        <p style='color: #ffffff; font-size: 11px; margin: 0; line-height: 1.6;'>
            <b>Profit = {intercept:.0f}</b><br>
            {'+ ' if coef_ship >= 0 else '- '}{abs(coef_ship):.2f} × Shipping Time (r={corr_ship:.3f})<br>
            {'+ ' if coef_defect >= 0 else '- '}{abs(coef_defect):.2f} × Defect Rate (r={corr_defect:.3f})<br>
            {'+ ' if coef_lead >= 0 else '- '}{abs(coef_lead):.2f} × Lead Time (r={corr_lead:.3f})
        </p>
        <p style='color: #81c784; font-size: 13px; font-weight: 600; margin: 10px 0 5px 0;'>
            📈 Model Accuracy: R² = {r2:.3f}
        </p>
        <p style='color: #b8d4f1; font-size: 11px; margin: 0;'>
            💡 <b>Key Insight:</b> {'Defect rate' if abs(coef_defect) == max(abs(coef_ship), abs(coef_defect), abs(coef_lead)) else 'Lead time' if abs(coef_lead) == max(abs(coef_ship), abs(coef_defect), abs(coef_lead)) else 'Shipping time'} memiliki dampak terbesar terhadap profit
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ==================== DETAILED TABLE ====================
st.markdown("### 📊 Detailed Supplier Performance Table")
st.markdown("""
<div style='background: rgba(42, 82, 152, 0.2); padding: 12px; border-radius: 8px; margin-bottom: 15px;'>
    <p style='color: #e8f1ff; font-size: 13px; line-height: 1.5; margin: 0;'>
        Tabel komprehensif ini menampilkan metrik performa detail untuk setiap supplier termasuk jumlah order, 
        waktu pengiriman rata-rata, biaya, defect rate, lead time, revenue, profit, dan margin keuntungan. 
        Data diurutkan berdasarkan total revenue untuk mengidentifikasi top performers. Pass rate menunjukkan 
        persentase order yang lolos quality inspection, sementara profit margin memberikan insight tentang 
        efisiensi biaya operasional setiap supplier. Tabel ini memudahkan perbandingan langsung antar supplier 
        untuk evaluasi kontrak dan keputusan strategis procurement.
    </p>
</div>
""", unsafe_allow_html=True)

# Prepare comprehensive table data
table_data = filtered_df.groupby('supplier_name').agg({
    'order_date': 'count',
    'shipping_times': 'mean',
    'costs': ['mean', 'sum'],
    'defect_rates': 'mean',
    'lead_times': 'mean',
    'revenue_generated': 'sum',
    'profit': 'sum',
    'inspection_results': lambda x: (x == 'Pass').sum() / len(x) * 100,
    'cluster_label': lambda x: x.mode()[0] if len(x) > 0 else 'N/A'
}).reset_index()

table_data.columns = ['Supplier', 'Orders', 'Avg Ship (d)', 'Avg Cost ($)', 'Total Cost ($)', 
                       'Defect (%)', 'Lead Time (d)', 'Revenue ($)', 'Profit ($)', 'Pass Rate (%)', 'Cluster']

# Calculate profit margin
table_data['Margin (%)'] = (table_data['Profit ($)'] / table_data['Revenue ($)'] * 100).round(1)

# Format numbers
table_data['Orders'] = table_data['Orders'].astype(int)
table_data['Avg Ship (d)'] = table_data['Avg Ship (d)'].round(1)
table_data['Avg Cost ($)'] = table_data['Avg Cost ($)'].round(2)
table_data['Total Cost ($)'] = table_data['Total Cost ($)'].round(0).astype(int)
table_data['Defect (%)'] = table_data['Defect (%)'].round(2)
table_data['Lead Time (d)'] = table_data['Lead Time (d)'].round(1)
table_data['Revenue ($)'] = table_data['Revenue ($)'].round(0).astype(int)
table_data['Profit ($)'] = table_data['Profit ($)'].round(0).astype(int)
table_data['Pass Rate (%)'] = table_data['Pass Rate (%)'].round(1)

# Sort by revenue
table_data = table_data.sort_values('Revenue ($)', ascending=False)

# Display with styling
st.dataframe(
    table_data,
    use_container_width=True,
    height=350,
    hide_index=True,
    column_config={
        "Revenue ($)": st.column_config.NumberColumn(format="$%d"),
        "Profit ($)": st.column_config.NumberColumn(format="$%d"),
        "Total Cost ($)": st.column_config.NumberColumn(format="$%d"),
        "Margin (%)": st.column_config.ProgressColumn(
            min_value=0,
            max_value=100,
            format="%.1f%%"
        ),
        "Pass Rate (%)": st.column_config.ProgressColumn(
            min_value=0,
            max_value=100,
            format="%.1f%%"
        )
    }
)

# ==================== FOOTER ====================
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #b8d4f1; font-size: 12px;'>"
    "Supply Chain Performance Dashboard | Business Intelligence | 2026"
    "</p>",
    unsafe_allow_html=True
)
