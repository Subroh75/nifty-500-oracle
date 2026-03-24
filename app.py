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
    # FinBERT: Specialized for Financial Sentiment
    return pipeline("sentiment-analysis", model="ProsusAI/finbert")

# --- 2. THE SNIPER ENGINES ---

def get_nifty_500_calendar():
    """Fetches official NSE board meetings for the next 15 days."""
    try:
        start = datetime.now().strftime('%d-%m-%Y')
        end = (datetime.now() + timedelta(days=15)).strftime('%d-%m-%Y')
        df = capital_market.board_meetings_announcements(from_date=start, to_date=end)
        if not df.empty:
            # Filter for results or audited financials
            return df[df['PURPOSE'].str.contains('Results|Audited|Financial', case=False, na=False)]
        return pd.DataFrame()
    except:
        return pd.DataFrame()

def get_whale_score(ticker):
    """Calculates Institutional Accumulation Score."""
    symbol = f"{ticker.upper()}.NS"
    try:
        data = yf.download(symbol, period="60d", interval="1d", progress=False)
        if data.empty: return 0
        
        # Metric 1: Volume Momentum (7d Avg vs 30d Avg)
        vol_7d = data['Volume'].tail(7).mean()
        vol_30d = data['Volume'].tail(30).mean()
        vol_ratio = vol_7d / vol_30d
        
        # Metric 2: Price Strength (Current vs 20d SMA)
        current_price = data['Close'].iloc[-1]
        sma_20 = data['Close'].rolling(20).mean().iloc[-1]
        
        # Scoring Logic
        score = (vol_ratio * 60) + (40 if current_price > sma_20 else 10)
        return round(min(score, 100), 2)
    except:
        return 0

def fetch_web_truth(ticker):
    """Automatically pulls the latest corporate news/summaries for the AI."""
    try:
        stock = yf.Ticker(f"{ticker.upper()}.NS")
        news = stock.news
        if news:
            # Aggregate top 3 news summaries to provide a larger text sample for NLP
            full_text = ""
            for item in news[:3]:
                full_text += f"{item.get('title', '')}. {item.get('summary', '')} "
            return full_text if len(full_text) > 50 else "Sample text too brief for reliable audit."
        return "No recent web filings found for this ticker."
    except:
        return "Error: Could not establish a connection to the data stream."

# --- 3. THE UI ARCHITECTURE ---

st.title("🏹 Nifty 500 Sniper: The Oracle v18.0")
st.markdown(f"**Status:** Institutional Intelligence Active | **Date:** {datetime.now().strftime('%Y-%m-%d')}")
st.markdown("---")

tab1, tab2 = st.tabs(["🐋 Whale Radar (Pre-Earnings)", "🔍 Automated Truth-Meter (Post-Earnings)"])

# --- TAB 1: PRE-EARNINGS WHALE RADAR ---
with tab1:
    col_a, col_b = st.columns([1, 2])
    
    with col_a:
        st.subheader("Target Selection")
        target = st.text_input("Enter NSE Ticker (e.g. RELIANCE, TCS, HDFCBANK):", "").upper()
        
        if st.button("Run Sniper Scan"):
            if target:
                with st.spinner(f"Analyzing {target} Whale footprints..."):
                    score = get_whale_score(target)
                    st.metric(f"{target} Whale Score", f"{score}/100")
                    
                    if score > 85:
                        st.success("🔥 WHISPER ALERT: Massive Institutional Accumulation Detected.")
                    elif score > 60:
                        st.info("⚖️ ACCUMULATION: Steady buying detected.")
                    else:
                        st.warning("⚠️ RETAIL NOISE: No significant Whale divergence.")
            else:
                st.error("Please enter a ticker to scan.")

    with col_right:
        st.subheader("Official NSE Earnings Calendar (T-15)")
        calendar = get_nifty_500_calendar()
        if not calendar.empty:
            st.dataframe(calendar[['SYMBOL', 'BOARD_MEETING_DATE', 'PURPOSE']], use_container_width=True)
        else:
            st.info("The official NSE calendar is quiet. Use the 'Manual Scan' for pre-announcement moves.")

# --- TAB 2: AUTOMATED TRUTH-METER ---
with tab2:
    st.header("Automated Linguistic Audit")
    st.write("This engine scrapes the latest corporate narratives to detect 'Management Decay'.")
    
    audit_target = st.text_input("Enter Ticker for Web-Audit:", "RELIANCE").upper()
    
    if st.button("Fetch & Audit Reality"):
        with st.spinner(f"Scraping and analyzing {audit_target}..."):
            # 1. DATA ACQUISITION
            truth_text = fetch_web_truth(audit_target)
            st.subheader("Latest Corporate Filing Found:")
            st.info(truth_text)
            
            # 2. AI SENTIMENT (FinBERT)
            oracle_ai = load_oracle_ai()
            sentiment_results = oracle_ai(truth_text[:512])[0] # Handling token limits
            
            # 3. NORMALIZED READABILITY (Clamped 0-100)
            raw_complexity = textstat.flesch_reading_ease(truth_text)
            transparency = max(0, min(100, raw_complexity))
            
            # 4. RESULTS DISPLAY
            c1, c2 = st.columns(2)
            c1.metric("Management Tone", sentiment_results['label'], f"{round(sentiment_results['score']*100, 1)}% AI Confidence")
            c2.metric("Transparency Index", f"{round(transparency, 2)}/100")
            
            # 5. EXPERT VERDICT LOGIC
            if transparency < 35:
                st.error("🚩 CRITICAL: High Linguistic Obfuscation. Management is likely hiding weak fundamentals.")
            elif sentiment_results['label'] == 'neutral' and transparency < 50:
                st.warning("⚠️ CAUTION: Neutral tone paired with low transparency suggests 'Linguistic Hedging'.")
            elif transparency > 65:
                st.success("✅ CLEAN COMMS: High transparency detected. Corporate reporting appears reliable.")

st.markdown("---")
st.caption("Oracle v18.0 | Mode: Institutional Sniper | Multi-Source Web Extraction Active")
