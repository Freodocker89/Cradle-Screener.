
import streamlit as st
import ccxt
import pandas as pd
from ta.trend import EMAIndicator

st.set_page_config(page_title="Cradle Screener", layout="wide")
st.title("📊 Cradle Strategy Screener for Bitget Perpetual Contracts")

# ✅ Connect to Bitget Futures (not Spot)
exchange = ccxt.bitget({
    'options': { 'defaultType': 'swap' }
})
markets = exchange.load_markets()

# Debug output
st.write(f"✅ Total markets loaded: {len(markets)}")

# Filter perpetual futures (USDT.P format)
symbols = [s for s in markets if s.endswith("USDT:USDT")]
symbols.sort()
st.write(f"🔍 Found {len(symbols)} perpetual USDT futures")
st.write(symbols[:10])  # preview first 10

# Timeframe selector
timeframe = st.selectbox("Select timeframe:", ["1h", "4h", "1d"])

# Cradle trade logic
def check_cradle(df):
    df["ema10"] = EMAIndicator(df["close"], window=10).ema_indicator()
    df["ema20"] = EMAIndicator(df["close"], window=20).ema_indicator()
    df["cradle_top"] = df[["ema10", "ema20"]].max(axis=1)
    df["cradle_bot"] = df[["ema10", "ema20"]].min(axis=1)
    prev, curr = df.iloc[-2], df.iloc[-1]
    long_signal = prev["ema10"] > prev["ema20"] and prev["close"] <= prev["cradle_top"] and prev["close"] >= prev["cradle_bot"] and prev["close"] < prev["open"] and curr["close"] > curr["open"]
    short_signal = prev["ema10"] < prev["ema20"] and prev["close"] >= prev["cradle_bot"] and prev["close"] <= prev["cradle_top"] and prev["close"] > prev["open"] and curr["close"] < curr["open"]
    if long_signal: return "LONG"
    elif short_signal: return "SHORT"
    else: return ""

# Main scan button
if st.button("🔍 Scan Market"):
    if not symbols:
        st.warning("⚠️ No futures symbols found.")
    else:
        results = []
        for i, symbol in enumerate(symbols):
            try:
                st.write(f"📈 {i+1}/{len(symbols)}: {symbol}")
                ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=50)
                df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
                signal = check_cradle(df)
                results.append((symbol, signal))
            except Exception as e:
                results.append((symbol, f"Error: {str(e)[:40]}"))
        st.success("✅ Scan complete.")
        st.dataframe(pd.DataFrame(results, columns=["Symbol", "Signal"]))
