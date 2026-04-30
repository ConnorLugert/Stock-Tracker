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
ma_window = st.number_input("Moving Average Window (days):", min_value=1, max_value=365, value=50)

if tickers:
    data_dict = {}
    ma_dict = {}
    valid_tickers = []
    fundamental_data = []

    for ticker in tickers:
        t = yf.Ticker(ticker)
        df = t.history(period=period_map[selected_period])
        
        if not df.empty:
            data_dict[ticker] = df.Close
            ma_dict[f"{ticker} MA"] = df.Close.rolling(window=ma_window).mean()
            valid_tickers.append(ticker)
            
            # Extract fundamental info
            info = t.info
            fundamental_data.append({
                "Ticker": ticker,
                "Market Cap": info.get("marketCap", "N/A"),
                "P/E Ratio": info.get("trailingPE", "N/A"),
                "52W High": info.get("fiftyTwoWeekHigh", "N/A"),
                "Forward EPS": info.get("forwardEps", "N/A")
            })

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
    
# 2. Charts
# 2. Charts
if data_dict:
    import plotly.express as px
    
    # --- Existing Price History Chart ---
    st.subheader("Price History")
    df_prices = pd.DataFrame(data_dict)
    fig1 = px.line(df_prices)
    fig1.update_layout(dragmode=False)
    st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False})

    # --- NEW: Normalized Comparison Chart ---
    st.subheader("Relative Performance (%)")
    # Divide every row by the first row and multiply by 100
    normalized_df = (df_prices / df_prices.iloc[0]) * 100
    
    fig_norm = px.line(normalized_df, labels={"value": "Normalized Price (Base 100)", "Date": "Date"})
    fig_norm.update_layout(dragmode=False)
    st.plotly_chart(fig_norm, use_container_width=True, config={'displayModeBar': False})
        # 3. Fundamental Table
        st.subheader("Fundamental Data")
        st.table(pd.DataFrame(fundamental_data).set_index("Ticker"))
    else:
        st.error("No data found for the entered tickers.")
