import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="Stock Tracker", layout="wide")
st.title("📊 Multi-Stock Comparison Pro")

# --- Optimized Data Fetching ---
@st.cache_data(ttl=3600)
def get_data(tickers, period):
    # Fetch benchmark (SPY) for Beta calculation
    all_tickers = list(set(tickers + ["SPY"]))
    data = yf.download(all_tickers, period=period, interval="1d")['Close']
    return data

def format_big_number(num):
    if not isinstance(num, (int, float)): return "N/A"
    if num >= 1e12: return f"${num/1e12:.2f}T"
    if num >= 1e9: return f"${num/1e9:.2f}B"
    if num >= 1e6: return f"${num/1e6:.2f}M"
    return f"${num:,.2f}"

# Sidebar / Inputs
ticker_input = st.text_input("Enter tickers separated by commas:", "AAPL, SCHD, VXUS, BND, GLD, VNQ, VWO").upper()
tickers = [t.strip() for t in ticker_input.split(",") if t.strip()]

period_map = {"1 Week": "5d", "1 Month": "1mo", "1 Year": "1y", "3 Years": "3y", "10 Years": "10y"}
selected_period = st.selectbox("Select time range:", list(period_map.keys()), index=2)

if tickers:
    df_prices = get_data(tickers, period_map[selected_period])
    
    # Separate benchmark from user tickers
    spy_prices = df_prices["SPY"]
    portfolio_prices = df_prices[[t for t in tickers if t in df_prices.columns]]
    
    valid_tickers = portfolio_prices.columns.tolist()
    fundamental_data = []

    # Calculate Returns for Beta/Sharpe
    returns = portfolio_prices.pct_change().dropna()
    spy_returns = spy_prices.pct_change().dropna()

    for ticker in valid_tickers:
        t_obj = yf.Ticker(ticker)
        info = t_obj.info
        
        # 1. Improved Dividend Logic
        # Try dividendYield (usually decimal), then yield (ETF decimal)
        div_yield = info.get('dividendYield') or info.get('yield')
        if div_yield is None:
            # Last ditch effort: calculate from rate / price
            rate = info.get('trailingAnnualDividendRate', 0)
            price = info.get('previousClose', 1)
            div_yield = rate / price if rate else 0
        
        # Ensure it's displayed as a % (e.g. 0.005 -> 0.50%)
        div_display = f"{div_yield * 100:.2f}%" if div_yield < 1 else f"{div_yield:.2f}%"

        # 2. Manual Beta Calculation (Ticker returns vs SPY returns)
        try:
            concat_df = pd.concat([returns[ticker], spy_returns], axis=1).dropna()
            covariance = concat_df.cov().iloc[0, 1]
            variance = spy_returns.var()
            beta_calc = covariance / variance
            beta_display = round(beta_calc, 2)
        except:
            beta_display = "N/A"

        # 3. Max Drawdown
        peaks = portfolio_prices[ticker].cummax()
        drawdowns = (portfolio_prices[ticker] - peaks) / peaks
        max_dd = drawdowns.min()

        fundamental_data.append({
            "Ticker": ticker,
            "Beta (vs SPY)": beta_display,
            "Max Drawdown": f"{max_dd:.2f}%",
            "Div. Yield": div_display,
            "Market Cap": format_big_number(info.get("marketCap")),
            "P/E Ratio": info.get("trailingPE", "N/A"),
            "Sector": info.get("sector", "ETF/Other")
        })

    # --- UI Layout ---
    st.subheader("Performance Metrics")
    m_cols = st.columns(len(valid_tickers))
    for idx, ticker in enumerate(valid_tickers):
        price_series = portfolio_prices[ticker]
        change = ((price_series.iloc[-1] - price_series.iloc[0]) / price_series.iloc[0]) * 100
        m_cols[idx].metric(ticker, f"${price_series.iloc[-1]:.2f}", f"{change:.2f}%")

    import plotly.express as px
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Relative Performance")
        norm = (portfolio_prices / portfolio_prices.iloc[0]) * 100
        st.line_chart(norm)
        
    with col2:
        st.subheader("Correlation Heatmap")
        corr = returns.corr()
        fig_corr = px.imshow(corr, text_auto=True, color_continuous_scale='RdBu_r', zmin=-1, zmax=1)
        st.plotly_chart(fig_corr, use_container_width=True)

    st.subheader("Fundamental Analysis & Risk")
    st.dataframe(pd.DataFrame(fundamental_data).set_index("Ticker"), use_container_width=True)
