import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

# Connect to SQLite DB
conn = sqlite3.connect("nifty50.db")
cursor = conn.cursor()

# =========================
# Check if tables exist
# =========================
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='nifty50_daily'")
daily_table_exists = cursor.fetchone() is not None

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='nifty50_raw'")
raw_table_exists = cursor.fetchone() is not None

if not daily_table_exists:
    st.warning("⚠️ Table 'nifty50_daily' does not exist. Run daily aggregation first.")
    daily_df = pd.DataFrame()  # empty
else:
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    daily_df = pd.read_sql("SELECT * FROM nifty50_daily WHERE date = ?", conn, params=(yesterday,))
    if daily_df.empty:
        st.warning("⚠️ No aggregated data available for yesterday. Run daily aggregation.")

if not raw_table_exists:
    st.warning("⚠️ Table 'nifty50_raw' does not exist. Run fetch_live_data_sqlite.py first.")
    latest_df = pd.DataFrame()  # empty
else:
    latest_df = pd.read_sql("""
        SELECT * FROM nifty50_raw 
        WHERE timestamp >= datetime('now','-30 minutes')
        ORDER BY timestamp DESC
    """, conn)

conn.close()

# =========================
# Dashboard
# =========================
st.set_page_config(page_title="📈 Nifty 50 Dashboard", layout="wide")
st.title("📊 Nifty 50 Live & Daily Dashboard")

if not daily_df.empty and not latest_df.empty:
    # Select stock
    symbols = daily_df['symbol'].unique().tolist()
    selected_symbol = st.selectbox("Select Stock", symbols)

    # Yesterday's summary
    stock_daily = daily_df[daily_df['symbol'] == selected_symbol].iloc[0]
    st.subheader(f"Yesterday's Summary for {selected_symbol}")
    st.metric("Open", stock_daily['open_price'])
    st.metric("High", stock_daily['high_price'])
    st.metric("Low", stock_daily['low_price'])
    st.metric("Close", stock_daily['close_price'])
    st.metric("Volume", stock_daily['volume'])
    st.metric("5-Day MA", round(stock_daily['MA_5'], 2))
    st.metric("10-Day MA", round(stock_daily['MA_10'], 2))

    # Live chart last 30 mins
    st.subheader(f"Live Price (Last 30 mins) for {selected_symbol}")
    stock_live = latest_df[latest_df['symbol'] == selected_symbol].copy()
    stock_live['timestamp'] = pd.to_datetime(stock_live['timestamp'])
    st.line_chart(stock_live.set_index('timestamp')['close_price'])

    # Top gainers & losers
    st.subheader("🔥 Top Gainers & Losers Yesterday")
    daily_df['pct_change'] = ((daily_df['close_price'] - daily_df['open_price']) / daily_df['open_price']) * 100
    top_gainers = daily_df.sort_values(by='pct_change', ascending=False).head(5)
    top_losers = daily_df.sort_values(by='pct_change').head(5)

    col1, col2 = st.columns(2)
    col1.write("Top Gainers")
    col1.dataframe(top_gainers[['symbol', 'pct_change']])
    col2.write("Top Losers")
    col2.dataframe(top_losers[['symbol', 'pct_change']])
else:
    st.info("📌 Dashboard will appear after fetching live data and performing daily aggregation.")

