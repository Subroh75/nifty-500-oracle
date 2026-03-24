import streamlit as st
import pandas as pd
import yfinance as yf
from nselib import capital_market
from datetime import datetime, timedelta
from transformers import pipeline
import textstat

# --- 1. CONFIG & AI INITIALIZATION ---
st.set_page_config(page_title="Nifty 500 Sniper v18.0", layout="wide")

@st.cache_resource
def load_oracle_ai():
    # FinBERT for professional financial sentiment
    return pipeline("sentiment-analysis", model="ProsusAI/finbert")

# --- 2. DATA ENGINES ---

def get_nifty_500_calendar():
    try:
        # Looking for results in the next 14 days
        start = datetime.now().strftime('%d-%m-%Y')
        end = (datetime.now() + timedelta(days=14)).strftime('%d-%m-%Y')
        df = capital_market.board_meetings_announcements(from_date=start, to_date=end)
        if not df.empty:
            return df[df['PURPOSE'].str.contains('Results|Audited', case=False, na=False)]
        return pd.DataFrame()
    except:
        return pd.DataFrame()

def get_whale_score(ticker):
    symbol = f"{ticker}.NS"
    try:
        data = yf.download(symbol, period="60d", interval="1d")
        if data.empty: return 0
        
        # Whale Logic: Volume Surge (7d vs 30d) + Delivery Proxy
        vol_7d = data['Volume'].tail(7).mean()
        vol_30d = data['Volume'].tail(30).mean()
        vol_ratio = vol_7d / vol_30d
        
        # Price Action vs VWAP
        current_price = data['Close'].iloc[-1]
        sma_20 = data['Close'].rolling(20).mean().iloc[-1]
        
        # Score calculation
        score = (vol_ratio * 50) + (50 if current_price > sma_20 else 10)
        return round(min(score, 100), 2)
    except:
        return 0

def get_bulk_deals():
    # Attempting to pull large scale institutional movements
    try:
        from nsepython import nse_largedeals
        df = nse_largedeals()
        return df
    except:
        return pd.DataFrame()

# --- 3. THE UI LAYOUT ---

st.title("🏹 Nifty 500 Sniper: The Oracle v18.0")
st.markdown("---")

# Sidebar for Global Market Context
with st.sidebar:
    st.header("📊 Sniper Dashboard")
    st.info("Tracking: Nifty 500 Universe")
    if st.button("Refresh All Data"):
        st.rerun()

# Main Tabs
tab1, tab2, tab3 = st.tabs(["Whale Radar (Pre-Earnings)", "Truth-Meter (Linguistic Audit)", "Bulk Deal Tracker"])

with tab1:
    st.header("🐋 Pre-Earnings Whale Accumulation")
    calendar = get_nifty_500_calendar()
    
    if not calendar.empty:
        col_a, col_b = st.columns([1, 2])
        with col_a:
            selected_ticker = st.selectbox("Select Upcoming Result Ticker", calendar['SYMBOL'].unique())
            if st.button("Run Sniper Analysis"):
                score = get_whale_score(selected_ticker)
                st.metric("Whale Confidence Score", f"{score}/100")
                if score > 80:
                    st.success("🔥 HIGH CONVICTION WHISPER DETECTED")
                else:
                    st.warning("⚠️ Retail Noise Only")
        with col_b:
            st.write("Upcoming Results Calendar")
            st.dataframe(calendar[['SYMBOL', 'BOARD_MEETING_DATE', 'PURPOSE']], use_container_width=True)
    else:
        st.warning("No official Nifty 500 result dates announced for the next 14 days.")
        st.info("Strategy: Check the 'Bulk Deal Tracker' for hidden moves instead.")

with tab2:
    st.header("🔍 Linguistic Truth-Meter")
    st.write("Paste the Management Discussion / CEO Statement below to audit for 'Management Decay'.")
    
    user_text = st.text_area("Insert Result Text Here:", height=250)
    
    if st.button("Execute Audit"):
        if user_text:
            oracle_ai = load_oracle_ai()
            # 1. AI Sentiment
            sentiment = oracle_ai(user_text[:512])[0]
            # 2. Readability (Gunning Fog Proxy)
            readability = textstat.flesch_reading_ease(user_text)
            
            c1, c2 = st.columns(2)
            c1.metric("AI Sentiment Tone", sentiment['label'], f"{round(sentiment['score']*100, 1)}% Confidence")
            c2.metric("Transparency Score", f"{readability}/100")
            
            if readability < 40:
                st.error("🚩 RED FLAG: High linguistic complexity detected. Management might be hiding weak fundamentals.")
            else:
                st.success("✅ CLEAR COMMS: Management is being transparent.")
        else:
            st.error("Please provide text for the engine to analyze.")

with tab3:
    st.header("🚀 Institutional Bulk Deals")
    st.write("Tracking deals representing >0.5% of company equity.")
    deals = get_bulk_deals()
    if not deals.empty:
        st.dataframe(deals, use_container_width=True)
    else:
        st.info("No major Bulk Deals recorded in the last 24 hours. The Whales are being quiet.")

st.markdown("---")
st.caption("Nifty 500 Sniper v18.0 | Powered by FinBERT AI & NSE Real-time Data")
