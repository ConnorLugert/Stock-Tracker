import streamlit as st
import yfinance as yf

st.title("Simple Stock Price App")

ticker_symbol = st.text_input("Enter Ticker Symbol (e.g., AAPL, GOOGL):", "AAPL")

if ticker_symbol:
    ticker_data = yf.Ticker(ticker_symbol)
    ticker_df = ticker_data.history(period="1mo")
    
    st.write(f"### Closing Price for {ticker_symbol}")
    st.line_chart(ticker_df.Close)
