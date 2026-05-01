import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="Stock Tracker", layout="wide")
st.title("Multi-Stock Comparison")

# --- Function to fetch Risk-Free Rate (3-Month T-Bill) ---
def get_risk_free_rate():
    try:
        t_bill = yf.Ticker("^IRX")
        current_yield = t_bill.history(period="1d")['Close'].iloc[-1]
        return current_yield / 100
    except:
        return 0.04

# --- Helper for Market Cap Formatting ---
def format_market_cap(val):
    if val == "N/A" or not isinstance(val, (int, float)): return "N/A"
    if val >= 1e12: return f"${val/1e12:.2f}T"
    if val >= 1e9: return f"${val/1e9:.2f}B"
    return f"${val/1e6:.2f}M"

rf_rate = get_risk_free_rate()

# Sidebar / Inputs
ticker_input = st.text_input("Enter tickers separated by commas:", "AAPL, TGT, BAC, PFE, WMT, VZ, TSLA, LMT").upper()
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
    st.info(f"**Risk-Free Rate:** {rf_rate*100:.2f}%\n\n(Based on 3-Month Treasury Bills)")

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
            
            # --- FIXED: Robust Dividend Yield Logic ---
            # Calculates yield manually: (Dividend Rate / Current Price)
            current_price = info.get('previousClose') or info.get('regularMarketPrice') or 1
            div_rate = info.get('trailingAnnualDividendRate') or info.get('dividendRate') or 0
            
            # Use manual calc if it's a common stock, or fallback to yield if manual is 0
            manual_yield = (div_rate / current_price) * 100
            info_yield = (info.get('dividendYield') or info.get('yield') or 0)
            
            # Logic to handle if info_yield is already a percentage (like 3.5) vs decimal (0.035)
            if info_yield < 1 and info_yield > 0:
                info_yield = info_yield * 100
                
            final_yield = manual_yield if manual_yield > 0 else info_yield

            # --- Beta Metric ---
            beta = info.get("beta")
            beta_display = f"{beta:.2f}" if isinstance(beta, (int, float)) else "N/A"

            fundamental_data.append({
                "Ticker": ticker,
                "Sharpe Ratio": round(sharpe, 2),
                "Beta": beta_display,
                "Sector": info.get("sector", "ETF/Other"),
                "Market Cap": format_market_cap(info.get("marketCap")),
                "P/E Ratio": round(info.get("trailingPE", 0), 2) if info.get("trailingPE") else "N/A",
                "Div. Yield (%)": f"{final_yield:.2f}%"
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
        
        # --- Correlation Matrix ---
        st.subheader("Correlation Matrix (Daily Returns)")
        returns_df = df_prices.pct_change().dropna()
        corr_matrix = returns_df.corr().round(2)
        fig_corr = px.imshow(
            corr_matrix, 
            text_auto=True, 
            aspect="auto", 
            color_continuous_scale="RdBu_r",
            labels=dict(color="Correlation"),
            zmin=-1, zmax=1
        )
        st.plotly_chart(fig_corr, use_container_width=True)

        # 3. Fundamental Table
        st.subheader("Fundamental Data & Risk Metrics")
        st.table(fund_df.set_index("Ticker"))

else:
    st.error("No data found for the entered tickers.")
