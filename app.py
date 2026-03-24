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
    return pipeline("sentiment-analysis", model="ProsusAI/finbert")

# --- 2. DATA ENGINES ---

def get_nifty_500_calendar():
    try:
        # Looking 14 days ahead for official NSE announcements
        start = datetime.now().strftime('%d-%m-%Y')
        end = (datetime.now() + timedelta(days=14)).strftime('%d-%m-%Y')
        df = capital_market.board_meetings_announcements(from_date=start, to_date=end)
        if not df.empty:
            # Filter for results or financials
            return df[df['PURPOSE'].str.contains('Results|Audited|Financial', case=False, na=False)]
        return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

def get_whale_score(ticker):
    symbol = f"{ticker.upper()}.NS"
    try:
        # Downloading 60 days of data to compare current 'Whale' activity vs history
        data = yf.download(symbol, period="60d", interval="1d", progress=False)
        if data.empty: return 0
        
        # Whale Logic: Recent Volume Surge (7d vs 30d average)
        vol_7d = data['Volume'].tail(7).mean()
        vol_30d = data['Volume'].tail(30).mean()
        vol_ratio = vol_7d / vol_30d
        
        # Price Action Logic: Above 20-day SMA indicates healthy accumulation
        current_price = data['Close'].iloc[-1]
        sma_20 = data['Close'].rolling(20).mean().iloc[-1]
        
        # Weighted Scoring (0-100)
        score = (vol_ratio * 60) + (40 if current_price > sma_20 else 10)
        return round(min(score, 100), 2)
    except:
        return 0

# --- 3. THE UI LAYOUT ---

st.title("🏹 Nifty 500 Sniper: The Oracle v18.0")
st.markdown(f"**Market Date:** {datetime.now().strftime('%Y-%m-%d')} | **Status:** Monitoring Nifty 500 Whales")

tab1, tab2 = st.tabs(["🐋 Whale Radar (Pre-Earnings)", "🔍 Truth-Meter (Linguistic Audit)"])

with tab1:
    st.header("Pre-Earnings Whale Accumulation")
    
    # Check for official dates
    calendar = get_nifty_500_calendar()
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Run Sniper Scan")
        # Added Manual Override so you don't get stuck if calendar is empty
        manual_ticker = st.text_input("Enter Nifty 500 Ticker (e.g., RELIANCE, TCS, INFY):", "").upper()
        
        if not calendar.empty:
            selected_ticker = st.selectbox("OR Select from Upcoming Results:", calendar['SYMBOL'].unique())
            final_ticker = manual_ticker if manual_ticker else selected_ticker
        else:
            final_ticker = manual_ticker

        if st.button("Execute Whale Audit"):
            if final_ticker:
                with st.spinner(f"Scanning {final_ticker} for institutional footprints..."):
                    score = get_whale_score(final_ticker)
                    st.metric(f"{final_ticker} Whale Score", f"{score}/100")
                    
                    if score > 80:
                        st.success("🔥 WHISPER DETECTED: High institutional accumulation. Positioning for a beat.")
                    elif score > 50:
                        st.info("⚖️ NEUTRAL: Typical market volume. No major Whale divergence.")
                    else:
                        st.warning("⚠️ RETAIL NOISE: Volume is thin. No Smart Money conviction yet.")
            else:
                st.error("Please enter or select a ticker.")

    with col2:
        st.subheader("Official NSE Earnings Window (T-14)")
        if not calendar.empty:
            st.dataframe(calendar[['SYMBOL', 'BOARD_MEETING_DATE', 'PURPOSE']], use_container_width=True)
        else:
            st.info("No official board meetings for 'Results' scheduled in the next 14 days. This is normal in late March.")
            st.write("**Manager's Tip:** Manually scan top stocks like **HDFCBANK** or **RELIANCE** above to find 'pre-announcement' accumulation.")

with tab2:
    st.header("Linguistic Truth-Meter")
    st.write("Analyze the 'Quality' of the results by auditing management's tone.")
    
    raw_text = st.text_area("Paste Management Discussion / Press Release text here:", height=300)
    
    if st.button("Run Truth-Meter Audit"):
        if raw_text:
            oracle_ai = load_oracle_ai()
            # AI Sentiment
            sentiment = oracle_ai(raw_text[:512])[0] # Analyzing first 512 tokens
            # Readability
            readability = textstat.flesch_reading_ease(raw_text)
            
            c1, c2 = st.columns(2)
            c1.metric("Management Tone", sentiment['label'], f"{round(sentiment['score']*100, 1)}% AI Confidence")
            c2.metric("Transparency Score", f"{readability}/100")
            
            if readability < 40:
                st.error("🚩 RED FLAG: High complexity. This is often 'Linguistic Hedging' to hide poor results.")
            else:
                st.success("✅ CLEAN: Transparent communication. Result quality likely high.")
        else:
            st.error("Please paste text for the AI to analyze.")

st.markdown("---")
st.caption("Oracle v18.0 | Mode: Institutional Sniper | Data: NSE India & Yahoo Finance")
