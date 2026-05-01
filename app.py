import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Stock Tracker", layout="wide")
st.title("📊 Multi-Stock Comparison Pro")

# 1. Caching data for speed
@st.cache_data(ttl=3600)
def fetch_all_data(ticker_list, period):
    # Fetching all at once is much faster
    data = yf.download(ticker_list, period=period)['Close']
    return data

# Sidebar / Inputs
ticker_input = st.text_input("Enter tickers:", "AAPL, TGT, BAC, PFE, WMT, VZ, TSLA, LMT").upper()
tickers = [t.strip() for t in ticker_input.split(",") if t.strip()]

period_map = {"1 Week": "5d", "1 Month": "1mo", "1 Year": "1y", "3 Years": "3y", "10 Years": "10y"}
selected_period = st.selectbox("Select time range:", list(period_map.keys()), index=2)

if tickers:
    df_prices = fetch_all_data(tickers, period_map[selected_period])
    
    if not df_prices.empty:
        # Create Tabs for a cleaner UI
        tab1, tab2, tab3 = st.tabs(["📈 Performance", "🎯 Risk & Correlation", "📋 Fundamentals"])

        with tab1:
            st.subheader("Relative Performance (%)")
            # Normalize to 100 to show growth comparison
            norm_df = (df_prices / df_prices.iloc[0]) * 100
            fig_norm = px.line(norm_df, labels={"value": "Normalized Growth", "Date": ""})
            fig_norm.update_layout(hovermode="x unified")
            st.plotly_chart(fig_norm, use_container_width=True)
            
            st.subheader("Price History ($)")
            fig_price = px.line(df_prices, labels={"value": "Price ($)", "Date": ""})
            fig_price.update_layout(hovermode="x unified")
            st.plotly_chart(fig_price, use_container_width=True)

        with tab2:
            col_a, col_b = st.columns([2, 1])
            with col_a:
                st.subheader("Correlation Heatmap")
                # Calculate correlation of daily percentage changes
                corr = df_prices.pct_change().corr().round(2)
                fig_corr = px.imshow(
                    corr, 
                    text_auto=True, 
                    color_continuous_scale="RdBu_r", 
                    zmin=-1, zmax=1
                )
                st.plotly_chart(fig_corr, use_container_width=True)
            with col_b:
                st.markdown("### 💡 Risk Tip")
                st.info("Values close to **1.0** mean the stocks move in lockstep. Values closer to **0** or negative mean they provide better diversification for your portfolio.")

        with tab3:
            st.subheader("Company Fundamentals")
            fundamental_list = []
            
            # Use a spinner because fetching individual 'info' can be slow
            with st.spinner('Fetching fundamental data...'):
                for ticker in tickers:
                    try:
                        t_obj = yf.Ticker(ticker)
                        info = t_obj.info
                        
                        # --- ROBUST DIVIDEND CALCULATION ---
                        # We take the actual $ amount and divide by current price to avoid the 38% bug
                        price = info.get('previousClose') or info.get('regularMarketPrice') or 1
                        div_cash = info.get('trailingAnnualDividendRate') or info.get('dividendRate') or 0
                        
                        if div_cash > 0:
                            actual_yield = (div_cash / price) * 100
                            div_display = f"{actual_yield:.2f}%"
                        else:
                            div_display = "0.00%"

                        # --- FORMATTING NUMBERS ---
                        pe = info.get("trailingPE")
                        pe_display = round(pe, 2) if pe else "N/A"
                        
                        beta = info.get("beta")
                        beta_display = round(beta, 2) if beta else "N/A"

                        fundamental_list.append({
                            "Ticker": ticker,
                            "Sector": info.get("sector", "N/A"),
                            "P/E Ratio": pe_display,
                            "Beta": beta_display,
                            "Div. Yield": div_display
                        })
                    except Exception as e:
                        st.warning(f"Could not fetch info for {ticker}")

            # Display as a clean table
            df_fundamentals = pd.DataFrame(fundamental_list).set_index("Ticker")
            st.table(df_fundamentals)

else:
    st.info("Please enter stock tickers above to begin.")
