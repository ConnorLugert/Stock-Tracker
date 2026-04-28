import streamlit as st
import yfinance as yf

st.title("Stock Price App")

ticker_symbol = st.text_input("Enter Ticker Symbol (e.g., AAPL, GOOGL):", "AAPL")

if ticker_symbol:
    period_map = {
        "1 Week": "5d",
        "1 Month": "1mo",
        "1 Year": "1y",
        "Year to Date": "ytd",
        "3 Years": "3y",
        "10 Years": "10y"
    }

    selected_period = st.selectbox("Select time range:", list(period_map.keys()))

    # Fetch data
    ticker_data = yf.Ticker(ticker_symbol)
    ticker_df = ticker_data.history(period=period_map[selected_period])
    
    # Calculate percentage change
    start_price = ticker_df.Close.iloc[0]
    end_price = ticker_df.Close.iloc[-1]
    pct_change = ((end_price - start_price) / start_price) * 100
    
# Calculate percentage change
    start_price = ticker_df.Close.iloc[0]
    end_price = ticker_df.Close.iloc[-1]
    
    # Calculate the dollar difference
    delta_value = end_price - start_price
    pct_change = (delta_value / start_price) * 100
    
    # Display price and metric
    # .upper() ensures the ticker is always CAPITALIZED
    st.write(f"### Closing Price for {ticker_symbol.upper()}")
    
    # Display the current price as the value, and the dollar difference as the delta
    st.metric(label=f"Price Change ({selected_period})", 
              value=f"${end_price:.2f}", 
              delta=f"${delta_value:.2f} ({pct_change:.2f}%)")
