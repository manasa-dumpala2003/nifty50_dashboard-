import requests
import pandas as pd
import mysql.connector
from datetime import datetime, time as dtime
import pytz
import schedule
import time
import logging
import os

# ---------- Logging Setup ----------
log_path = os.path.join(os.path.dirname(__file__), "nifty.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s]: %(message)s",
    handlers=[logging.FileHandler(log_path), logging.StreamHandler()]
)

# ---------- MySQL Connection ----------
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Manasa@1232425",
        database="nifty_db"
    )

# ---------- Fetch Live NIFTY50 Data ----------
def fetch_nifty_data():
    url = "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%2050"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data["data"])
        df["timestamp"] = datetime.now(pytz.timezone("Asia/Kolkata"))
        logging.info("Fetched live NIFTY50 data successfully.")
        return df
    except Exception as e:
        logging.error(f"Failed fetching NIFTY50: {e}")
        return None

# ---------- Store Raw Data and Overall ----------
def store_raw_data(df):
    if df is None or df.empty:
        logging.warning("No data to store.")
        return

    conn = get_connection()
    cursor = conn.cursor()

    # Create raw table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS raw_nifty_data (
            id INT AUTO_INCREMENT PRIMARY KEY,
            symbol VARCHAR(50),
            companyName VARCHAR(100),
            open FLOAT,
            dayHigh FLOAT,
            dayLow FLOAT,
            lastPrice FLOAT,
            previousClose FLOAT,
            priceChange FLOAT,
            pChange FLOAT,
            timestamp DATETIME
        )
    """)

    # Create overall table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS nifty_overall (
            id INT AUTO_INCREMENT PRIMARY KEY,
            indexName VARCHAR(50),
            lastPrice FLOAT,
            previousClose FLOAT,
            priceChange FLOAT,
            pChange FLOAT,
            dayHigh FLOAT,
            dayLow FLOAT,
            timestamp DATETIME
        )
    """)

    # Overall index (first row)
    overall = df.iloc[0]
    overall_timestamp = overall["timestamp"].strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("""
        INSERT INTO nifty_overall
        (indexName, lastPrice, previousClose, priceChange, pChange, dayHigh, dayLow, timestamp)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        overall["symbol"],
        float(overall["lastPrice"]),
        float(overall["previousClose"]),
        float(overall["change"]),
        float(overall["pChange"]),
        float(overall["dayHigh"]),
        float(overall["dayLow"]),
        overall_timestamp
    ))

    # Individual stocks (skip first row)
    for _, row in df.iloc[1:].iterrows():
        timestamp_str = row["timestamp"].strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            INSERT INTO raw_nifty_data
            (symbol, companyName, open, dayHigh, dayLow, lastPrice, previousClose, priceChange, pChange, timestamp)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            row["symbol"],
            row.get("companyName", row["symbol"]),
            float(row["open"]),
            float(row["dayHigh"]),
            float(row["dayLow"]),
            float(row["lastPrice"]),
            float(row["previousClose"]),
            float(row["change"]),
            float(row["pChange"]),
            timestamp_str
        ))

    conn.commit()
    conn.close()
    logging.info(f"Stored raw data ({len(df)-1} rows) and overall index successfully.")

# ---------- Store Closing Data ----------
def store_closing_data():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS closing_nifty_data (
            id INT AUTO_INCREMENT PRIMARY KEY,
            symbol VARCHAR(50),
            companyName VARCHAR(100),
            closingPrice FLOAT,
            previousClose FLOAT,
            priceChange FLOAT,
            pChange FLOAT,
            dayHigh FLOAT,
            dayLow FLOAT,
            volume BIGINT,
            date DATE,
            timestamp DATETIME
        )
    """)

    df = pd.read_sql("SELECT * FROM raw_nifty_data", conn)
    if df.empty:
        logging.info("No raw data to process for closing.")
        conn.close()
        return

    latest_df = df.sort_values("timestamp").groupby("symbol").tail(1)
    for _, row in latest_df.iterrows():
        timestamp_str = row["timestamp"].strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            INSERT INTO closing_nifty_data
            (symbol, companyName, closingPrice, previousClose, priceChange, pChange, dayHigh, dayLow, volume, date, timestamp)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            row["symbol"],
            row["companyName"],
            float(row["lastPrice"]),
            float(row["previousClose"]),
            float(row["priceChange"]),
            float(row["pChange"]),
            float(row["dayHigh"]),
            float(row["dayLow"]),
            int(row.get("totalTradedVolume", 0)),
            row["timestamp"].date(),
            timestamp_str
        ))

    conn.commit()
    conn.close()
    logging.info(f"Stored closing data for {datetime.now(pytz.timezone('Asia/Kolkata')).date()}")

# ---------- Monthly Cleanup ----------
def cleanup_raw_data():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM raw_nifty_data
        WHERE timestamp < (NOW() - INTERVAL 30 DAY)
    """)
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    logging.info(f"Deleted {deleted} old rows from raw_nifty_data (monthly cleanup).")

# ---------- Market Open Check ----------
MARKET_START = dtime(9, 15)
MARKET_END = dtime(15, 30)
def is_market_open():
    now = datetime.now(pytz.timezone("Asia/Kolkata")).time()
    return MARKET_START <= now <= MARKET_END

# ---------- Scheduled Jobs ----------
def job_live_fetch():
    if is_market_open():
        df = fetch_nifty_data()
        if df is not None:
            store_raw_data(df)
    else:
        logging.info("Market closed — skipping live fetch.")

def monthly_cleanup_job():
    today = datetime.now(pytz.timezone("Asia/Kolkata")).day
    if today == 1:
        cleanup_raw_data()

schedule.every(10).minutes.do(job_live_fetch)
schedule.every().day.at("15:30").do(store_closing_data)
schedule.every().day.at("00:10").do(monthly_cleanup_job)

# ---------- Run immediately ----------
job_live_fetch()
logging.info("🚀 Automation started — live data, closing data, and monthly cleanup.")

# ---------- Continuous loop ----------
while True:
    schedule.run_pending()
    time.sleep(30)

