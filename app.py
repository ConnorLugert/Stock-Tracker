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

# Moving Average Input
ma_window = st.number_input("Moving Average Window (days):", min_value=1, max_value=365, value=50)

if tickers:
    data_dict = {}
    ma_dict = {}
    valid_tickers = []

    for ticker in tickers:
        df = yf.Ticker(ticker).history(period=period_map[selected_period])
        if not df.empty:
            data_dict[ticker] = df.Close
            # Calculate Moving Average
            ma_dict[f"{ticker} MA"] = df.Close.rolling(window=ma_window).mean()
            valid_tickers.append(ticker)

    # 1. Metrics (Row Logic)
    cols_per_row = 4
    for i in range(0, len(valid_tickers), cols_per_row):
        ticker_chunk = valid_tickers[i : i + cols_per_row]
        cols = st.columns(cols_per_row)
        for j, ticker in enumerate(ticker_chunk):
            df = yf.Ticker(ticker).history(period=period_map[selected_period])
            start, end = df.Close.iloc[0], df.Close.iloc[-1]
            delta = end - start
            pct = (delta / start) * 100
            with cols[j]:
                st.metric(f"{ticker}", f"${end:.2f}", f"${delta:.2f} ({pct:.2f}%)")
    
    # 2. Main Price Chart
    if data_dict:
        st.subheader("Price History")
        st.line_chart(pd.DataFrame(data_dict))
        
        # 3. Moving Average Chart
        st.subheader(f"{ma_window}-Day Moving Average")
        st.line_chart(pd.DataFrame(ma_dict))
    else:
        st.error("No data found for the entered tickers.")
