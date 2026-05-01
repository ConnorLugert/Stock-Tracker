import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Stock Tracker", layout="wide")
st.title("📊 Multi-Stock Comparison Pro")

# 1. Caching data saves time and prevents Yahoo Finance rate limiting
@st.cache_data(ttl=3600)
def fetch_all_data(ticker_list, period):
    data = yf.download(ticker_list, period=period)['Close']
    return data

# Sidebar / Inputs
ticker_input = st.text_input("Enter tickers:", "AAPL, TGT, BAC, PFE, WMT, VZ, TSLA, LMT").upper()
tickers = [t.strip() for t in ticker_input.split(",") if t.strip()]

period_map = {"1 Week": "5d", "1 Month": "1mo", "1 Year": "1y", "3 Years": "3y", "10 Years": "10y"}
selected_period = st.selectbox("Select time range:", list(period_map.keys()), index=2)

if tickers:
    # Batch download prices for speed
    df_prices = fetch_all_data(tickers, period_map[selected_period])
    
    if not df_prices.empty:
        # Create Tabs for a cleaner UI
        tab1, tab2, tab3 = st.tabs(["📈 Performance", "🎯 Risk & Correlation", "📋 Fundamentals"])

        with tab1:
            st.subheader("Relative Performance (%)")
            norm_df = (df_prices / df_prices.iloc[0]) * 100
            fig_norm = px.line(norm_df, labels={"value": "Normalized Price", "Date": ""})
            st.plotly_chart(fig_norm, use_container_width=True)
            
            st.subheader("Price History ($)")
            fig_price = px.line(df_prices, labels={"value": "Price ($)", "Date": ""})
            st.plotly_chart(fig_price, use_container_width=True)

        with tab2:
            col_a, col_b = st.columns([1, 1])
            with col_a:
                st.subheader("Correlation Heatmap")
                corr = df_prices.pct_change().corr().round(2)
                fig_corr = px.imshow(corr, text_auto=True, color_continuous_scale="RdBu_r", zmin=-1, zmax=1)
                st.plotly_chart(fig_corr, use_container_width=True)
            with col_b:
                # Add a brief explanation of what they are seeing
                st.info("**How to read this:** Blue (1.0) means stocks move together. Red (-1.0) means they move in opposite directions. Diversified portfolios look for values closer to 0.")

        with tab3:
            # Build the fundamental table with rounded numbers
            fundamental_list = []
            for ticker in tickers:
                info = yf.Ticker(ticker).info
                fundamental_list.append({
                    "Ticker": ticker,
                    "Sector": info.get("sector", "N/A"),
                    "P/E Ratio": round(info.get("trailingPE", 0), 2) if info.get("trailingPE") else "N/A",
                    "Beta": round(info.get("beta", 0), 2) if info.get("beta") else "N/A",
                    "Div. Yield": f"{ (info.get('dividendYield', 0) or 0) * 100 :.2f}%"
                })
            st.table(pd.DataFrame(fundamental_list).set_index("Ticker"))
