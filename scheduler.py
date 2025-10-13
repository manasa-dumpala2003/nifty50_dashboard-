import schedule
import time
from fetch_live_data_sqlite import fetch_live_data
from daily_aggregation_sqlite import aggregate_daily

# Fetch live data every 2 minutes
schedule.every(2).minutes.do(fetch_live_data)

# Aggregate daily metrics at 18:30 (market close)
schedule.every().day.at("18:30").do(aggregate_daily)

print("📊 Scheduler running...")

while True:
    schedule.run_pending()
    time.sleep(30)

