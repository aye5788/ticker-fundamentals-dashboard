import streamlit as st
import requests
import pandas as pd

# Read API key from secrets
API_KEY = st.secrets["fmp"]["api_key"]
BASE_URL = "https://financialmodelingprep.com/api/v3"

# Streamlit UI
st.set_page_config(page_title="Fundamentals Dashboard", layout="wide")
st.title("📊 Fundamentals Dashboard")

ticker = st.text_input("Enter Stock Ticker (e.g., AAPL):", value="AAPL").upper()

if not ticker:
    st.warning("Please enter a stock ticker.")
    st.stop()

# Function to call API
def fetch_data(endpoint):
    url = f"{BASE_URL}/{endpoint}?apikey={API_KEY}"
    res = requests.get(url)
    if res.status_code == 200:
        return res.json()
    return []

# ------------------------------------------
# Section 1: YoY Revenue and Net Income Growth
# ------------------------------------------
st.subheader("📉 YoY Growth (Revenue & Net Income)")
income_data = fetch_data(f"income-statement/{ticker}?limit=10")

if income_data:
    df_income = pd.DataFrame(income_data).sort_values("date")
    df_income["Revenue YoY %"] = df_income["revenue"].pct_change() * 100
    df_income["Net Income YoY %"] = df_income["netIncome"].pct_change() * 100

    df_yoy = df_income[["date", "Revenue YoY %", "Net Income YoY %"]].set_index("date").T
    st.dataframe(df_yoy)
else:
    st.warning("No income statement data available.")

# ------------------------------------------
# Section 2: EPS, Free Cash Flow, Dividend Yield
# ------------------------------------------
st.subheader("💰 Earnings & Cash Flow")
profile_data = fetch_data(f"profile/{ticker}")
quote_data = fetch_data(f"quote/{ticker}")
cashflow_data = fetch_data(f"cash-flow-statement/{ticker}?limit=1")

eps = profile_data[0].get("eps", "N/A") if profile_data else "N/A"
div_yield = profile_data[0].get("lastDiv", "N/A") if profile_data else "N/A"
fcf = cashflow_data[0].get("freeCashFlow", "N/A") if cashflow_data else "N/A"

earnings_df = pd.DataFrame({
    "Metric": ["EPS (TTM)", "Free Cash Flow (TTM)", "Dividend Yield"],
    "Value": [eps, fcf, div_yield]
})
st.dataframe(earnings_df)

# ------------------------------------------
# Section 3: Sector P/E Comparison
# ------------------------------------------
st.subheader("💡 Sector P/E Comparison")
sector_pe_data = fetch_data("stock/sectors-performance")
sector_mapping = fetch_data(f"profile/{ticker}")

sector_name = sector_mapping[0].get("sector", "") if sector_mapping else ""
pe_data = fetch_data("stock/sectors-peg-ratios")

sector_pe_value = None
for sector in pe_data:
    if sector["sector"].lower() == sector_name.lower():
        sector_pe_value = sector.get("peRatio", None)
        break

if sector_pe_value:
    st.write(f"**Sector ({sector_name}) Avg P/E**: {sector_pe_value:.2f}")
else:
    st.warning(f"No sector P/E found for {sector_name or 'this ticker'}.")

# ------------------------------------------
# Section 4: Key Ratios
# ------------------------------------------
st.subheader("📌 Key Ratios (TTM)")
ratios_data = fetch_data(f"ratios-ttm/{ticker}")

pe_ratio = ratios_data[0].get("peRatioTTM", "N/A") if ratios_data else "N/A"
peg_ratio = ratios_data[0].get("pegRatioTTM", "N/A") if ratios_data else "N/A"
roe = ratios_data[0].get("returnOnEquityTTM", "N/A") if ratios_data else "N/A"
current_ratio = ratios_data[0].get("currentRatioTTM", "N/A") if ratios_data else "N/A"
debt_equity = ratios_data[0].get("debtEquityRatioTTM", "N/A") if ratios_data else "N/A"

ratios_df = pd.DataFrame({
    "Metric": ["PE Ratio (TTM)", "PEG Ratio", "ROE", "Current Ratio", "Debt/Equity"],
    "Value": [pe_ratio, peg_ratio, roe, current_ratio, debt_equity]
})
st.dataframe(ratios_df)

# ------------------------------------------
# Section 5: Profitability & Valuation
# ------------------------------------------
st.subheader("📌 Profitability & Valuation Metrics")
pb_ratio = ratios_data[0].get("priceToBookRatioTTM", "N/A") if ratios_data else "N/A"
roa = ratios_data[0].get("returnOnAssetsTTM", "N/A") if ratios_data else "N/A"
gross_margin = ratios_data[0].get("grossProfitMarginTTM", "N/A") if ratios_data else "N/A"
op_margin = ratios_data[0].get("operatingProfitMarginTTM", "N/A") if ratios_data else "N/A"
net_margin = ratios_data[0].get("netProfitMarginTTM", "N/A") if ratios_data else "N/A"
interest_coverage = ratios_data[0].get("interestCoverageTTM", "N/A") if ratios_data else "N/A"

profit_df = pd.DataFrame({
    "Metric": ["P/B Ratio", "ROA", "Gross Margin", "Operating Margin", "Net Margin", "Interest Coverage"],
    "Value": [pb_ratio, roa, gross_margin, op_margin, net_margin, interest_coverage]
})
st.dataframe(profit_df)
