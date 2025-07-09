import streamlit as st
import requests
import pandas as pd

# Load API key from Streamlit secrets
api_key = st.secrets["fmp"]["api_key"]

# Utility functions for FMP endpoints
def get_json(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except:
        return None

# Load Ticker Input
st.set_page_config(page_title="Fundamentals Dashboard")
st.title("📊 Fundamentals Dashboard")
ticker = st.text_input("Enter Stock Ticker (e.g., AAPL):", value="AAPL")

if ticker:
    # --- Income Statement for YoY Growth ---
    income_url = f"https://financialmodelingprep.com/api/v3/income-statement/{ticker}?limit=10&apikey={api_key}"
    income_data = get_json(income_url)
    if income_data:
        income_df = pd.DataFrame(income_data)
        income_df["date"] = pd.to_datetime(income_df["date"])
        income_df = income_df.sort_values("date")
        income_df["Revenue YoY %"] = income_df["revenue"].pct_change() * 100
        income_df["Net Income YoY %"] = income_df["netIncome"].pct_change() * 100
        yoy_df = income_df[["date", "Revenue YoY %", "Net Income YoY %"]].dropna().copy()

        st.subheader("📈 YoY Growth (Revenue & Net Income)")
        st.dataframe(yoy_df.set_index("date").T.style.format("{:.2f}%"))
    else:
        st.warning("No income statement data found.")

    # --- Earnings & Cash Flow ---
    st.subheader("💰 Earnings & Cash Flow")
    eps_url = f"https://financialmodelingprep.com/api/v3/ratios-ttm/{ticker}?apikey={api_key}"
    eps_data = get_json(eps_url)
    eps_val = eps_data[0].get("epsTTM") if eps_data else None

    quote_url = f"https://financialmodelingprep.com/api/v3/quote/{ticker}?apikey={api_key}"
    quote_data = get_json(quote_url)
    div_yield = quote_data[0].get("dividendYield") if quote_data else None

    earnings_table = pd.DataFrame({
        "Metric": ["EPS (TTM)", "Free Cash Flow (TTM)", "Dividend Yield"],
        "Value": [
            round(eps_val, 2) if eps_val else "N/A",
            "N/A",  # Free cash flow TTM not directly available
            f"{div_yield*100:.2f}%" if div_yield else "N/A"
        ]
    })
    st.table(earnings_table)

    # --- Sector P/E Comparison ---
    st.subheader("💡 Sector P/E Comparison")
    profile_url = f"https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={api_key}"
    profile_data = get_json(profile_url)
    sector = profile_data[0].get("sector") if profile_data else None

    if sector:
        sector_url = f"https://financialmodelingprep.com/api/v4/sector_pe_ratio?apikey={api_key}"
        sector_data = get_json(sector_url)
        if sector_data and sector in sector_data:
            pe_sector = sector_data[sector]["pe"]
            st.info(f"Sector P/E (for {sector}): {round(pe_sector, 2)}")
        else:
            st.warning(f"No sector P/E found for {sector}")
    else:
        st.warning("Unable to retrieve sector information.")

    # --- Key Ratios ---
    st.subheader("📌 Key Ratios (TTM)")
    if eps_data:
        ttm_table = pd.DataFrame({
            "Metric": [
                "PE Ratio (TTM)", "PEG Ratio", "ROE", "Current Ratio", "Debt/Equity"
            ],
            "Value": [
                eps_data[0].get("peRatioTTM", "N/A"),
                eps_data[0].get("pegRatioTTM", "N/A"),
                eps_data[0].get("returnOnEquityTTM", "N/A"),
                eps_data[0].get("currentRatioTTM", "N/A"),
                eps_data[0].get("debtEquityRatioTTM", "N/A")
            ]
        })
        st.dataframe(ttm_table)

    # --- Profitability & Valuation Metrics ---
    st.subheader("📌 Profitability & Valuation Metrics")
    if eps_data:
        prof_table = pd.DataFrame({
            "Metric": ["P/B Ratio", "ROA", "Gross Margin", "Operating Margin", "Net Margin", "Interest Coverage"],
            "Value": [
                eps_data[0].get("priceToBookRatioTTM", "N/A"),
                eps_data[0].get("returnOnAssetsTTM", "N/A"),
                eps_data[0].get("grossProfitMarginTTM", "N/A"),
                eps_data[0].get("operatingProfitMarginTTM", "N/A"),
                eps_data[0].get("netProfitMarginTTM", "N/A"),
                eps_data[0].get("interestCoverageTTM", "N/A")
            ]
        })
        st.dataframe(prof_table)

st.markdown("""
    <br>
    <div style='text-align:center; font-size: small;'>
        Data via Financial Modeling Prep — <a href="https://financialmodelingprep.com">https://financialmodelingprep.com</a>
    </div>
""", unsafe_allow_html=True)

