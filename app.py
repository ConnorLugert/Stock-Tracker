import streamlit as st
import yfinance as yf

st.title("Stock Comparison App")

# Layout: Two input columns
col1, col2 = st.columns(2)
ticker1 = col1.text_input("Ticker 1:", "AAPL").upper()
ticker2 = col2.text_input("Ticker 2:", "MSFT").upper()

period_map = {
    "1 Week": "5d", "1 Month": "1mo", "1 Year": "1y", 
    "Year to Date": "ytd", "3 Years": "3y", "10 Years": "10y"
}
selected_period = st.selectbox("Select time range:", list(period_map.keys()))

if ticker1 and ticker2:
    def get_stock_data(symbol, period):
        data = yf.Ticker(symbol).history(period=period)
        return data

    df1 = get_stock_data(ticker1, period_map[selected_period])
    df2 = get_stock_data(ticker2, period_map[selected_period])

    # Display Metrics Side-by-Side
    m1, m2 = st.columns(2)
    for i, (df, ticker, col) in enumerate([(df1, ticker1, m1), (df2, ticker2, m2)]):
        start = df.Close.iloc[0]
        end = df.Close.iloc[-1]
        delta = end - start
        pct = (delta / start) * 100
        col.metric(f"{ticker} Change", f"${end:.2f}", f"${delta:.2f} ({pct:.2f}%)")

    # Combine data for the chart
    import pandas as pd
    combined_df = pd.DataFrame({ticker1: df1.Close, ticker2: df2.Close})
    
    st.line_chart(combined_df)
