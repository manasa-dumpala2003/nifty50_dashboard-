import mysql.connector
import pandas as pd
from datetime import datetime, timedelta

def aggregate_daily():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="your_password",
        database="nifty_data"
    )

    df = pd.read_sql("SELECT * FROM nifty50_raw", conn)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['date'] = df['timestamp'].dt.date

    daily_agg = df.groupby(['symbol','date']).agg(
        open_price=('open_price','first'),
        high_price=('high_price','max'),
        low_price=('low_price','min'),
        close_price=('close_price','last'),
        volume=('volume','sum')
    ).reset_index()

    # Moving averages
    daily_agg['MA_5'] = daily_agg.groupby('symbol')['close_price'].transform(lambda x: x.rolling(5).mean())
    daily_agg['MA_10'] = daily_agg.groupby('symbol')['close_price'].transform(lambda x: x.rolling(10).mean())

    # Create daily table if not exists
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS nifty50_daily (
        id BIGINT AUTO_INCREMENT PRIMARY KEY,
        symbol VARCHAR(10),
        date DATE,
        open_price DECIMAL(10,2),
        high_price DECIMAL(10,2),
        low_price DECIMAL(10,2),
        close_price DECIMAL(10,2),
        volume BIGINT,
        MA_5 DECIMAL(10,2),
        MA_10 DECIMAL(10,2)
    )
    """)
    conn.commit()

    for i, row in daily_agg.iterrows():
        cursor.execute("""
        INSERT INTO nifty50_daily (symbol, date, open_price, high_price, low_price, close_price, volume, MA_5, MA_10)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (row['symbol'], row['date'], row['open_price'], row['high_price'], row['low_price'], row['close_price'], row['volume'], row['MA_5'], row['MA_10']))
    conn.commit()

    # Delete raw data older than 30 days
    cutoff = datetime.now() - timedelta(days=30)
    cursor.execute("DELETE FROM nifty50_raw WHERE timestamp < %s", (cutoff,))
    conn.commit()

    cursor.close()
    conn.close()
    print("✅ Daily aggregation completed and old data deleted.")

if __name__ == "__main__":
    aggregate_daily()
