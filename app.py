import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Stock Tracker", layout="wide")
st.title("📊 Multi-Stock Comparison Pro")

# --- 1. Functions for Data & Rates ---

@st.cache_data(ttl=3600)
def fetch_all_data(ticker_list, period):
    data = yf.download(ticker_list, period=period)['Close']
    return data

def get_risk_free_rate():
    try:
        # ^IRX is the 13-week Treasury Bill yield
        t_bill = yf.Ticker("^IRX")
        current_yield = t_bill.history(period="1d")['Close'].iloc[-1]
        return current_yield / 100
    except:
        return 0.04  # Fallback to 4% if API fails

def format_big_number(num):
    if not isinstance(num, (int, float)): return "N/A"
    if num >= 1e12: return f"${num/1e12:.2f}T"
    if num >= 1e9: return f"${num/1e9:.2f}B"
    return f"${num/1e6:.2f}M"

# --- 2. Sidebar & Inputs ---

ticker_input = st.text_input("Enter tickers:", "AAPL, TGT, BAC, PFE, WMT, VZ, TSLA, LMT").upper()
tickers = [t.strip() for t in ticker_input.split(",") if t.strip()]

period_map = {"1 Week": "5d", "1 Month": "1mo", "1 Year": "1y", "3 Years": "3y", "10 Years": "10y"}
selected_period = st.selectbox("Select time range:", list(period_map.keys()), index=2)

rf_rate = get_risk_free_rate()

if tickers:
    df_prices = fetch_all_data(tickers, period_map[selected_period])
    
    if not df_prices.empty:
        tab1, tab2, tab3 = st.tabs(["📈 Performance", "🎯 Risk & Correlation", "📋 Fundamentals"])

        with tab1:
            st.subheader("Relative Performance (%)")
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
                returns = df_prices.pct_change().dropna()
                corr = returns.corr().round(2)
                fig_corr = px.imshow(corr, text_auto=True, color_continuous_scale="RdBu_r", zmin=-1, zmax=1)
                st.plotly_chart(fig_corr, use_container_width=True)
            with col_b:
                st.metric("3-Month T-Bill (Risk-Free Rate)", f"{rf_rate*100:.2f}%")
                st.info("**Sharpe Ratio:** Measures return per unit of risk. Higher is better. It uses the T-Bill rate above as the benchmark.")

        with tab3:
            st.subheader("Comprehensive Fundamentals")
            fundamental_list = []
            
            with st.spinner('Analyzing Company Data...'):
                for ticker in tickers:
                    try:
                        t_obj = yf.Ticker(ticker)
                        info = t_obj.info
                        
                        # --- Sharpe Ratio Calculation ---
                        ticker_returns = df_prices[ticker].pct_change().dropna()
                        if not ticker_returns.empty:
                            daily_rf = (1 + rf_rate)**(1/252) - 1
                            excess_returns = ticker_returns - daily_rf
                            sharpe = (excess_returns.mean() / excess_returns.std()) * np.sqrt(252)
                        else:
                            sharpe = 0

                        # --- Robust Dividend ---
                        price = info.get('previousClose') or info.get('regularMarketPrice') or 1
                        div_cash = info.get('trailingAnnualDividendRate') or info.get('dividendRate') or 0
                        div_yield = (div_cash / price) * 100 if div_cash > 0 else 0

                        fundamental_list.append({
                            "Ticker": ticker,
                            "Sector": info.get("sector", "N/A"),
                            "Market Cap": format_big_number(info.get("marketCap")),
                            "P/E Ratio": round(info.get("trailingPE", 0), 2) if info.get("trailingPE") else "N/A",
                            "Beta": round(info.get("beta", 0), 2) if info.get("beta") else "N/A",
                            "Sharpe Ratio": round(sharpe, 2),
                            "Div. Yield": f"{div_yield:.2f}%",
                            "Profit Margin": f"{(info.get('profitMargins', 0) or 0)*100:.2f}%",
                            "52W High": f"${info.get('fiftyTwoWeekHigh', 0):.2f}"
                        })
                    except Exception:
                        st.warning(f"Skipping {ticker} - data unavailable.")

            st.table(pd.DataFrame(fundamental_list).set_index("Ticker"))

else:
    st.info("Please enter stock tickers above to begin.")
