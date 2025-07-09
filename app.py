import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import date

st.set_page_config(layout="wide")
FMP_API_KEY = st.secrets["fmp_api_key"]

# User input
ticker = st.text_input("Enter stock ticker", value="AAPL").upper()

@st.cache_data
def get_company_profile(ticker):
    url = f"https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={FMP_API_KEY}"
    return requests.get(url).json()[0]

@st.cache_data
def get_income_statement(ticker, period="annual"):
    url = f"https://financialmodelingprep.com/api/v3/income-statement/{ticker}?period={period}&apikey={FMP_API_KEY}"
    return requests.get(url).json()

@st.cache_data
def get_key_metrics(ticker):
    url = f"https://financialmodelingprep.com/api/v3/key-metrics-ttm/{ticker}?apikey={FMP_API_KEY}"
    return requests.get(url).json()[0]

@st.cache_data
def get_ratios_ttm(ticker):
    url = f"https://financialmodelingprep.com/api/v3/ratios-ttm/{ticker}?apikey={FMP_API_KEY}"
    return requests.get(url).json()[0]

@st.cache_data
def get_sector_pe_snapshot():
    url = f"https://financialmodelingprep.com/api/v3/sector_price_earning_ratio?apikey={FMP_API_KEY}"
    return requests.get(url).json()

# Load data
profile = get_company_profile(ticker)
income_annual = get_income_statement(ticker, "annual")
income_quarterly = get_income_statement(ticker, "quarter")
metrics = get_key_metrics(ticker)
ratios = get_ratios_ttm(ticker)
sector_pe_data = get_sector_pe_snapshot()

# Header
st.title(f"{profile['companyName']} ({ticker}) Fundamentals")

# Revenue & Net Income chart
st.subheader("Revenue & Net Income")
interval = st.radio("Select time interval", ("Annual", "Quarterly"))
income = income_annual if interval == "Annual" else income_quarterly
df = pd.DataFrame(income)
df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date")

fig = px.bar(df, x="date", y=["revenue", "netIncome"], barmode="group", labels={"value": "USD", "date": "Date", "variable": "Metric"})
st.plotly_chart(fig, use_container_width=True)

# YoY Growth
st.subheader("📊 YoY Growth (Revenue & Net Income)")
df["Revenue YoY %"] = df["revenue"].pct_change().mul(100).round(2)
df["Net Income YoY %"] = df["netIncome"].pct_change().mul(100).round(2)
growth_df = df[["date", "Revenue YoY %", "Net Income YoY %"]].copy()
growth_df["date"] = pd.to_datetime(growth_df["date"]).dt.year
st.dataframe(growth_df.set_index("date").T.style.format("{:.2f}%"))

# Earnings & Cash Flow
st.subheader("🧾 Earnings & Cash Flow")
earnings_data = {
    "EPS (TTM)": metrics.get("epsTTM", "N/A"),
    "Free Cash Flow (TTM)": metrics.get("freeCashFlowTTM", "N/A"),
    "Dividend Yield": metrics.get("dividendYieldTTM", "N/A")
}
st.table(pd.DataFrame(earnings_data.items(), columns=["", "Value"]))

# Sector P/E comparison
st.subheader("💡 Sector P/E Comparison")
sector = profile.get("sector")
sector_pe = next((s for s in sector_pe_data if s.get("sector") == sector), None)

if sector_pe:
    st.success(f"Sector: {sector} — P/E Ratio: {sector_pe.get('pe'):.2f}")
else:
    st.info(f"No sector P/E found for {sector}")

# Key Ratios
st.subheader("Key Ratios (TTM)")
key_ratio_data = {
    "PE Ratio (TTM)": metrics.get("peRatioTTM", "N/A"),
    "PEG Ratio": metrics.get("pegRatioTTM", "N/A"),
    "ROE": metrics.get("roeTTM", "N/A"),
    "Current Ratio": metrics.get("currentRatioTTM", "N/A"),
    "Debt/Equity": metrics.get("debtEquityRatioTTM", "N/A"),
}
st.table(pd.DataFrame(key_ratio_data.items(), columns=["", "Value"]))

# Profitability
st.subheader("Profitability & Valuation Metrics")
prof_data = {
    "P/B Ratio": metrics.get("pbRatioTTM", "N/A"),
    "ROA": metrics.get("roaTTM", "N/A"),
    "Gross Margin": ratios.get("grossProfitMarginTTM", "N/A"),
    "Operating Margin": ratios.get("operatingProfitMarginTTM", "N/A"),
    "Net Margin": ratios.get("netProfitMarginTTM", "N/A"),
    "Interest Coverage": ratios.get("interestCoverageTTM", "N/A"),
}
st.table(pd.DataFrame(prof_data.items(), columns=["", "Value"]))

