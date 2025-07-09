import streamlit as st
import pandas as pd
import requests
import altair as alt
from datetime import datetime

# Title
st.set_page_config(layout="wide")
st.title("📊 Fundamentals Dashboard")

# Input
symbol = st.text_input("Enter Stock Ticker (e.g., AAPL):", "AAPL").upper()
api_key = st.secrets["fmp"]["api_key"]

# Helper function to fetch from FMP API
def fetch_data(endpoint):
    url = f"https://financialmodelingprep.com/api/v3/{endpoint}?apikey={api_key}"
    response = requests.get(url)
    return response.json() if response.status_code == 200 else {}

# --- Revenue & Net Income YoY ---
st.subheader("📈 YoY Growth (Revenue & Net Income)")
income_data = fetch_data(f"income-statement/{symbol}?limit=12&datatype=json")

if income_data:
    df_income = pd.DataFrame(income_data)
    df_income["date"] = pd.to_datetime(df_income["date"])
    df_income = df_income.sort_values("date")

    df_income["Revenue YoY %"] = df_income["revenue"].pct_change() * 100
    df_income["Net Income YoY %"] = df_income["netIncome"].pct_change() * 100
    yoy_df = df_income[["date", "Revenue YoY %", "Net Income YoY %"]].dropna()
    yoy_df["Year"] = yoy_df["date"].dt.year

    yoy_pivot = yoy_df.pivot_table(index="Year", values=["Revenue YoY %", "Net Income YoY %"])
    st.dataframe(yoy_pivot.style.format("{:.2f}%"), use_container_width=True)
else:
    st.warning("No income statement data found.")

# --- Earnings & Cash Flow Metrics ---
st.subheader("🧾 Earnings & Cash Flow")
quote_data = fetch_data(f"quote/{symbol}")
fcf_data = fetch_data(f"cash-flow-statement/{symbol}?limit=1")
dividend_data = fetch_data(f"profile/{symbol}")

try:
    eps = quote_data[0].get("eps")
except: eps = "N/A"
try:
    fcf = fcf_data[0].get("freeCashFlow")
except: fcf = "N/A"
try:
    dividend_yield = dividend_data[0].get("lastDiv") / quote_data[0].get("price")
except: dividend_yield = "N/A"

st.dataframe(pd.DataFrame({
    "Metric": ["EPS (TTM)", "Free Cash Flow (TTM)", "Dividend Yield"],
    "Value": [eps, fcf, f"{dividend_yield:.2%}" if isinstance(dividend_yield, float) else "N/A"]
}))

# --- Sector P/E Comparison ---
st.subheader("💡 Sector P/E Comparison")
profile = fetch_data(f"profile/{symbol}")
sector = profile[0].get("sector") if profile else None
sector_pe_data = fetch_data("sector_price_earning_ratio")

if sector and sector_pe_data:
    match = next((item for item in sector_pe_data if item["sector"] == sector), None)
    if match:
        sector_pe = match["pe"]
        st.markdown(f"**Sector:** {sector}  |  **P/E:** {sector_pe:.2f}")
    else:
        st.info(f"No sector P/E found for {sector}")
else:
    st.warning("Unable to retrieve sector information.")

# --- Valuation Metrics ---
st.subheader("📌 Key Ratios (TTM)")
ratios_ttm = fetch_data(f"ratios-ttm/{symbol}")

if ratios_ttm:
    ttm_df = pd.DataFrame(ratios_ttm)
    ttm_metrics = [
        "peRatioTTM", "pegRatioTTM", "returnOnEquityTTM", "currentRatioTTM", "debtEquityRatioTTM"
    ]
    ttm_labels = [
        "PE Ratio (TTM)", "PEG Ratio", "ROE", "Current Ratio", "Debt/Equity"
    ]
    values = [ttm_df[col].iloc[0] if col in ttm_df else "N/A" for col in ttm_metrics]
    st.dataframe(pd.DataFrame({"Metric": ttm_labels, "Value": values}))

# --- Profitability & Valuation ---
st.subheader("📌 Profitability & Valuation Metrics")
ratios_data = fetch_data(f"ratios/{symbol}?limit=1")

if ratios_data:
    data = ratios_data[0]
    metrics = [
        ("P/B Ratio", data.get("priceToBookRatio")),
        ("ROA", data.get("returnOnAssets")),
        ("Gross Margin", data.get("grossProfitMargin")),
        ("Operating Margin", data.get("operatingProfitMargin")),
        ("Net Margin", data.get("netProfitMargin")),
        ("Interest Coverage", data.get("interestCoverage"))
    ]
    df_ratios = pd.DataFrame(metrics, columns=["Metric", "Value"])
    st.dataframe(df_ratios)

st.markdown("""
    <br><sub>Data via Financial Modeling Prep — [https://financialmodelingprep.com](https://financialmodelingprep.com)</sub>
""", unsafe_allow_html=True)


