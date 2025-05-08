
import streamlit as st
import ccxt
import pandas as pd
import ta

st.set_page_config(layout="wide")
st.markdown("## 📊 Cradle Strategy Screener for Bitget Perpetual Contracts")

# === Load Bitget markets ===
with st.spinner("🔄 Loading Bitget symbols..."):
    exchange = ccxt.bitget()
    markets = exchange.load_markets()
    symbols = [s for s in markets if s.endswith("USDT:USDT") and "/USDT:USDT" in s and markets[s]["type"] == "swap"]
    symbols.sort()

col1, col2 = st.columns([2, 1])
with col1:
    st.markdown(f"🔍 Scanning {len(symbols)} perpetual futures...")

# === Timeframe selection ===
with col2:
    timeframe = st.selectbox("Select timeframe:", [
        "10m", "15m", "20m", "30m", "1h", "2h", "4h", "6h", "8h", "10h", "12h", "16h", "1d"
    ])

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

if st.button("🔍 Scan Market"):
    results = []
    for i, symbol in enumerate(symbols):
        st.write(f"Scanning {i+1}/{len(symbols)}: {symbol}")
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=50)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            signal = check_cradle(df)
            if signal:
                results.append({"Symbol": symbol, "Signal": signal})
        except Exception as e:
            st.error(f"Error scanning {symbol}: {e}")

    st.success(f"✅ {len(results)} trade opportunities found.")
    if results:
        st.dataframe(pd.DataFrame(results))
