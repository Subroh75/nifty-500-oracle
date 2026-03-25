import streamlit as st
import pandas as pd
import yfinance as yf
from nselib import capital_market
from datetime import datetime, timedelta
import textstat
import gc

# --- 1. CONFIG & SYSTEM RECOVERY ---
st.set_page_config(page_title="Nifty 500 Sniper v29.0", layout="wide")

def clear_memory():
    gc.collect()

# --- 2. ENGINES: SECTOR HEATMAP, CALENDAR & RADAR ---

@st.cache_data(ttl=3600)
def get_sector_heatmap():
    """Calculates avg Whale Score for major sectors. Forced to scalar float for UI stability."""
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
                # Use 'Close' specifically to avoid MultiIndex issues
                h = yf.download(t, period="30d", interval="1d", progress=False)
                if not h.empty:
                    # Logic: Recent 5-day volume vs 20-day average
                    curr_vol = float(h['Volume'].tail(5).mean().iloc[0] if isinstance(h['Volume'].tail(5).mean(), pd.Series) else h['Volume'].tail(5).mean())
                    base_vol = float(h['Volume'].tail(20).mean().iloc[0] if isinstance(h['Volume'].tail(20).mean(), pd.Series) else h['Volume'].tail(20).mean())
                    ratio = curr_vol / (base_vol + 1)
                    scores.append(ratio * 100)
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

def get_whale_score_v5(ticker):
    symbol = f"{ticker.upper()}.NS"
    try:
        data = yf.download([symbol, "^NSEI"], period="60d", interval="1d", progress=False)['Close']
        hist = yf.download(symbol, period="60d", interval="1d", progress=False)
        # Ensure we extract scalar values for calculation
        v_curr = float(hist['Volume'].tail(7).mean().iloc[0] if isinstance(hist['Volume'].tail(7).mean(), pd.Series) else hist['Volume'].tail(7).mean())
        v_base = float(hist['Volume'].tail(30).mean().iloc[0] if isinstance(hist['Volume'].tail(30).mean(), pd.Series) else hist['Volume'].tail(30).mean())
        v_ratio = v_curr / (v_base + 1)
        
        # RS Calculation
        s_price = data[symbol].iloc[-1]
        i_price = data["^NSEI"].iloc[-1]
        rs = round(((s_price/data[symbol].iloc[-20]) - (i_price/data["^NSEI"].iloc[-20])) * 100, 2)
        return round(min((v_ratio * 60) + (40 if rs > 0 else 10), 100), 2), float(rs)
    except: return 0.0, 0.0

# --- 3. UI ARCHITECTURE ---

st.title("🏹 Nifty 500 Sniper: The Oracle v29.0")

with st.sidebar:
    st.header("🛰️ Sector Heatmap")
    st.write("Avg Whale Activity (T-30)")
    heat_data = get_sector_heatmap()
    for sector, val in heat_data.items():
        st.write(f"**{sector}:** {round(val, 1)}")
        # Fix: Clamping value between 0.0 and 1.0 for progress bar
        bar_val = max(0.0, min(float(val/150), 1.0))
        st.progress(bar_val)
    
    st.markdown("---")
    if st.button("Force Global Refresh"):
        st.cache_data.clear()
        st.rerun()

tab1, tab2 = st.tabs(["🐋 Whale Radar & Prediction", "🔍 Deep Scan Truth-Meter"])

with tab1:
    l, r = st.columns([1, 2])
    with l:
        st.subheader("Asset Audit")
        target = st.text_input("Ticker:", "RELIANCE").upper()
        if st.button("Execute Scan"):
            score, rs = get_whale_score_v5(target)
            st.metric(f"Whale Score", f"{score}/100")
            st.metric("Relative Strength", f"{rs}%")
            
            st.subheader("📅 Earnings History")
            try:
                hist = yf.Ticker(f"{target}.NS").earnings_dates
                if hist is not None: st.table(hist.head(4).reset_index())
            except: st.warning("No historical data.")

    with r:
        st.subheader("📅 30-Day Official Calendar")
        cal = get_monthly_calendar()
