import streamlit as st
import pandas as pd
import yfinance as yf
from nselib import capital_market
from datetime import datetime, timedelta
import textstat
import gc

# --- 1. CONFIG & SYSTEM RECOVERY ---
st.set_page_config(page_title="Nifty 500 Sniper v27.0", layout="wide")

def clear_memory():
    gc.collect()

# --- 2. ENGINES: CALENDAR, WHALE RADAR & HISTORY ---

@st.cache_data(ttl=3600)
def get_monthly_calendar():
    try:
        start = datetime.now().strftime('%d-%m-%Y')
        end = (datetime.now() + timedelta(days=30)).strftime('%d-%m-%Y')
        df = capital_market.board_meetings_announcements(from_date=start, to_date=end)
        if not df.empty:
            res = df[df['PURPOSE'].str.contains('Results|Audited|Financial', case=False, na=False)]
            res['BOARD_MEETING_DATE'] = pd.to_datetime(res['BOARD_MEETING_DATE'], dayfirst=True)
            return res.sort_values(by='BOARD_MEETING_DATE')
        return pd.DataFrame()
    except: return pd.DataFrame()

def get_earnings_history(ticker):
    """Fetches the last 4 actual earnings dates from Yahoo Finance."""
    try:
        stock = yf.Ticker(f"{ticker.upper()}.NS")
        # earnings_dates returns a DF with the historical schedule
        hist = stock.earnings_dates
        if hist is not None and not hist.empty:
            # Clean up for display
            display_hist = hist.head(4).reset_index()
            display_hist.columns = ['Historical Date', 'EPS Estimate', 'Reported EPS', 'Surprise']
            return display_hist
        return pd.DataFrame()
    except: return pd.DataFrame()

def get_whale_score_v4(ticker):
    symbol = f"{ticker.upper()}.NS"
    try:
        data = yf.download([symbol, "^NSEI"], period="60d", interval="1d", progress=False)['Close']
        hist = yf.download(symbol, period="60d", interval="1d", progress=False)
        if data.empty or hist.empty: return 0, 0
        v_ratio = hist['Volume'].tail(7).mean() / (hist['Volume'].tail(30).mean() + 1)
        rs = round(((data[symbol].iloc[-1]/data[symbol].iloc[-20]) - (data["^NSEI"].iloc[-1]/data["^NSEI"].iloc[-20])) * 100, 2)
        score = (v_ratio * 60) + (40 if rs > 0 else 10)
        return round(min(score, 100), 2), rs
    except: return 0, 0

# --- 3. UI ARCHITECTURE ---

st.title("🏹 Nifty 500 Sniper: The Oracle v27.0")

with st.sidebar:
    st.header("🛰️ Sniper Terminal")
    if st.button("Force Global Refresh"):
        st.cache_data.clear()
        st.rerun()
    st.info("System: Predictive Analytics Active")

tab1, tab2 = st.tabs(["🐋 Whale Radar & Prediction", "🔍 Deep Scan Truth-Meter"])

with tab1:
    l, r = st.columns([1, 2])
    with l:
        st.subheader("Asset Audit")
        target = st.text_input("Ticker:", "RELIANCE").upper()
        if st.button("Execute Scan"):
            score, rs = get_whale_score_v4(target)
            st.metric(f"Whale Score", f"{score}/100")
            st.metric("Relative Strength", f"{rs}%")
            
            # Show History for Prediction
            st.markdown("---")
            st.subheader("📅 Earnings History")
            hist_df = get_earnings_history(target)
            if not hist_df.empty:
                st.write("Past 4 Quarters:")
                st.table(hist_df[['Historical Date', 'Reported EPS']])
                st.caption("Use these dates to estimate the upcoming Q4 window.")
            else:
                st.warning("No historical earnings data found.")

    with r:
        st.subheader("📅 30-Day Official Calendar")
        cal = get_monthly_calendar()
        if not cal.empty:
            st.dataframe(cal[['SYMBOL', 'BOARD_MEETING_DATE', 'PURPOSE']], use_container_width=True)
        else:
            st.info("No official board meetings scheduled yet.")
            st.write("**Strategy:** Look at the 'Earnings History' on the left to predict the April 2026 window.")

with tab2:
    st.header("Linguistic Deep Scan")
    audit_target = st.text_input("Ticker for Audit:", "TCS").upper()
    if st.button("Run Truth-Meter"):
        with st.spinner("Initializing AI Engine..."):
            from transformers import pipeline
            oracle = pipeline("sentiment-analysis", model="ProsusAI/finbert", device=-1)
            summary = yf.Ticker(f"{audit_target}.NS").info.get('longBusinessSummary', "")
            if summary:
                st.info(summary[:600] + "...")
                sent = oracle(summary[:512])[0]
                st.write(f"Tone: **{sent['label'].upper()}** | Confidence: **{round(sent['score']*100, 1)}%**")
                st.write(f"Transparency: **{textstat.flesch_reading_ease(summary)}/100**")
                del oracle 
                clear_memory()
            else: st.error("No data found.")
