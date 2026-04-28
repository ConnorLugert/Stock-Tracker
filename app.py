import streamlit as st
import yfinance as yf
import pandas as pd

st.title("Multi-Stock Comparison")

# 1. Default tickers set to AAPL, GOOG, NVDA
ticker_input = st.text_input("Enter tickers separated by commas:", "AAPL, GOOG, NVDA").upper()
tickers = [t.strip() for t in ticker_input.split(",") if t.strip()]

period_map = {
    "1 Week": "5d", "1 Month": "1mo", "1 Year": "1y", 
    "Year to Date": "ytd", "3 Years": "3y", "10 Years": "10y"
}
selected_period = st.selectbox("Select time range:", list(period_map.keys()))

if tickers:
    data_dict = {}
    
    # Create columns to display metrics horizontally
    # We create a column for each ticker
    cols = st.columns(len(tickers))
    
    for i, ticker in enumerate(tickers):
        df = yf.Ticker(ticker).history(period=period_map[selected_period])
        if not df.empty:
            data_dict[ticker] = df.Close
            
            # Show metrics in the corresponding column
            start = df.Close.iloc[0]
            end = df.Close.iloc[-1]
            delta = end - start
            pct = (delta / start) * 100
            
            with cols[i]:
                st.metric(f"{ticker}", f"${end:.2f}", f"${delta:.2f} ({pct:.2f}%)")
    
    # Plotting
    if data_dict:
        combined_df = pd.DataFrame(data_dict)
        st.line_chart(combined_df)
    else:
        st.error("No data found for the entered tickers.")
