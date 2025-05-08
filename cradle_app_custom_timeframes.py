
import streamlit as st
import ccxt
import pandas as pd
from ta.trend import EMAIndicator

st.set_page_config(page_title="Cradle Screener", layout="wide")
st.title("📊 Cradle Strategy Screener for Bitget Perpetual Contracts")

# ✅ Connect to Bitget Futures
exchange = ccxt.bitget({
    'options': { 'defaultType': 'swap' }
})
markets = exchange.load_markets()

# Filter USDT perpetual futures
symbols = [s for s in markets if s.endswith("USDT:USDT")]
symbols.sort()

# Timeframe options including custom intervals
timeframe = st.selectbox("Select timeframe:", [
    "1m", "3m", "5m", "10m", "15m", "20m", "30m",
    "1h", "2h", "4h", "6h", "8h", "10h", "12h", "16h",
    "1d", "3d", "1w"
])

# Cradle check logic
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

# Main scanner
if st.button("🔍 Scan Market"):
    if not symbols:
        st.warning("⚠️ No symbols found.")
    else:
        trade_setups = []
        for i, symbol in enumerate(symbols):
            try:
                st.text(f"Scanning {i+1}/{len(symbols)}: {symbol}")
                ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=50)
                df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
                signal = check_cradle(df)
                if signal:
                    trade_setups.append((symbol, signal))
            except Exception:
                pass

        if trade_setups:
            st.success(f"✅ {len(trade_setups)} trade opportunities found.")
            st.dataframe(pd.DataFrame(trade_setups, columns=["Symbol", "Signal"]))
        else:
            st.info("No trade signals found at this time.")
