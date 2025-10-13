import streamlit as st
import pandas as pd
import mysql.connector
from datetime import datetime, timedelta

# ======================
# MySQL Connection
# ======================
conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Manasa@1232425",
        database="nifty_data"
)

# Load yesterday's aggregated data
yesterday = (datetime.now() - timedelta(days=1)).date()
daily_df = pd.read_sql(f"SELECT * FROM nifty50_daily WHERE date='{yesterday}'", conn)

# Load last 30 mins live data
latest_df = pd.read_sql(f"""
SELECT * FROM nifty50_raw 
WHERE timestamp >= NOW() - INTERVAL 30 MINUTE
ORDER BY timestamp DESC
""", conn)
conn.close()

st.set_page_config(page_title="📈 Nifty 50 Dashboard", layout="wide")
st.title("📊 Nifty 50 Live & Daily Dashboard")

# ======================
# Select Stock
# ======================
symbols = daily_df['symbol'].unique().tolist()
selected_symbol = st.selectbox("Select Stock", symbols)

# ======================
# Yesterday Metrics
# ======================
stock_daily = daily_df[daily_df['symbol']==selected_symbol].iloc[0]
st.subheader(f"Yesterday's Summary for {selected_symbol}")
st.metric("Open", stock_daily['open_price'])
st.metric("High", stock_daily['high_price'])
st.metric("Low", stock_daily['low_price'])
st.metric("Close", stock_daily['close_price'])
st.metric("Volume", stock_daily['volume'])
st.metric("5-Day MA", round(stock_daily['MA_5'],2))
st.metric("10-Day MA", round(stock_daily['MA_10'],2))

# ======================
# Live Data Chart (Last 30 mins)
# ======================
st.subheader(f"Live Price (Last 30 mins) for {selected_symbol}")
stock_live = latest_df[latest_df['symbol']==selected_symbol].copy()
stock_live['timestamp'] = pd.to_datetime(stock_live['timestamp'])
st.line_chart(stock_live.set_index('timestamp')['close_price'])

# ======================
# Top Gainers & Losers (Yesterday)
# ======================
st.subheader("🔥 Top Gainers & Losers Yesterday")
daily_df['pct_change'] = ((daily_df['close_price']-daily_df['open_price'])/daily_df['open_price'])*100
top_gainers = daily_df.sort_values(by='pct_change', ascending=False).head(5)
top_losers = daily_df.sort_values(by='pct_change').head(5)

col1, col2 = st.columns(2)
col1.write("Top Gainers")
col1.dataframe(top_gainers[['symbol','pct_change']])
col2.write("Top Losers")
col2.dataframe(top_losers[['symbol','pct_change']])
