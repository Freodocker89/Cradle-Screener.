
import streamlit as st
import ccxt
import pandas as pd
from ta.trend import EMAIndicator

st.set_page_config(page_title="Cradle Screener Diagnostics", layout="wide")
st.title("🧪 Cradle Screener Debug - Bitget Perpetual Contracts")

# Load Bitget markets and check
st.write("📦 Loading Bitget markets...")
exchange = ccxt.bitget()
markets = exchange.load_markets()

# Show diagnostics
st.write(f"🔢 Total markets loaded: {len(markets)}")

if markets:
    preview = list(markets.keys())[:5]
    st.write("🧾 First 5 markets:", preview)

    # Try getting all .P contracts
    symbols = [s for s in markets if s.endswith("USDT.P")]
    st.write(f"✅ Perpetual USDT.P symbols found: {len(symbols)}")
    st.write(symbols[:10])  # show first 10 if any
else:
    st.error("❌ No markets were returned from Bitget — possible CCXT issue or Bitget blocking anonymous API calls.")

# Optional: Scan if symbols exist
timeframe = st.selectbox("Select timeframe:", ["1h", "4h", "1d"])

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

if st.button("🔍 Scan"):
    if not symbols:
        st.warning("⚠️ No symbols to scan.")
    else:
        results = []
        for i, symbol in enumerate(symbols):
            try:
                st.write(f"🔎 Scanning {i+1}/{len(symbols)}: {symbol}")
                ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=50)
                df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
                signal = check_cradle(df)
                results.append((symbol, signal))
            except Exception as e:
                results.append((symbol, f"Error: {str(e)[:40]}"))
                st.write(f"⚠️ Error with {symbol}: {str(e)[:40]}")
        st.success("✅ Scan complete.")
        st.dataframe(pd.DataFrame(results, columns=["Symbol", "Signal"]))
