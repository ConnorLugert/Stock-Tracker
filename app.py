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
        # Get the latest close price (which is the yield %)
        current_yield = t_bill.history(period="1d")['Close'].iloc[-1]
        return current_yield / 100  # Convert 5.25 to 0.0525
    except:
        return 0.04  # Fallback to 4% if fetch fails

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
selected_period = st.selectbox("Select time range:", list(period_map.keys()))
st.caption(f"Current Risk-Free Rate (3M T-Bill): {rf_rate*100:.2f}%")

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
            
            # --- Sharpe Ratio Calculation with Risk-Free Rate ---
            daily_returns = df['Close'].pct_change().dropna()
            if not daily_returns.empty:
                # Annualize the risk-free rate to a daily rate
                daily_rf = (1 + rf_rate)**(1/252) - 1
                
                excess_returns = daily_returns - daily_rf
                sharpe = (excess_returns.mean() / excess_returns.std()) * np.sqrt(252) if excess_returns.std() != 0 else 0
            else:
                sharpe = 0

            # Extract expanded fundamental info
            info = t.info
            fundamental_data.append({
                "Ticker": ticker,
                "Sharpe Ratio": round(sharpe, 2),
                "Market Cap": info.get("marketCap", "N/A"),
                "P/E Ratio": info.get("trailingPE", "N/A"),
                "Div. Yield (%)": f"{info.get('dividendYield', 0) * 100:.2f}%" if info.get('dividendYield') else "0.00%",
                "Profit Margin": f"{info.get('profitMargins', 0) * 100:.2f}%" if info.get('profitMargins') else "N/A",
                "Price to Book": info.get("priceToBook", "N/A"),
            })

    # 1. Metrics
    cols_per_row = 4
    for i in range(0, len(valid_tickers), cols_per_row):
        ticker_chunk = valid_tickers[i : i + cols_per_row]
        cols = st.columns(cols_per
