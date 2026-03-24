import streamlit as st
import pandas as pd
import yfinance as yf
from nselib import capital_market
from datetime import datetime, timedelta
from transformers import pipeline
import textstat

# --- 1. CORE CONFIG & AI ENGINE ---
st.set_page_config(page_title="Nifty 500 Sniper v18.0", layout="wide")

@st.cache_resource
def load_oracle_ai():
    return pipeline("sentiment-analysis", model="ProsusAI/finbert")

# --- 2. THE SNIPER ENGINES ---

def get_nifty_500_calendar():
    try:
        start = datetime.now().strftime('%d-%m-%Y')
        end = (datetime.now() + timedelta(days=15)).strftime('%d-%m-%Y')
        df = capital_market.board_meetings_announcements(from_date=start, to_date=end)
        if not df.empty:
            return df[df['PURPOSE'].str.contains('Results|Audited|Financial', case=False, na=False)]
        return pd.DataFrame()
    except:
        return pd.DataFrame()

def get_whale_score(ticker):
    symbol = f"{ticker.upper()}.NS"
    try:
        data = yf.download(symbol, period="60d", interval="1d", progress=False)
        if data.empty: return 0
        vol_7d = data['Volume'].tail(7).mean()
        vol_30d = data['Volume'].tail(30).mean()
        vol_ratio = vol_7d / vol_30d
        current_price = data['Close'].iloc[-1]
        sma_20 = data['Close'].rolling(20).mean().iloc[-1]
        score = (vol_ratio * 60) + (40 if current_price > sma_20 else 10)
        return round(min(score, 100), 2)
    except:
        return 0

def fetch_web_truth(ticker):
    """Automatically pulls news or company profile if news is empty."""
    try:
        stock = yf.Ticker(f"{ticker.upper()}.NS")
        news = stock.news
        
        # Priority 1: Latest News/Filings
        if news:
            full_text = ""
            for item in news[:3]:
                full_text += f"{item.get('title', '')}. {item.get('summary', '')} "
            if len(full_text) > 100:
                return full_text
        
        # Priority 2: Fallback to Company Business Summary
        summary = stock.info.get('longBusinessSummary', "")
        if len(summary) > 100:
            return f"Note: No recent filings. Auditing General Business Statement:\n\n{summary}"
            
        return "Insufficient data found for this ticker on the web."
    except:
        return "Error: Could not connect to market data stream."

# --- 3. THE UI ARCHITECTURE ---

st.title("🏹 Nifty 500 Sniper: The Oracle v18.0")
st.markdown(f"**Status:** Institutional Intelligence Active | **Date:** {datetime.now().strftime('%Y-%m-%d')}")
st.markdown("---")

tab1, tab2 = st.tabs(["🐋 Whale Radar (Pre-Earnings)", "🔍 Automated Truth-Meter (Post-Earnings)"])

# --- TAB 1: PRE-EARNINGS WHALE RADAR ---
with tab1:
    col_left, col_right = st.columns([1, 2])
    with col_left:
        st.subheader("Target Selection")
        target = st.text_input("Enter NSE Ticker (e.g. RELIANCE, TCS):", "").upper()
        if st.button("Run Sniper Scan"):
            if target:
                with st.spinner(f"Analyzing {target}..."):
                    score = get_whale_score(target)
                    st.metric(f"{target} Whale Score", f"{score}/100")
                    if score > 85: st.success("🔥 WHISPER ALERT: Institutional Accumulation.")
                    elif score > 60: st.info("⚖️ ACCUMULATION: Steady buying.")
                    else: st.warning("⚠️ RETAIL NOISE: No Whale activity.")
            else:
                st.error("Please enter a ticker.")
    with col_right:
        st.subheader("Official NSE Earnings Calendar (T-15)")
        calendar = get_nifty_500_calendar()
        if not calendar.empty:
            st.dataframe(calendar[['SYMBOL', 'BOARD_MEETING_DATE', 'PURPOSE']], use_container_width=True)
        else:
            st.info("The NSE calendar is currently quiet.")

# --- TAB 2: AUTOMATED TRUTH-METER ---
with tab2:
    st.header("Automated Linguistic Audit")
    audit_target = st.text_input("Enter Ticker for Web-Audit:", "RELIANCE").upper()
    
    if st.button("Fetch & Audit Reality"):
        with st.spinner(f"Scraping {audit_target}..."):
            truth_text = fetch_web_truth(audit_target)
            
            if "Insufficient data" in truth_text:
                st.error(truth_text)
            else:
                st.subheader("Statement Found:")
                st.info(truth_text)
                
                # Run AI & Linguistic Audit
                oracle_ai = load_oracle_ai()
                sentiment_results = oracle_ai(truth_text[:512])[0]
                
                # Calculate Readability (normalized)
                raw_complexity = textstat.flesch_reading_ease(truth_text)
                transparency = max(0, min(100, raw_complexity))
                
                c1, c2 = st.columns(2)
                c1.metric("Management Tone", sentiment_results['label'], f"{round(sentiment_results['score']*100, 1)}% AI Confidence")
                c2.metric("Transparency Index", f"{round(transparency, 2)}/100")
                
                # Professional Verdict
                if transparency < 35:
                    st.error("🚩 CRITICAL: High Linguistic Obfuscation detected.")
                elif transparency > 65:
                    st.success("✅ CLEAN COMMS: High transparency.")
                else:
                    st.info("⚖️ NEUTRAL: Communication is standard.")

st.markdown("---")
st.caption("Oracle v18.0 | Institutional Sniper Mode | Validation Update Active")
