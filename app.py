import streamlit as st
import requests
import pandas as pd

API_KEY = st.secrets["FMP_API_KEY"]
BASE_URL = "https://financialmodelingprep.com/api/v3"

st.set_page_config(page_title="Fundamentals Dashboard", layout="wide")
st.title("📊 Fundamentals Dashboard")

ticker = st.text_input("Enter Stock Ticker (e.g., AAPL):", "AAPL").upper()

# Helper to fetch data from FMP
def fetch_fmp_data(endpoint):
    url = f"{BASE_URL}/{endpoint}?apikey={API_KEY}"
    res = requests.get(url)
    if res.status_code == 200:
        return res.json()
    return None

# ------------------ YoY Growth ------------------
st.subheader("📉 YoY Growth (Revenue & Net Income)")
income_data = fetch_fmp_data(f"income-statement/{ticker}?limit=10")

if income_data and isinstance(income_data, list):
    df_income = pd.DataFrame(income_data)
    if 'date' in df_income.columns and 'revenueGrowth' in df_income.columns and 'netIncomeRatio' in df_income.columns:
        df_yoy = pd.DataFrame({
            "Date": df_income["date"],
            "Revenue YoY %": df_income["revenueGrowth"] * 100,
            "Net Income YoY %": df_income["netIncomeRatio"] * 100
        }).set_index("Date").T
        st.dataframe(df_yoy)
    else:
        st.warning("No income statement data available.")
else:
    st.warning("No income statement data available.")

# ------------------ Earnings & Cash Flow ------------------
st.subheader("💰 Earnings & Cash Flow")
profile = fetch_fmp_data(f"profile/{ticker}")
ratios = fetch_fmp_data(f"ratios-ttm/{ticker}")

eps = ratios[0].get("epsTTM") if ratios else "N/A"
fcf = ratios[0].get("freeCashFlowTTM") if ratios else "N/A"
div_yield = profile[0].get("lastDiv") if profile else "N/A"

earnings_df = pd.DataFrame({
    "Metric": ["EPS (TTM)", "Free Cash Flow (TTM)", "Dividend Yield"],
    "Value": [eps, fcf, div_yield]
})
earnings_df["Value"] = earnings_df["Value"].astype(str)
st.dataframe(earnings_df)

# ------------------ Sector P/E Comparison ------------------
st.subheader("💡 Sector P/E Comparison")
sector_pe_data = fetch_fmp_data("stock/sectors-performance-pe-ratios")

if sector_pe_data and isinstance(sector_pe_data, list):
    company_sector = profile[0].get("sector") if profile else None
    sector_match = next((item for item in sector_pe_data if item["sector"] == company_sector), None)

    if sector_match:
        st.metric(f"{company_sector} Sector Avg P/E", round(sector_match["peRatio"], 2))
    else:
        st.warning(f"No sector P/E found for {company_sector or 'this ticker'}.")
else:
    st.warning("Unable to retrieve sector information.")

# ------------------ Key Ratios (TTM) ------------------
st.subheader("📌 Key Ratios (TTM)")
pe_ratio = ratios[0].get("peRatioTTM") if ratios else "N/A"
peg_ratio = ratios[0].get("pegRatioTTM") if ratios else "N/A"
roe = ratios[0].get("returnOnEquityTTM") if ratios else "N/A"
current_ratio = ratios[0].get("currentRatioTTM") if ratios else "N/A"
de_ratio = ratios[0].get("debtEquityRatioTTM") if ratios else "N/A"

ratios_df = pd.DataFrame({
    "Metric": ["PE Ratio (TTM)", "PEG Ratio", "ROE", "Current Ratio", "Debt/Equity"],
    "Value": [pe_ratio, peg_ratio, roe, current_ratio, de_ratio]
})
ratios_df["Value"] = ratios_df["Value"].astype(str)
st.dataframe(ratios_df)

# ------------------ Footer ------------------
st.markdown("#### Profitability & Valuation Metrics")
st.markdown("Data via [Financial Modeling Prep](https://financialmodelingprep.com)")
