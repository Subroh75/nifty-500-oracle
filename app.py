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
    # Loading FinBERT - The gold standard for financial NLP
    return pipeline("sentiment-analysis", model="ProsusAI/finbert")

# --- 2. THE SNIPER FUNCTIONS ---

def get_nifty_500_calendar():
    """Fetches official NSE board meetings for the next 15 days."""
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
    """Calculates Institutional Accumulation based on Volume/Price Divergence."""
    symbol = f"{ticker.upper()}.NS"
    try:
        data = yf.download(symbol, period="60d", interval="1d", progress=False)
        if data.empty: return 0
        
        # Metric 1: Volume Surge (7-day Avg vs 30-day Avg)
        vol_7d = data['Volume'].tail(7).mean()
        vol_30d = data['Volume'].tail(30).mean()
        vol_ratio = vol_7d / vol_30d
        
        # Metric 2: Price Position (Relative to 20-day SMA)
        current_price = data['Close'].iloc[-1]
        sma_20 = data['Close'].rolling(20).mean().iloc[-1]
        
        # Scoring: 60% Volume Weight, 40% Price Trend
        score = (vol_ratio * 60) + (40 if current_price > sma_20 else 10)
        return round(min(score, 100), 2)
    except:
        return 0

def fetch_web_truth(ticker):
    """Automatically pulls the latest corporate statements/news from the web."""
    try:
        stock = yf.Ticker(f"{ticker.upper()}.NS")
        news = stock.news
        if news:
            # We extract the summary of the most recent corporate announcement
            # This replaces manual copy-pasting
            latest_report = news[0].get('summary', "")
            title = news[0].get('title', "")
            return f"HEADLINE: {title}\n\nSUMMARY: {latest_report}"
        return "No recent web filings found for this ticker."
    except:
        return "Error: Could not connect to the web data stream."

# --- 3. THE UI ARCHITECTURE ---

st.title("🏹 Nifty 500 Sniper: The Oracle v18.0")
st.markdown(f"**Live Market Monitor** | System Date: {datetime.now().strftime('%Y-%m-%d')}")
st.markdown("---")

tab1, tab2 = st.tabs(["🐋 Whale Radar (Pre-Earnings)", "🔍 Automated Truth-Meter (Post-Earnings)"])

# --- TAB 1: PRE-EARNINGS WHALE RADAR ---
with tab1:
    col_left, col_right = st.columns([1, 2])
    
    with col_left:
        st.subheader("Target Selection")
        # Manual input for any Nifty 500 stock
        target = st.text_input("Enter NSE Ticker (e.g. RELIANCE, TCS, HDFCBANK):", "").upper()
        
        if st.button("Run Sniper Scan"):
            if target:
                with st.spinner(f"Analyzing {target} Whale footprints..."):
                    score = get_whale_score(target)
                    st.metric(f"{target} Whale Score", f"{score}/100")
                    
                    if score > 85:
                        st.success("🔥 WHISPER ALERT: Extreme Institutional Accumulation.")
                    elif score > 60:
                        st.info("⚖️ ACCUMULATION: Steady institutional buying detected.")
                    else:
                        st.warning("⚠️ RETAIL NOISE: No significant Whale activity.")
            else:
                st.error("Please enter a ticker to scan.")

    with col_right:
        st.subheader("Official NSE Calendar (Next 15 Days)")
        calendar = get_nifty_500_calendar()
        if not calendar.empty:
            st.dataframe(calendar[['SYMBOL', 'BOARD_MEETING_DATE', 'PURPOSE']], use_container_width=True)
        else:
            st.info("The official NSE board meeting calendar is currently quiet. This is normal in the 2-week lead-up to result season.")
            st.write("**Manager Note:** Use the 'Target Selection' on the left to scan stocks *before* the dates are officially posted.")

# --- TAB 2: AUTOMATED TRUTH-METER ---
with tab2:
    st.header("Automated Linguistic Audit")
    st.write("This engine automatically fetches the latest corporate statements and runs an AI Audit for 'Management Decay'.")
    
    audit_target = st.text_input("Enter Ticker for Web-Audit:", "RELIANCE").upper()
    
    if st.button("Fetch & Audit Reality"):
        with st.spinner(f"Scraping web data for {audit_target}..."):
            # 1. FETCH DATA
            truth_text = fetch_web_truth(audit_target)
            st.subheader("Latest Corporate Filing Found:")
            st.info(truth_text)
            
            # 2. RUN AI SENTIMENT
            oracle_ai = load_oracle_ai()
            sentiment_results = oracle_ai(truth_text[:512])[0] # AI limit check
            
            # 3. RUN READABILITY
            complexity = textstat.flesch_reading_ease(truth_text)
            
            # 4. DISPLAY RESULTS
            c1, c2 = st.columns(2)
            c1.metric("Management Sentiment", sentiment_results['label'], f"{round(sentiment_results['score']*100, 1)}% AI Confidence")
            c2.metric("Transparency Index", f"{complexity}/100")
            
            if complexity < 35:
                st.error("🚩 WARNING: High Linguistic Obfuscation. Management is using complex language to mask performance.")
            elif complexity > 65:
                st.success("✅ CLEAN: Transparent and straightforward communication.")
            else:
                st.info("⚖️ NEUTRAL: Communication is within standard corporate ranges.")

st.markdown("---")
st.caption("Nifty 500 Sniper v18.0 | Institutional Intelligence Layer | Built for High-Alpha Execution")
