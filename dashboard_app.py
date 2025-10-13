import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import yfinance as yf
import time

# ---------- SETTINGS ----------
DB_NAME = "nifty50.db"

nifty_50_symbols = [
    "TCS","INFY","RELIANCE","HDFCBANK","HINDUNILVR","ICICIBANK","KOTAKBANK",
    "LT","AXISBANK","ITC","SBIN","BHARTIARTL","HCLTECH","BAJFINANCE","BAJAJFINSV",
    "MARUTI","TECHM","WIPRO","SUNPHARMA","TITAN","ONGC","HINDALCO","ULTRACEMCO",
    "NESTLEIND","POWERGRID","ADANIENT","M&M","HDFC","JSWSTEEL","COALINDIA","GRASIM",
    "EICHERMOT","DRREDDY","BPCL","TATAMOTORS","BRITANNIA","DIVISLAB","SHREECEM",
    "TATAPOWER","UPL","GAIL","CIPLA","ZEEL","BAJAJ-AUTO","ASIANPAINT","ADANIPORTS"
]

# ---------- DATABASE SETUP ----------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS nifty50_raw (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT,
        timestamp DATETIME,
        open_price REAL,
        high_price REAL,
        low_price REAL,
        close_price REAL,
        volume INTEGER
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS nifty50_daily (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT,
        date TEXT,
        open_price REAL,
        high_price REAL,
        low_price REAL,
        close_price REAL,
        volume REAL,
        MA_5 REAL,
        MA_10 REAL
    )
    """)
    conn.commit()
    return conn, cursor

# ---------- FETCH LIVE DATA ----------
def fetch_live_data(cursor, conn):
    for symbol in nifty_50_symbols:
        try:
            stock = yf.Ticker(symbol + ".NS")
            data = stock.history(period="1d", interval="2m")

            # Skip if no data
            if data.empty:
                st.warning(f"No data returned for {symbol}. Skipping.")
                continue

            latest = data.tail(1)
            timestamp = latest.index[0].to_pydatetime()
            open_price = float(latest['Open'].values[0])
            high_price = float(latest['High'].values[0])
            low_price = float(latest['Low'].values[0])
            close_price = float(latest['Close'].values[0])
            volume = int(latest['Volume'].values[0])

            cursor.execute("""
                INSERT INTO nifty50_raw (symbol, timestamp, open_price, high_price, low_price, close_price, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (symbol, timestamp, open_price, high_price, low_price, close_price, volume))
            conn.commit()

        except Exception as e:
            st.warning(f"Error fetching {symbol}: {e}")

# ---------- DAILY AGGREGATION ----------
def aggregate_daily_data(cursor, conn):
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    cursor.execute("SELECT COUNT(*) FROM nifty50_daily WHERE date = ?", (yesterday,))
    if cursor.fetchone()[0] == 0:
        df = pd.read_sql("SELECT * FROM nifty50_raw", conn)
        if df.empty:
            return
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date
        daily_agg = df.groupby(['symbol','date']).agg(
            open_price=('open_price','first'),
            high_price=('high_price','max'),
            low_price=('low_price','min'),
            close_price=('close_price','last'),
            volume=('volume','sum')
        ).reset_index()
        daily_agg['MA_5'] = daily_agg.groupby('symbol')['close_price'].transform(lambda x: x.rolling(5).mean())
        daily_agg['MA_10'] = daily_agg.groupby('symbol')['close_price'].transform(lambda x: x.rolling(10).mean())

        for _, row in daily_agg.iterrows():
            cursor.execute("""
                INSERT INTO nifty50_daily
                (symbol, date, open_price, high_price, low_price, close_price, volume, MA_5, MA_10)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (row['symbol'], row['date'], row['open_price'], row['high_price'], row['low_price'],
                  row['close_price'], row['volume'], row['MA_5'], row['MA_10']))
        conn.commit()

# ---------- CLEANUP OLD RAW DATA ----------
def cleanup_old_raw_data(cursor, conn, days=30):
    cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    cursor.execute("DELETE FROM nifty50_raw WHERE timestamp < ?", (cutoff,))
    conn.commit()

# ---------- STREAMLIT DASHBOARD ----------
st.set_page_config(page_title="📈 Nifty 50 Dashboard", layout="wide")
st.title("📊 Nifty 50 Live & Daily Dashboard (Auto-Refresh)")

# Initialize DB
conn, cursor = init_db()

# Fetch live data, aggregate, cleanup
fetch_live_data(cursor, conn)
aggregate_daily_data(cursor, conn)
cleanup_old_raw_data(cursor, conn, days=30)

# Load data for dashboard
yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
daily_df = pd.read_sql("SELECT * FROM nifty50_daily WHERE date = ?", conn, params=(yesterday,))
latest_df = pd.read_sql("""
SELECT * FROM nifty50_raw 
WHERE timestamp >= datetime('now','-30 minutes')
ORDER BY timestamp ASC
""", conn)
conn.close()

# ---------- DASHBOARD INTERFACE ----------
if not daily_df.empty and not latest_df.empty:
    symbols = daily_df['symbol'].unique().tolist()
    selected_symbol = st.selectbox("Select Stock", symbols)

    # Yesterday summary
    stock_daily = daily_df[daily_df['symbol']==selected_symbol].iloc[0]
    st.subheader(f"Yesterday's Summary for {selected_symbol}")
    st.metric("Open", stock_daily['open_price'])
    st.metric("High", stock_daily['high_price'])
    st.metric("Low", stock_daily['low_price'])
    st.metric("Close", stock_daily['close_price'])
    st.metric("Volume", stock_daily['volume'])
    st.metric("5-Day MA", round(stock_daily['MA_5'],2))
    st.metric("10-Day MA", round(stock_daily['MA_10'],2))

    # Live chart last 30 mins
    st.subheader(f"Live Price (Last 30 mins) for {selected_symbol}")
    chart_placeholder = st.empty()

    latest_df = latest_df[latest_df['symbol']==selected_symbol]
    latest_df['timestamp'] = pd.to_datetime(latest_df['timestamp'])
    if not latest_df.empty:
        chart_placeholder.line_chart(latest_df.set_index('timestamp')['close_price'])

    # Top gainers & losers
    st.subheader("🔥 Top Gainers & Losers Yesterday")
    daily_df['pct_change'] = ((daily_df['close_price'] - daily_df['open_price']) / daily_df['open_price']) * 100
    top_gainers = daily_df.sort_values(by='pct_change', ascending=False).head(5)
    top_losers = daily_df.sort_values(by='pct_change').head(5)

    col1, col2 = st.columns(2)
    col1.write("Top Gainers")
    col1.dataframe(top_gainers[['symbol','pct_change']])
    col2.write("Top Losers")
    col2.dataframe(top_losers[['symbol','pct_change']])

else:
    st.info("Data will appear after fetching live and aggregated daily data.")
