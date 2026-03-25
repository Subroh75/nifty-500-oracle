import streamlit as st
import pandas as pd
import yfinance as yf
from nselib import capital_market
from datetime import datetime, timedelta
import textstat
import gc

# --- 1. CONFIG & SYSTEM RECOVERY ---
st.set_page_config(page_title="Nifty 500 Sniper v30.0", layout="wide")

def clear_memory():
    gc.collect()

# --- 2. ENGINES: SECTOR HEATMAP, CALENDAR & RADAR ---

@st.cache_data(ttl=3600)
def get_sector_heatmap():
    sectors = {
        "Nifty Bank": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS"],
        "Nifty IT": ["TCS.NS", "INFY.NS", "HCLTECH.NS", "WIPRO.NS", "LTIM.NS"],
        "Nifty Energy": ["RELIANCE.NS", "ONGC.NS", "NTPC.NS", "POWERGRID.NS", "BPCL.NS"],
        "Nifty Auto": ["TATAMOTORS.NS", "M&M.NS", "MARUTI.NS", "BAJAJ-AUTO.NS", "EICHERMOT.NS"]
    }
    heatmap = {}
    for name, tickers in sectors.items():
        scores = []
        for t in tickers:
            try:
                h = yf.download(t, period="30d", interval="1d", progress=False)
                if not h.empty:
                    curr_vol = float(h['Volume'].tail(5).mean().iloc[0] if isinstance(h['Volume'].tail(5).mean(), pd.Series) else h['Volume'].tail(5).mean())
                    base_vol = float(h['Volume'].tail(20).mean().iloc[0] if isinstance(h['Volume'].tail(20).mean(), pd.Series) else h['Volume'].tail(20).mean())
                    scores.append((curr_vol / (base_vol + 1)) * 100)
            except: continue
        heatmap[name] = float(sum(scores)/len(scores)) if scores else 0.0
    return heatmap

@st.cache_data(ttl=3600)
def get_monthly_calendar():
    try:
        start, end = datetime.now().strftime('%d-%m-%Y'), (datetime.now() + timedelta(days=30)).strftime('%d-%m-%Y')
        df = capital_market.board_meetings_announcements(from_date=start, to_date=end)
        if not df.empty:
            res = df[df['PURPOSE'].str.contains('Results|Audited|Financial', case=False, na=False)].copy()
            res['BOARD_MEETING_DATE'] = pd.to_datetime(res['BOARD_MEETING_DATE'], dayfirst=True)
            return res.sort_values(by='BOARD_MEETING_DATE')
        return pd.DataFrame()
    except: return pd.DataFrame()

# --- 3. UI ARCHITECTURE ---

st.title("🏹 Nifty 500 Sniper: The Oracle v30.0")

with st.sidebar:
    st.header("🛰️ Sector Heatmap")
    heat_data = get_sector_heatmap()
    for sector, val in heat_data.items():
        st.write(f"**{sector}:** {round(val, 1)}")
        st.progress(max(0.0, min(float(val/150), 1.0)))
    st.markdown("---")
    if st.button("Force Global Refresh"):
        st.cache_data.clear()
        st.rerun()

tab1, tab2 = st.tabs(["🐋 Whale Radar & RS", "🔍 Deep Scan Truth-Meter"])

with tab1:
    l, r = st.columns([1, 2])
    with l:
        st.subheader("Asset Audit")
        target = st.text_input("Ticker:", "RELIANCE").upper()
        if st.button("Execute Scan"):
            # Whale Logic (Same as v29)
            score = 75 # Placeholder for brevity, keep your full get_whale_score_v5 logic here
            st.metric(f"Whale Score", f"{score}/100")
            
            st.subheader("📅 Earnings History")
            try:
                hist = yf.Ticker(f"{target}.NS").earnings_dates
                if hist is not None: st.table(hist.head(4).reset_index())
            except: st.warning("No historical data found.")

    with r:
        st.subheader("📅 30-Day Official Calendar")
        cal = get_monthly_calendar()
        if not cal.empty:
            st.dataframe(cal[['SYMBOL', 'BOARD_MEETING_DATE', 'PURPOSE']], use_container_width=True)
        else:
            st.warning("No official dates filed with NSE yet.")
            st.info("💡 **Strategy Mode:** Official announcements for April Q4 usually begin appearing after April 5th. In the meantime, audit the 'Early Birds' below:")
            st.table(pd.DataFrame({
                "Likely Ticker": ["TCS", "INFY", "HDFCBANK", "ICICIBANK", "WIPRO"],
                "Expected Window": ["April 10-15", "April 15-18", "April 18-20", "April 20-25", "April 22-25"]
            }))

with tab2:
    # (Deep Scan logic remains as in v29)
    st.header("Linguistic Deep Scan")
    audit_target = st.text_input("Ticker for Audit:", "TCS").upper()
    if st.button("Run Truth-Meter"):
        with st.spinner("Analyzing..."):
            from transformers import pipeline
            oracle = pipeline("sentiment-analysis", model="ProsusAI/finbert", device=-1)
            summary = yf.Ticker(f"{audit_target}.NS").info.get('longBusinessSummary', "")
            if summary:
                st.info(summary[:400] + "...")
                sent = oracle(summary[:512])[0]
                st.write(f"Tone: **{sent['label'].upper()}** | Clarity: **{textstat.flesch_reading_ease(summary)}/100**")
                del oracle
                clear_memory()
