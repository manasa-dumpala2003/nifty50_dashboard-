# 📈 Automated NIFTY50 Stock Data Pipeline

## 🧠 Overview
This project automates the process of fetching **live NIFTY50 stock market data** from the NSE India API, processing it with **Pandas**, and storing it in a **MySQL database** for analysis and historical tracking.

It uses Python **scheduling** and **logging** to continuously collect, clean, and store stock data at fixed intervals — making it a real-world example of a **data pipeline for financial analytics**.

---

## 🚀 Features

✅ **Live Data Fetching** – Automatically fetches the latest NIFTY50 data from the NSE API every 10 minutes.  
✅ **Data Storage** – Saves data into MySQL tables (`raw_nifty_data`, `nifty_overall`, and `closing_nifty_data`).  
✅ **Closing Data Automation** – Stores daily closing prices at 3:30 PM (market close).  
✅ **Monthly Cleanup** – Automatically deletes raw data older than 30 days.  
✅ **Error Handling & Logging** – Logs all operations and errors for easy debugging.  
✅ **Time-Zone Aware** – Works with Indian Standard Time (`Asia/Kolkata`).  

---

## 🏗️ Project Architecture

    
    ┌──────────────────────────────────┐
    │       NSE API (Live Data)        │
    └──────────────────────────────────┘
                   │
                   ▼
    ┌──────────────────────────────────┐
    │   Data Fetch (requests + JSON)   │
    └──────────────────────────────────┘
                   │
                   ▼
    ┌──────────────────────────────────┐
    │  Data Processing (Pandas + TZ)   │
    └──────────────────────────────────┘
                   │
                   ▼
    ┌──────────────────────────────────┐
    │ MySQL Database (nifty_db)        │
    │ ├─ raw_nifty_data                │
    │ ├─ nifty_overall                 │
    │ └─ closing_nifty_data            │
    └──────────────────────────────────┘
                   │
                   ▼
    ┌──────────────────────────────────┐
    │  Scheduler + Logging Automation   │
    └──────────────────────────────────┘

---

## ⚙️ Technologies Used

| Category | Tools & Libraries |
|-----------|------------------|
| **Programming** | Python 3 |
| **Data Handling** | Pandas |
| **API Communication** | Requests |
| **Database** | MySQL |
| **Automation** | Schedule |
| **Logging** | Logging Module |
| **Timezone Handling** | pytz |

---

## 🧩 Database Tables

### 1️⃣ `raw_nifty_data`
Stores real-time data for each NIFTY50 stock fetched every 10 minutes.  
**Columns:** symbol, companyName, open, dayHigh, dayLow, lastPrice, previousClose, priceChange, pChange, timestamp

### 2️⃣ `nifty_overall`
Stores the overall index data (NIFTY50 summary).  
**Columns:** indexName, lastPrice, previousClose, priceChange, pChange, dayHigh, dayLow, timestamp

### 3️⃣ `closing_nifty_data`
Stores the final prices for each stock at the end of each trading day.  
**Columns:** symbol, companyName, closingPrice, previousClose, priceChange, pChange, dayHigh, dayLow, volume, date, timestamp

---

## 🕒 Automation Schedule

| Task | Frequency | Function |
|------|------------|----------|
| **Fetch Live Data** | Every 10 minutes (9:15 AM – 3:30 PM) | `job_live_fetch()` |
| **Store Closing Data** | Daily at 3:30 PM | `store_closing_data()` |
| **Monthly Cleanup** | 1st of every month at 12:10 AM | `cleanup_raw_data()` |

---

## 🧰 Logging

The script uses Python’s built-in **logging** module to track:

- ✅ Successful data fetches  
- ✅ Database insertions  
- ⚠️ API or connection errors  
- 🧹 Cleanup operations  

All logs are saved in **`nifty.log`** for easy monitoring and debugging.

---

## 🧠 Key Learning Outcomes

🔹 Working with real-world APIs and JSON data  
🔹 Handling data automation with Python schedulers  
🔹 Using MySQL as a data warehouse for time-series data  
🔹 Managing data integrity and cleanup in pipelines  
🔹 Implementing logging and error handling in production-style scripts  
🔹 Understanding market timing and timezone handling  

