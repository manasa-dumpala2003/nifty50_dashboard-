import streamlit as st
import pandas as pd
import mysql.connector
import plotly.express as px

# ---------- MySQL Connection ----------
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Manasa@1232425",
        database="nifty_db"
    )

# ---------- Fetch Data ----------
def fetch_latest_nifty_overall():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM nifty_overall ORDER BY timestamp DESC LIMIT 1", conn)
    conn.close()
    return df

def fetch_nifty_overall_trend():
    conn = get_connection()
    df = pd.read_sql("""
        SELECT timestamp, lastPrice
        FROM nifty_overall
        ORDER BY timestamp ASC
    """, conn)
    conn.close()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

def fetch_symbols():
    conn = get_connection()
    df = pd.read_sql("SELECT DISTINCT symbol FROM raw_nifty_data", conn)
    conn.close()
    return df['symbol'].tolist()

def fetch_symbol_trend(symbol):
    conn = get_connection()
    df = pd.read_sql(f"""
        SELECT symbol, lastPrice, timestamp
        FROM raw_nifty_data
        WHERE symbol='{symbol}'
        ORDER BY timestamp ASC
        LIMIT 1000
    """, conn)
    conn.close()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

def fetch_last_50_rows():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM raw_nifty_data ORDER BY timestamp DESC LIMIT 50", conn)
    conn.close()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

# ---------- Streamlit UI ----------
st.set_page_config(page_title="NIFTY50 Dashboard", layout="wide")
st.title("📊 NIFTY 50 Live Dashboard")

# --- KPI Section ---
st.subheader("📌 NIFTY 50 KPIs")
latest = fetch_latest_nifty_overall()
if not latest.empty:
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Last Price", f"{latest['lastPrice'].values[0]:,.2f}")
    kpi2.metric("Price Change", f"{latest['priceChange'].values[0]:,.2f}")
    kpi3.metric("Previous Close", f"{latest['previousClose'].values[0]:,.2f}")

# --- Overall NIFTY Trend (from nifty_overall) ---
st.subheader("📈 NIFTY 50 Overall Trend")
overall_trend = fetch_nifty_overall_trend()

# Area chart with time (X-axis) and lastPrice (Y-axis)
fig_overall = px.area(
    overall_trend,
    x="timestamp",
    y="lastPrice",
    template="plotly_white",
    color_discrete_sequence=["#0072B2"]
)
fig_overall.update_traces(fill="tozeroy", mode="lines+markers")

# Y-axis zoomed to visible range only
y_min = max(10000, overall_trend['lastPrice'].min() * 0.98)
y_max = overall_trend['lastPrice'].max() * 1.02
fig_overall.update_layout(
    xaxis_title="Timestamp (Time)",
    yaxis_title="Last Price",
    yaxis=dict(range=[y_min, y_max]),
    showlegend=False
)

st.plotly_chart(fig_overall, use_container_width=True)

# --- Sidebar: Symbol Selection ---
st.sidebar.header("Stock Symbol Trend")
symbols = fetch_symbols()
selected_symbol = st.sidebar.selectbox("Select Symbol", symbols)

symbol_trend = fetch_symbol_trend(selected_symbol)
st.subheader(f"📈 {selected_symbol} Price Trend (Intraday)")
fig_symbol = px.area(
    symbol_trend,
    x="timestamp",
    y="lastPrice",
    title=f"{selected_symbol} Stock Price Movement",
    template="plotly_white",
    color_discrete_sequence=["#009E73"]
)
fig_symbol.update_traces(fill="tozeroy", mode="lines+markers")

# Auto-scale y-axis for symbol trend
y_min_symbol = symbol_trend['lastPrice'].min() * 0.98
y_max_symbol = symbol_trend['lastPrice'].max() * 1.02
fig_symbol.update_layout(
    xaxis_title="Time",
    yaxis_title="Last Price",
    yaxis=dict(range=[y_min_symbol, y_max_symbol]),
    showlegend=False
)
st.plotly_chart(fig_symbol, use_container_width=True)

# --- Last 50 Rows Table ---
st.subheader("📝NIFTY50 Data")
last_50 = fetch_last_50_rows()
st.dataframe(last_50[['symbol', 'open', 'dayHigh', 'dayLow', 'lastPrice', 'previousClose', 'priceChange', 'pChange', 'timestamp']], use_container_width=True)  