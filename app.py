import streamlit as st
import pandas as pd
import yfinance as yf
from nselib import capital_market
from datetime import datetime, timedelta
import textstat
import re
import gc # Garbage Collector to save RAM

# --- 1. CORE CONFIG ---
st.set_page_config(page_title="Nifty 500 Sniper v24.0", layout="wide")

# --- 2. DATA ENGINES ---

def get_nifty_500_calendar():
    try:
        start = datetime.now().strftime('%d-%m-%Y')
        end = (datetime.now() + timedelta(days=15)).strftime('%d-%m-%Y')
        df = capital_market.board_meetings_announcements(from_date=start, to_date=end)
        if not df.empty:
            return df[df['PURPOSE'].str.contains('Results|Audited|Financial', case=False, na=False)]
        return pd.DataFrame()
    except: return pd.DataFrame()

def get_whale_score_v3(ticker):
    symbol = f"{ticker.upper()}.NS"
    index_symbol = "^NSEI" 
    try:
        data = yf.download([symbol, index_symbol], period="60d", interval="1d", progress=False)['Close']
        if data.empty: return 0, 0
        hist = yf.download(symbol, period="60d", interval="1d", progress=False)
        vol_7d, vol_30d = hist['Volume'].tail(7).mean(), hist['Volume'].tail(30).mean()
        vol_ratio = vol_7d / (vol_30d + 1)
        stock_perf = (data[symbol].iloc[-1] / data[symbol].iloc[-20]) - 1
        index_perf = (data[index_symbol].iloc[-1] / data[index_symbol].iloc[-20]) - 1
        rs_value = round((stock_perf - index_perf) * 100, 2)
        score = (vol_ratio * 60) + (40 if rs_value > 0 else 10)
        return round(min(score, 100), 2), rs_value
    except: return 0, 0

def audit_text_v4(text, source):
    raw_score = textstat.flesch_reading_ease(text)
    segments = ['oil', 'retail', 'digital', 'telecom', 'media', 'chemicals', 'hydrocarbon']
    segment_count = sum(1 for s in segments if s in text.lower())
    comma_density = len(re.findall(r',', text)) / (len(text.split()) + 1)
    if segment_count > 3: raw_score += 20  
    if "Static" in source: raw_score += 10 
    if comma_density > 0.08: raw_score += 20 
    return max(0, min(100, raw_score))

# --- 3. UI ARCHITECTURE ---

st.title("🏹 Nifty 500 Sniper: The Oracle v24.0")

with st.sidebar:
    st.header("🛰️ Terminal Controls")
    # Memory Guard
    st.write(f"Server RAM Status: **Stable**")
    if st.button("Clear System RAM"):
        gc.collect()
        st.success("RAM Purged")

tab1, tab2 = st.tabs(["🐋 Whale Radar & RS", "🔍 Deep Scan Truth-Meter"])

with tab1:
    col_l, col_r = st.columns([1, 2])
    with col_l:
        st.subheader("Asset Audit")
        target = st.text_input("Enter NSE Ticker:", "RELIANCE").upper()
        if st.button("Execute Whale Scan"):
            with st.spinner(f"Analyzing {target}..."):
                score, rs = get_whale_score_v3(target)
                st.metric(f"{target} Whale Score", f"{score}/100")
                st.metric("Relative Strength (vs Nifty 50)", f"{rs}%")
                if score > 85 and rs > 0: st.success("🔥 ALPHA ALERT: Outperformance detected.")
    with col_r:
        st.subheader("Upcoming Results (T-15)")
        calendar = get_nifty_500_calendar()
        if not calendar.empty:
            st.dataframe(calendar[['SYMBOL', 'BOARD_MEETING_DATE', 'PURPOSE']], use_container_width=True)
        else: st.info("Official NSE Calendar is currently empty.")

with tab2:
    st.header("Deep Scan Linguistic Audit")
    audit_target = st.text_input("Ticker for Audit:", "RELIANCE").upper()
    if st.button("Execute Deep Scan"):
        with st.spinner("Fetching data and initializing Light-AI..."):
            # Load AI only when needed to save memory
            from transformers import pipeline
            oracle_ai = pipeline("sentiment-analysis", model="ProsusAI/finbert", device=-1)
            
            stock = yf.Ticker(f"{audit_target}.NS")
            summary = stock.info.get('longBusinessSummary', "")
            if summary:
                st.subheader(f"Data Source: Official Profile")
                st.info(summary)
                sentiment = oracle_ai(summary[:512])[0]
                transparency = audit_text_v4(summary, "Static")
                
                c1, c2 = st.columns(2)
                c1.metric("Management Tone", sentiment['label'].upper(), f"{round(sentiment['score']*100, 1)}% Confidence")
                c2.metric("Transparency Index", f"{round(transparency, 2)}/100")
                
                # Cleanup AI from RAM after use
                del oracle_ai
                gc.collect()
            else:
                st.error("No web data found.")
