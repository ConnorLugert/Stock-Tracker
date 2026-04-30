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
                sharpe = (excess_returns.mean() / excess_returns.std()) * np.sqrt(252) if excess_returns.std() != 0 else 0
            else:
                sharpe = 0

            # Extract info
            info = t.info
            fundamental_data.append({
                "Ticker": ticker,
                "Sharpe Ratio": round(sharpe, 2),
                "Sector": info.get("sector", "ETF/Other"),
                "Market Cap": info.get("marketCap", "N/A"),
                "P/E Ratio": info.get("trailingPE", "N/A"),
                "Div. Yield (%)": f"{info.get('dividendYield', 0) * 100:.2f}%" if info.get('dividendYield') else "0.00%",
            })

    # 1. Metrics
    cols_per_row = 4
    for i in range(0, len(valid_tickers), cols_per_row):
        ticker_chunk = valid_tickers[i : i + cols_per_row]
        cols = st.columns(cols_per_row)
        for j, ticker in enumerate(ticker_chunk):
            ticker_series = data_dict[ticker]
            start, end = ticker_series.iloc[0], ticker_series.iloc[-1]
            delta = end - start
            pct = (delta / start) * 100
            with cols[j]:
                st.metric(f"{ticker}", f"${end:.2f}", f"${delta:.2f} ({pct:.2f}%)")

    # 2. Charts
    if data_dict:
        import plotly.express as px
        df_prices = pd.DataFrame(data_dict)

        st.subheader("Relative Performance (%)")
        normalized_df = (df_prices / df_prices.iloc[0]) * 100
        fig_norm = px.line(normalized_df, labels={"value": "Normalized Price (Base 100)", "Date": "Date"})
        fig_norm.update_layout(dragmode=False, hovermode="x unified")
        st.plotly_chart(fig_norm, use_container_width=True)

        st.subheader("Portfolio Diversification")
        fund_df = pd.DataFrame(fundamental_data)
        sector_counts = fund_df['Sector'].value_counts().reset_index()
        sector_counts.columns = ['Sector', 'Count']
        fig_pie = px.pie(sector_counts, values='Count', names='Sector', hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)

        st.subheader("Price History")
        fig1 = px.line(df_prices, labels={"value": "Price ($)", "Date": "Date"})
        fig1.update_layout(dragmode=False, hovermode="x unified")
        st.plotly_chart(fig1, use_container_width=True)

        # 3. Fundamental Table
        st.subheader("Fundamental Data & Risk Metrics")
        st.table(fund_df.set_index("Ticker"))
else:
    st.error("No data found for the entered tickers.")
