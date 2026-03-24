import streamlit as st
import pandas as pd
import yfinance as yf
from nselib import capital_market
from datetime import datetime, timedelta
from transformers import pipeline
import textstat

# --- 1. THE BRAIN: AI SENTIMENT MODEL ---
@st.cache_resource
def load_finbert():
    # Professional-grade financial sentiment analysis
    return pipeline("sentiment-analysis", model="ProsusAI/finbert")

# --- 2. DATA ENGINES ---
def get_nifty_500_calendar():
    try:
        start = datetime.now().strftime('%d-%m-%Y')
        end = (datetime.now() + timedelta(days=14)).strftime('%d-%m-%Y')
        df = capital_market.board_meetings_announcements(from_date=start, to_date=end)
        return df[df['PURPOSE'].str.contains('Results', case=False, na=False)]
    except:
        return pd.DataFrame()

def get_whale_score(ticker):
    symbol = f"{ticker}.NS"
    data = yf.download(symbol, period="60d", interval="1d")
    if data.empty: return 0
    
    # Whale Logic: Volume Surge + Price Stability = Quiet Accumulation
    vol_7d = data['Volume'].tail(7).mean()
    vol_30d = data['Volume'].tail(30).mean()
    vol_ratio = vol_7d / vol_30d
    
    # 7-day VWAP Adherence
    data['VWAP'] = (data['Close'] * data['Volume']).cumsum() / data['Volume'].cumsum()
    current_price = data['Close'].iloc[-1]
    vwap_last = data['VWAP'].iloc[-1]
    
    # Score 0-100: Higher is more "Whale-heavy"
    score = (vol_ratio * 50) + (50 if current_price >= vwap_last else 20)
    return round(min(score, 100), 2)

# --- 3. THE INTERFACE ---
st.set_page_config(page_title="Oracle v18.0", layout="wide", initial_sidebar_state="expanded")
st.title("🏹 Nifty 500 Oracle: Whisper vs. Reality")

# Load AI
with st.spinner("Initializing AI Audit Engine..."):
    sentiment_pipe = load_finbert()

tab1, tab2 = st.tabs(["Pre-Earnings: Whale Radar", "Post-Earnings: Truth-Meter"])

with tab1:
    st.header("🐋 Pre-Earnings Whale Accumulation")
    calendar = get_nifty_500_calendar()
    
    if not calendar.empty:
        selected_ticker = st.selectbox("Select Nifty 500 Ticker", calendar['SYMBOL'].unique())
        if st.button("Audit Whale Positioning"):
            score = get_whale_score(selected_ticker)
            st.metric("Whale Score", f"{score}/100")
            if score > 80:
                st.success(f"STRONG WHISPER: High institutional footprint in {selected_ticker}.")
            else:
                st.info("Neutral: Retail-driven volume patterns.")
    else:
        st.warning("No Nifty 500 earnings scheduled in the next 14 days.")

with tab2:
    st.header("🔍 Post-Earnings Truth-Meter")
    management_text = st.text_area("Paste the CEO's Statement or MD&A section from the results PDF:", height=200)
    
    if st.button("Run Linguistic Audit"):
        if management_text:
            # 1. Readability Audit
            readability = textstat.flesch_reading_ease(management_text)
            # 2. AI Sentiment Audit
            sentiment = sentiment_pipe(management_text[:512])[0]
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Transparency Score")
                st.progress(readability/100)
                st.write(f"Score: {readability} (Higher is more transparent)")
            
            with col2:
                st.subheader("AI Sentiment Analysis")
                st.write(f"Tone: **{sentiment['label']}**")
                st.write(f"Confidence: {round(sentiment['score']*100, 2)}%")
        else:
            st.error("Please paste text to analyze.")
