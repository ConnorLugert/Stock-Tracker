import streamlit as st
import yfinance as yf

st.title("Stock Price App")

ticker_symbol = st.text_input("Enter Ticker Symbol (e.g., AAPL, GOOGL):", "AAPL")

if ticker_symbol:
    # Define the periods
    period_map = {
        "1 Week": "5d",
        "1 Month": "1mo",
        "1 Year": "1y",
        "Year to Date": "ytd",
        "3 Years": "3y",
        "10 Years": "10y"
    }

    # Create the dropdown
    selected_period = st.selectbox("Select time range:", list(period_map.keys()))

    # Fetch data based on selection
    ticker_data = yf.Ticker(ticker_symbol)
    ticker_df = ticker_data.history(period=period_map[selected_period])
    
    st.write(f"### Closing Price for {ticker_symbol}")
    st.line_chart(ticker_df.Close)
