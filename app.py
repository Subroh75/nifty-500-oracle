import streamlit as st
import pandas as pd
import yfinance as yf
from nselib import capital_market
from datetime import datetime, timedelta
from transformers import pipeline
import textstat
import re

# --- 1. CORE CONFIG & AI CACHING ---
st.set_page_config(page_title="Nifty 500 Sniper v20.0", layout="wide")

@st.cache_resource
def load_oracle_ai():
    # Forced CPU mode for Streamlit Cloud stability
    return pipeline("sentiment-analysis", model="ProsusAI/finbert", device=-1)

# --- 2. THE INTELLIGENCE ENGINES ---

def get_nifty_500_calendar():
    try:
        start = datetime.now().strftime('%d-%m-%Y')
        end = (datetime.now() + timedelta(days=15)).strftime('%d-%m-%Y')
        df = capital_market.board_meetings_announcements(from_date=start, to_date=end)
        if not df.empty:
            return df[df['PURPOSE'].str.contains('Results|Audited|Financial', case=False, na=False)]
        return pd.DataFrame()
    except: return pd.DataFrame()

def get_whale_score(ticker):
    symbol = f"{ticker.upper()}.NS"
    try:
        data = yf.download(symbol, period="60d", interval="1d", progress=False)
        if data.empty: return 0
        vol_7d, vol_30d = data['Volume'].tail(7).mean(), data['Volume'].tail(30).mean()
        vol_ratio = vol_7d / (vol_30d + 1)
        current_price = data['Close'].iloc[-1]
        sma_20 = data['Close'].rolling(20).mean().iloc[-1]
        score = (vol_ratio * 60) + (40 if current_price > sma_20 else 10)
        return round(min(score, 100), 2)
    except: return 0

def fetch_deep_truth(ticker):
    try:
        stock = yf.Ticker(f"{ticker.upper()}.NS")
        news = stock.news
        if news:
            content = " ".join([n.get('title', '') + ". " + n.get('summary', '') for n in news[:3]])
            if len(content) > 100: return content, "Live News Feed (Dynamic)"
        summary = stock.info.get('longBusinessSummary', "")
        if len(summary) > 100: return summary, "Official Corporate Profile (Static)"
        return None, "Insufficient data."
    except: return None, "Connection error."

def audit_text_v2(text, source):
    """Refined Engine: Normalizes for Industrial Conglomerates."""
    raw_score = textstat.flesch_reading_ease(text)
    
    # Check for Conglomerate complexity (Multiple business segments)
    segments = ['oil', 'retail', 'digital', 'telecom', 'media', 'bank', 'chemicals', 'energy']
    segment_count = sum(1 for s in segments if s in text.lower())
    
    # Normalization Logic
    if segment_count > 3: raw_score += 15  # Conglomerate Grace
    if "Static" in source: raw_score += 10 # Profile Grace
    
    # Comma Density Filter (Identifies part-lists/product catalogs)
    comma_count = len(re.findall(r',', text))
    word_count = len(text.split())
    if (comma_count / (word_count + 1)) > 0.07: raw_score += 20 # Product List Grace
    
    return max(0, min(100, raw_score))

# --- 3. THE UI LAYOUT ---

st.title("🏹 Nifty 500 Sniper: The Oracle v20.0")

with st.sidebar:
    st.header("🛰️ Sniper Controls")
    st.success("System: ONLINE")
    st.write("Current Market: NSE India")
    if st.button("Purge Cache & Rerun"):
        st.cache_resource.clear()
        st.rerun()

tab1, tab2 = st.tabs(["🐋 Whale Radar", "🔍 Automated Truth-Meter"])

with tab1:
    col_l, col_r = st.columns([1, 2])
    with col_l:
        st.subheader("Asset Selection")
        target = st.text_input("Enter Ticker:", "").upper()
        if st.button("Execute Whale Audit"):
            if target:
                score = get_whale_score(target)
                st.metric(f"{target} Whale Score", f"{score}/100")
                if score > 85: st.success("🔥 WHISPER ALERT: Institutional Accumulation.")
                else: st.info("Monitoring Smart Money footprints...")
    with col_r:
        st.subheader("Official Results Calendar (T-15)")
        calendar = get_nifty_500_calendar()
        if not calendar.empty:
            st.dataframe(calendar[['SYMBOL', 'BOARD_MEETING_DATE', 'PURPOSE']], use_container_width=True)
        else: st.info("Official NSE Calendar is currently empty.")

with tab2:
    st.header("Automated Deep Scan Audit")
    audit_target = st.text_input("Ticker for Audit:", "RELIANCE").upper()
    if st.button("Execute Deep Scan"):
        with st.spinner(f"Initiating Intelligence Scan for {audit_target}..."):
            truth_text, source = fetch_deep_truth(audit_target)
            if truth_text:
                st.subheader(f"Data Source: {source}")
                st.info(truth_text)
                
                oracle_ai = load_oracle_ai()
                sentiment = oracle_ai(truth_text[:512])[0]
                transparency = audit_text_v2(truth_text, source)
                
                c1, c2 = st.columns(2)
                c1.metric("Management Tone", sentiment['label'].upper(), f"{round(sentiment['score']*100, 1)}% Confidence")
                c2.metric("Transparency Index", f"{round(transparency, 2)}/100")
                
                if transparency < 35:
                    st.error("🚩 CRITICAL: High Linguistic Obfuscation. High risk of Management Decay.")
                elif "Static" in source and transparency < 55:
                    st.warning("⚠️ NOTE: Transparency score is impacted by technical product lists. Monitor live filings for conviction.")
                elif transparency > 65:
                    st.success("✅ CLEAN COMMS: High transparency detected.")
                else:
                    st.info("⚖️ NEUTRAL: Communication is within standard institutional ranges.")
            else:
                st.error("Data unavailable for this ticker.")
