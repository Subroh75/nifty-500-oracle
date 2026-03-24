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
    # FinBERT - Optimized for Financial Nuance
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

def fetch_deep_truth(ticker):
    """
    Automated Deep Scan: 
    Pivots from News -> Corporate Profile -> Web Summary to ensure AI has data.
    """
    try:
        stock = yf.Ticker(f"{ticker.upper()}.NS")
        
        # Level 1: Recent News Filings
        news = stock.news
        if news and len(news) > 0:
            content = " ".join([n.get('title', '') + ". " + n.get('summary', '') for n in news[:3]])
            if len(content) > 100:
                return content, "Source: Live News Feed"

        # Level 2: Official Business Narrative (Fallback)
        summary = stock.info.get('longBusinessSummary', "")
        if len(summary) > 100:
            return summary, "Source: Official Corporate Profile"
            
        return None, "Insufficient data across all web channels."
    except:
        return None, "Connection error to NSE/Yahoo data stream."

# --- 3. THE UI ARCHITECTURE ---

st.title("🏹 Nifty 500 Sniper: The Oracle v18.0")
st.markdown(f"**Status:** Institutional Mode Active | **System Date:** {datetime.now().strftime('%Y-%m-%d')}")
st.markdown("---")

tab1, tab2 = st.tabs(["🐋 Whale Radar (Pre-Earnings)", "🔍 Automated Truth-Meter (Post-Earnings)"])

# --- TAB 1: WHALE RADAR ---
with tab1:
    col_l, col_r = st.columns([1, 2])
    with col_l:
        st.subheader("Target Selection")
        target = st.text_input("Enter NSE Ticker (e.g. RELIANCE, TCS):", "").upper()
        if st.button("Run Sniper Scan"):
            if target:
                with st.spinner(f"Analyzing {target}..."):
                    score = get_whale_score(target)
                    st.metric(f"{target} Whale Score", f"{score}/100")
                    if score > 85: st.success("🔥 WHISPER ALERT: Institutional Accumulation.")
                    elif score > 60: st.info("⚖️ ACCUMULATION: Steady institutional buying.")
                    else: st.warning("⚠️ RETAIL NOISE: No significant Whale footprints.")
            else:
                st.error("Please enter a ticker.")
    with col_r:
        st.subheader("Official NSE Calendar (T-15)")
        calendar = get_nifty_500_calendar()
        if not calendar.empty:
            st.dataframe(calendar[['SYMBOL', 'BOARD_MEETING_DATE', 'PURPOSE']], use_container_width=True)
        else:
            st.info("The NSE board meeting calendar is currently quiet.")

# --- TAB 2: DEEP SCAN TRUTH-METER ---
with tab2:
    st.header("Automated Deep Scan Audit")
    audit_target = st.text_input("Enter Ticker for Linguistic Audit:", "RELIANCE").upper()
    
    if st.button("Execute Deep Scan"):
        with st.spinner(f"Initiating Deep Scan for {audit_target}..."):
            truth_text, source_info = fetch_deep_truth(audit_target)
            
            if not truth_text:
                st.error(f"Audit Failed: {source_info}")
            else:
                st.subheader(f"Data Found ({source_info})")
                st.info(truth_text)
                
                # AI & Readability Audit
                oracle_ai = load_oracle_ai()
                sentiment = oracle_ai(truth_text[:512])[0]
                
                # Normalize Transparency (0-100)
                raw_ease = textstat.flesch_reading_ease(truth_text)
                transparency = max(0, min(100, raw_ease))
                
                c1, c2 = st.columns(2)
                c1.metric("Management Tone", sentiment['label'], f"{round(sentiment['score']*100, 1)}% AI Confidence")
                c2.metric("Transparency Index", f"{round(transparency, 2)}/100")
                
                # Expert Verdict
                if transparency < 35:
                    st.error("🚩 CRITICAL: High Linguistic Obfuscation. Possible 'Management Decay'.")
                elif transparency > 65:
                    st.success("✅ CLEAN COMMS: High transparency detected.")
                else:
                    st.info("⚖️ NEUTRAL: Communication is within standard ranges.")

st.markdown("---")
st.caption("Oracle v18.0 | Deep Scan Mode | Automated Fallback Logic Active")
