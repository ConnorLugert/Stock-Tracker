import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="Stock Tracker", layout="wide")
st.title("Multi-Stock Comparison")

# --- Function to fetch Risk-Free Rate (3-Month T-Bill) ---
def get_risk_free_rate():
    try:
        # ^IRX is the ticker for 13-week (3-month) Treasury Bill yield
        t_bill = yf.Ticker("^IRX")
        current_yield = t_bill.history(period="1d")['Close'].iloc[-1]
        return current_yield / 100 
    except:
        return 0.04 

rf_rate = get_risk_free_rate()

# Sidebar / Inputs
ticker_input = st.text_input("Enter tickers separated by commas:", "AAPL, GOOG, NVDA, META, VTI, VOO, VB").upper()
tickers = [t.strip() for t in ticker_input.split(",") if t.strip()]

period_map = {
    "1 Week": "5d",
    "1 Month": "1mo",
    "1 Year": "1y",
    "Year to Date": "ytd",
    "3 Years": "3y",
    "10 Years": "10y"
}

col_top1, col_top2 = st.columns([2, 1])
with col_top1:
    selected_period = st.selectbox("Select time range:", list(period_map.keys()))
with col_top2:
    # Explicitly stating the Risk-Free Rate source and value
    st.info(f"**Risk-Free Rate:** {rf_rate*100:.2f}% \n\n (Based on 3-Month Treasury Bills)")

if tickers:
    data_dict = {}
    valid_tickers = []
    fundamental_data = []

    for ticker in tickers:
        t = yf.Ticker(ticker)
        df = t.history(period=period_map[selected_period])
        if not df.empty:
            data_dict[ticker] = df.Close
            valid_tickers.append(ticker)
            
            # --- Sharpe Ratio Calculation ---
            daily_returns = df['Close'].pct_change().dropna()
            if not daily_returns.empty:
                daily_rf = (1 + rf_rate)**(1/252) - 1
                excess_returns = daily_returns - daily_rf
                sharpe = (excess_returns.mean() / excess_returns.std()) * np.sqrt
