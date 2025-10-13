import yfinance as yf
import mysql.connector
from datetime import datetime

# List of Nifty 50 symbols (update if necessary)
nifty_50_symbols = [
    "TCS","INFY","RELIANCE","HDFCBANK","HINDUNILVR","ICICIBANK","KOTAKBANK",
    "LT","AXISBANK","ITC","SBIN","BHARTIARTL","HCLTECH","BAJFINANCE","BAJAJFINSV",
    "MARUTI","TECHM","WIPRO","SUNPHARMA","TITAN","ONGC","HINDALCO","ULTRACEMCO",
    "NESTLEIND","POWERGRID","ADANIENT","M&M","HDFC","JSWSTEEL","COALINDIA","GRASIM",
    "EICHERMOT","DRREDDY","BPCL","TATAMOTORS","BRITANNIA","DIVISLAB","SHREECEM",
    "TATAPOWER","UPL","GAIL","CIPLA","HINDUNILVR","ZEEL","BAJAJ-AUTO","ASIANPAINT",
    "ADANIPORTS","TECHM"
]

def fetch_live_data():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="your_password",
        database="nifty_data"
    )
    cursor = conn.cursor()

    for symbol in nifty_50_symbols:
        try:
            stock = yf.Ticker(symbol + ".NS")
            data = stock.history(period="1d", interval="2m")
            latest = data.tail(1)

            timestamp = latest.index[0].to_pydatetime()
            open_price = float(latest['Open'].values[0])
            high_price = float(latest['High'].values[0])
            low_price = float(latest['Low'].values[0])
            close_price = float(latest['Close'].values[0])
            volume = int(latest['Volume'].values[0])

            sql = """
            INSERT INTO nifty50_raw (symbol, timestamp, open_price, high_price, low_price, close_price, volume)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            """
            cursor.execute(sql, (symbol, timestamp, open_price, high_price, low_price, close_price, volume))
            conn.commit()
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")

    cursor.close()
    conn.close()
    print("✅ Live data fetched successfully.")

if __name__ == "__main__":
    fetch_live_data()
