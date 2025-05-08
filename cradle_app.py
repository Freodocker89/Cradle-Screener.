# cradle_app.py
import streamlit as st
import ccxt
import pandas as pd
import ta

st.set_page_config(page_title="Cradle Screener", layout="wide")

# Title
st.title("📊 Cradle Strategy Screener for Bitget Perpetuals")

# Load exchange
exchange = ccxt.bitget()

# Select timeframe
timeframe = st.selectbox("Select timeframe:", ["1h", "4h", "1d"])

# Symbol list
symbols = [
    "BTC/USDT:USDT", "ETH/USDT:USDT", "BNB/USDT:USDT", "SOL/USDT:USDT", "XRP/USDT:USDT",
    "ADA/USDT:USDT", "DOGE/USDT:USDT", "AVAX/USDT:USDT", "DOT/USDT:USDT", "MATIC/USDT:USDT",
    "SHIB/USDT:USDT", "TRX/USDT:USDT", "LTC/USDT:USDT", "LINK/USDT:USDT", "UNI/USDT:USDT",
    "ATOM/USDT:USDT", "NEAR/USDT:USDT", "ALGO/USDT:USDT", "APE/USDT:USDT", "FTM/USDT:USDT"
]

# Define cradle logic
def check_cradle(df):
    df['ema10'] = ta.trend.ema_indicator(df['close'], window=10).ema_indicator()
    df['ema20'] = ta.trend.ema_indicator(df['close'], window=20).ema_indicator()
    df['cradle_top'] = df[['ema10', 'ema20']].max(axis=1)
    df['cradle_bot'] = df[['ema10', 'ema20']].min(axis=1)

    prev = df.iloc[-2]
    curr = df.iloc[-1]

    long_trend = prev['ema10'] > prev['ema20']
    pullback = prev['close'] <= prev['cradle_top'] and prev['close'] >= prev['cradle_bot'] and prev['close'] < prev['open']
    signal = curr['close'] > curr['open']
    long_signal = long_trend and pullback and signal

    short_trend = prev['ema10'] < prev['ema20']
    pullback_short = prev['close'] >= prev['cradle_bot'] and prev['close'] <= prev['cradle_top'] and prev['close'] > prev['open']
    signal_short = curr['close'] < curr['open']
    short_signal = short_trend and pullback_short and signal_short

    if long_signal:
        return "LONG"
    elif short_signal:
        return "SHORT"
    else:
        return ""

# Button to run scan
if st.button("🔍 Scan Market"):
    results = []
    with st.spinner("Scanning assets..."):
        for symbol in symbols:
            try:
                ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=50)
                df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
                signal = check_cradle(df)
                results.append((symbol.split(":")[0], signal))
            except Exception as e:
                results.append((symbol.split(":")[0], f"Error: {e}"))

    # Display results
    df_results = pd.DataFrame(results, columns=["Symbol", "Signal"])
    st.dataframe(df_results[df_results["Signal"] != ""].reset_index(drop=True), use_container_width=True)
