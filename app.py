import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Fundamentals Dashboard", layout="wide")
st.title("📊 Fundamentals Dashboard")

# Load API key
api_key = st.secrets["fmp"]["api_key"]

# Ticker input
ticker = st.text_input("Enter Stock Ticker (e.g., AAPL):", value="AAPL").upper()

@st.cache_data(ttl=3600)
def fetch_data(url):
    response = requests.get(url)
    if response.ok:
        return response.json()
    return None

# === Fetch endpoints ===
income_data = fetch_data(f"https://financialmodelingprep.com/api/v3/income-statement/{ticker}?limit=10&apikey={api_key}")
cashflow_ttm = fetch_data(f"https://financialmodelingprep.com/api/v3/cash-flow-statement-ttm/{ticker}?apikey={api_key}")
profile = fetch_data(f"https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={api_key}")
ratios = fetch_data(f"https://financialmodelingprep.com/api/v3/ratios-ttm/{ticker}?apikey={api_key}")
key_metrics = fetch_data(f"https://financialmodelingprep.com/api/v3/key-metrics-ttm/{ticker}?apikey={api_key}")

# === Revenue & Net Income YoY Growth ===
st.markdown("### 📈 YoY Growth (Revenue & Net Income)")
if income_data:
    df_income = pd.DataFrame(income_data)
    df_yoy = pd.DataFrame({
        "Date": df_income["date"],
        "Revenue YoY %": df_income["revenueGrowth"] * 100,
        "Net Income YoY %": df_income["netIncomeRatio"] * 100,
    }).set_index("Date").T
    st.dataframe(df_yoy)
else:
    st.warning("No income statement data found.")

# === Earnings & Cash Flow ===
st.markdown("### 💰 Earnings & Cash Flow")
eps = key_metrics[0].get("epsTTM") if key_metrics else "N/A"
fcf = cashflow_ttm.get("freeCashFlowTTM") if cashflow_ttm else "N/A"
div_yield = "N/A"
if profile:
    try:
        div_yield = round((float(profile[0]["lastDiv"]) / float(profile[0]["price"])) * 100, 2)
        div_yield = f"{div_yield}%"
    except:
        pass

st.table(pd.DataFrame({
    "Metric": ["EPS (TTM)", "Free Cash Flow (TTM)", "Dividend Yield"],
    "Value": [eps, fcf, div_yield]
}))

# === Sector P/E ===
st.markdown("### 💡 Sector P/E Comparison")
sector = profile[0].get("sector") if profile else None
sector_pe = "N/A"
if sector:
    # Normally you’d need a mapping for sector-level P/E — FMP doesn’t expose direct sector PE in a stable endpoint.
    st.info(f"No sector P/E found for {sector}.")
else:
    st.warning("Unable to retrieve sector information.")

# === Key Ratios (TTM) ===
st.markdown("### 📌 Key Ratios (TTM)")
if ratios:
    ratio = ratios[0]
    st.table(pd.DataFrame({
        "Metric": ["PE Ratio (TTM)", "PEG Ratio", "ROE", "Current Ratio", "Debt/Equity"],
        "Value": [
            ratio.get("priceEarningsRatioTTM", "N/A"),
            ratio.get("pegRatioTTM", "N/A"),
            ratio.get("returnOnEquityTTM", "N/A"),
            ratio.get("currentRatioTTM", "N/A"),
            ratio.get("debtEquityRatioTTM", "N/A")
        ]
    }))
else:
    st.warning("Key ratios not found.")

# === Profitability & Valuation Metrics ===
st.markdown("### 📌 Profitability & Valuation Metrics")
if ratios:
    st.table(pd.DataFrame({
        "Metric": ["P/B Ratio", "ROA", "Gross Margin", "Operating Margin", "Net Margin", "Interest Coverage"],
        "Value": [
            ratios[0].get("priceToBookRatioTTM", "N/A"),
            ratios[0].get("returnOnAssetsTTM", "N/A"),
            ratios[0].get("grossProfitMarginTTM", "N/A"),
            ratios[0].get("operatingProfitMarginTTM", "N/A"),
            ratios[0].get("netProfitMarginTTM", "N/A"),
            ratios[0].get("interestCoverageTTM", "N/A")
        ]
    }))
else:
    st.warning("Profitability metrics unavailable.")

st.caption("Data via Financial Modeling Prep — https://financialmodelingprep.com")

