import streamlit as st
import yfinance as yf
import pandas as pd

st.title("Multi-Stock Comparison")

# Input tickers
ticker_input = st.text_input("Enter tickers separated by commas:", "AAPL, GOOG, NVDA, META, VTI, VOO, VB").upper()
tickers = [t.strip() for t in ticker_input.split(",") if t.strip()]

period_map = {
    "1 Week": "5d", "1 Month": "1mo", "1 Year": "1y", 
    "Year to Date": "ytd", "3 Years": "3y", "10 Years": "10y"
}
selected_period = st.selectbox("Select time range:", list(period_map.keys()))

if tickers:
    data_dict = {}
    valid_tickers = []

    # 1. First, fetch all data
    for ticker in tickers:
        df = yf.Ticker(ticker).history(period=period_map[selected_period])
        if not df.empty:
            data_dict[ticker] = df.Close
            valid_tickers.append(ticker)

    # 2. Logic to display in rows of 4
    cols_per_row = 4
    for i in range(0, len(valid_tickers), cols_per_row):
        # Get the subset of tickers for this row
        ticker_chunk = valid_tickers[i : i + cols_per_row]
        cols = st.columns(cols_per_row)
        
        for j, ticker in enumerate(ticker_chunk):
            df = yf.Ticker(ticker).history(period=period_map[selected_period])
            start = df.Close.iloc[0]
            end = df.Close.iloc[-1]
            delta = end - start
            pct = (delta / start) * 100
            
            with cols[j]:
                st.metric(f"{ticker}", f"${end:.2f}", f"${delta:.2f} ({pct:.2f}%)")
    
    # 3. Plotting
    if data_dict:
        st.line_chart(pd.DataFrame(data_dict))
    else:
        st.error("No data found for the entered tickers.")
