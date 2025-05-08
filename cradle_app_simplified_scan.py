
import streamlit as st
import ccxt
import pandas as pd
from ta.trend import EMAIndicator

st.set_page_config(page_title="Cradle Screener", layout="wide")
st.title("📊 Cradle Strategy Screener for Bitget Perpetual Contracts")

# Load Bitget markets
exchange = ccxt.bitget()
markets = exchange.load_markets()

# Get all perpetual USDT.P symbols (simplified filter)
symbols = [s for s in markets if s.endswith("USDT.P")]
symbols.sort()

# Timeframe input
timeframe = st.selectbox("Select timeframe:", ["1h", "4h", "1d"])

# Cradle signal logic
def check_cradle(df):
    df["ema10"] = EMAIndicator(df["close"], window=10).ema_indicator()
    df["ema20"] = EMAIndicator(df["close"], window=20).ema_indicator()
    df["cradle_top"] = df[["ema10", "ema20"]].max(axis=1)
    df["cradle_bot"] = df[["ema10", "ema20"]].min(axis=1)

    prev = df.iloc[-2]
    curr = df.iloc[-1]

    long_trend = prev["ema10"] > prev["ema20"]
    pullback = prev["close"] <= prev["cradle_top"] and prev["close"] >= prev["cradle_bot"] and prev["close"] < prev["open"]
    signal = curr["close"] > curr["open"]
    long_signal = long_trend and pullback and signal

    short_trend = prev["ema10"] < prev["ema20"]
    pullback_short = prev["close"] >= prev["cradle_bot"] and prev["close"] <= prev["cradle_top"] and prev["close"] > prev["open"]
    signal_short = curr["close"] < curr["open"]
    short_signal = short_trend and pullback_short and signal_short

    if long_signal:
        return "LONG"
    elif short_signal:
        return "SHORT"
    else:
        return ""

# Run scan
if st.button("🔍 Scan Market"):
    st.write(f"Scanning {len(symbols)} perpetual futures...")

    results = []
    for i, symbol in enumerate(symbols):
        try:
            st.write(f"🔎 {i+1}/{len(symbols)}: {symbol}")
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=50)
            df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
            signal = check_cradle(df)
            results.append((symbol, signal))
        except Exception as e:
            results.append((symbol, f"Error: {str(e)[:50]}"))
            st.write(f"⚠️ Error with {symbol}: {str(e)[:50]}")

    st.success("✅ Scan complete.")
    df_results = pd.DataFrame(results, columns=["Symbol", "Signal"])
    st.dataframe(df_results.reset_index(drop=True), use_container_width=True)
