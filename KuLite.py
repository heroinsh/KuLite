import requests
import pandas as pd
import os
from datetime import datetime
import dearpygui.dearpygui as dpg

# تنظیمات پایه
BASE_URL = "https://api.kucoin.com/api/v1/market/candles"
LIMIT = 4000
MAX_CANDLES_PER_REQUEST = 1500
SAVE_FOLDER = "data_files"  # پوشه‌ای برای ذخیره فایل‌ها

# اطمینان از وجود پوشه برای ذخیره فایل‌ها
def ensure_save_folder():
    if not os.path.exists(SAVE_FOLDER):
        os.makedirs(SAVE_FOLDER)

# دریافت داده‌ها از API
def fetch_candle_data(symbol, interval, limit):
    end_time = int(datetime.now().timestamp())
    all_data = []

    while limit > 0:
        candles_to_fetch = min(limit, MAX_CANDLES_PER_REQUEST)
        duration = candles_to_fetch * 60 * int(interval[:-3]) if interval.endswith("min") else candles_to_fetch * 3600
        start_time = end_time - duration

        response = requests.get(BASE_URL, params={
            "symbol": symbol,
            "startAt": start_time,
            "endAt": end_time,
            "type": interval
        })

        if response.status_code != 200:
            raise ConnectionError(f"Error retrieving data: {response.json()}")

        data = response.json().get('data', [])
        if not data:
            print("No data found.")
            break

        all_data.extend(data)
        limit -= len(data)
        end_time = start_time

    return all_data

# تبدیل داده‌ها به DataFrame
def prepare_dataframe(data):
    df = pd.DataFrame(data, columns=['Time', 'Open', 'Close', 'High', 'Low', 'Volume', 'Turnover'])
    df['Time'] = pd.to_datetime(pd.to_numeric(df['Time']), unit='s')
    return df[['Time', 'Open', 'Close', 'High', 'Low', 'Volume']]

# ذخیره داده‌ها در فایل Excel و CSV با شماره گذاری
def save_to_files(df, symbol, interval):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file_excel = os.path.join(SAVE_FOLDER, f"data_{symbol}_{interval}_{timestamp}.xlsx")
    output_file_csv = os.path.join(SAVE_FOLDER, f"data_{symbol}_{interval}_{timestamp}.csv")
    
    # ذخیره به Excel
    df.to_excel(output_file_excel, index=False)
    
    # ذخیره به CSV
    df.to_csv(output_file_csv, index=False)

    return os.path.abspath(output_file_excel), os.path.abspath(output_file_csv)

# عملکرد دکمه دانلود
def download_data_callback(sender, app_data, user_data):
    symbol = dpg.get_value("symbol_input").strip().upper()
    interval = dpg.get_value("interval_combo").strip()

    if not symbol or "-" not in symbol or len(symbol.split("-")) != 2:
        dpg.add_text("Invalid trading pair format. Use BASE-QUOTE (e.g., BTC-USDT).", parent="log_window")
        return

    if interval not in ["1min", "5min", "15min", "30min", "1hour", "4hour", "1day", "1week"]:
        dpg.add_text("Invalid interval. Choose a valid option.", parent="log_window")
        return

    try:
        # نمایش پیام در حال انجام کار
        dpg.add_text("Downloading data... Please wait.", parent="log_window")
        
        # دانلود داده‌ها
        data = fetch_candle_data(symbol, interval, LIMIT)
        df = prepare_dataframe(data)
        file_path_excel, file_path_csv = save_to_files(df, symbol, interval)
        
        # نمایش پیام تکمیل دانلود
        dpg.add_text(f"Data has been saved to:\nExcel: {file_path_excel}\nCSV: {file_path_csv}", parent="log_window")
    except Exception as e:
        dpg.add_text(f"An error occurred: {e}", parent="log_window")

# عملکرد دکمه باز کردن لینک
def open_telegram_callback():
    import webbrowser
    webbrowser.open("https://t.me/Heroinin16")

# ایجاد رابط کاربری
def create_gui():
    with dpg.window(label="KuCoin Candle Downloader", width=800, height=600):
        dpg.add_text("Welcome to KuCoin Candle Downloader!")
        dpg.add_spacing(count=2)

        dpg.add_input_text(label="Trading Pair (e.g., BTC-USDT):", tag="symbol_input", default_value="BTC-USDT")
        dpg.add_combo(label="Candle Interval:",
                      items=["1min", "5min", "15min", "30min", "1hour", "4hour", "1day", "1week"],
                      default_value="1hour", tag="interval_combo")

        dpg.add_spacing(count=2)
        dpg.add_button(label="Download Data", callback=download_data_callback)
        dpg.add_spacing(count=2)
        dpg.add_button(label="Made by H0lwin", callback=open_telegram_callback)
        dpg.add_spacing(count=2)

        with dpg.child_window(label="Log", height=200, tag="log_window"):
            dpg.add_text("Logs will appear here.")

if __name__ == "__main__":
    ensure_save_folder()  # اطمینان از وجود پوشه
    dpg.create_context()
    dpg.create_viewport(title="KuCoin Candle Downloader", width=800, height=600)
    create_gui()
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()
