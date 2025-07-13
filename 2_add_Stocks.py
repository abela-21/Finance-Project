import streamlit as st
import os
import sys
import pandas as pd
import yfinance as yf
import logging
from typing import Dict, Optional, List, Tuple, Union
from pathlib import Path
from config import PortfolioConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to Python path (using relative path)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from portfolio_tracker import load_portfolio, save_portfolio, validate_ticker

# Define the portfolio path relative to the script
portfolio_path = os.path.join(os.path.dirname(__file__), "..", "portfolio.csv")

st.title("Add Stocks to Portfolio")


# Function to get company name from ticker
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_company_info(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        if info and "longName" in info:
            return (
                info["longName"],
                info.get("sector", "Unknown"),
                info.get("industry", "Unknown"),
            )
        return None, None, None
    except Exception:
        return None, None, None


# Function to search for tickers
def search_tickers(query):
    # This is a simplified implementation
    # In a full version, you'd want to use a proper API for ticker search
    common_tickers = {
        "apple": "AAPL",
        "microsoft": "MSFT",
        "amazon": "AMZN",
        "google": "GOOGL",
        "facebook": "META",
        "tesla": "TSLA",
        "nvidia": "NVDA",
        "jp morgan": "JPM",
        "johnson": "JNJ",
        "visa": "V",
        "walmart": "WMT",
        "disney": "DIS",
        "netflix": "NFLX",
        "coca cola": "KO",
        "pepsi": "PEP",
        "nike": "NKE",
        "mcdonald": "MCD",
    }

    results = []
    query = query.lower()
    for company, ticker in common_tickers.items():
        if query in company or query in ticker.lower():
            name, sector, industry = get_company_info(ticker)
            results.append(
                {
                    "ticker": ticker,
                    "name": name or company.title(),
                    "sector": sector,
                    "industry": industry,
                }
            )
    return results


# Load portfolio data
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_portfolio_data(path):
    return load_portfolio(path)


# Initialize or load portfolio
if "portfolio" not in st.session_state:
    st.session_state.portfolio = load_portfolio_data(portfolio_path)

# Ticker search functionality
st.subheader("Stock Search")
search_query = st.text_input("Search for a company or ticker", "")
if search_query:
    results = search_tickers(search_query)
    if results:
        st.write(f"Found {len(results)} matching stocks:")
        result_df = pd.DataFrame(results)
        selected_ticker = st.selectbox(
            "Select a stock to add",
            options=result_df["ticker"].tolist(),
            format_func=lambda x: f"{x} - {result_df[result_df['ticker'] == x]['name'].iloc[0]}",
        )
    else:
        st.warning(
            "No matching stocks found. Try a different search term or enter the ticker directly."
        )
        selected_ticker = None
else:
    selected_ticker = None

# Manual ticker input with validation
st.subheader("Add Stock Manually")
with st.form("add_stock_form"):
    ticker_col, quantity_col = st.columns(2)

    with ticker_col:
        ticker = (
            st.text_input(
                "Stock Ticker (e.g., AAPL)",
                value=selected_ticker if selected_ticker else "",
                help="Enter the stock symbol exactly as it appears on exchanges",
            )
            .upper()
            .strip()
        )

    with quantity_col:
        quantity = st.number_input(
            "Quantity",
            min_value=0.01,
            value=1.0,
            step=0.01,
            help="Number of shares to add",
        )

    cost_col, allocation_col = st.columns(2)

    with allocation_col:
        target_allocation = (
            st.number_input(
                "Target Allocation (%)",
                min_value=0.0,
                max_value=100.0,
                value=5.0,
                step=0.1,
                help="Percentage of your portfolio you want allocated to this stock",
            )
            / 100
        )

    with cost_col:
        transaction_cost = st.number_input(
            "Transaction Cost ($)",
            min_value=0.0,
            value=5.0,
            step=0.01,
            help="Commission or fees paid for this transaction",
        )

    submitted = st.form_submit_button("Add Stock")

# Stock validation and addition logic
if submitted:
    if not ticker:
        st.error("Please enter a ticker symbol.")
    else:
        # Show a spinner while validating the ticker
        with st.spinner(f"Validating ticker {ticker}..."):
            valid = validate_ticker(ticker)

        if not valid:
            st.warning(
                f"Ticker {ticker} could not be validated. It may not exist or may be delisted."
            )
            proceed = st.button("Add Anyway")
            valid = proceed

        if valid:
            # Check target allocation
            current_total_allocation = sum(
                info["target_allocation"]
                for key, info in st.session_state.portfolio.items()
                if key != "cash_balance"
            )
            new_total_allocation = current_total_allocation + target_allocation

            # Warn if allocation exceeds 100%
            if new_total_allocation > 1.0:
                st.warning(
                    f"Adding {target_allocation * 100:.1f}% would exceed 100% total allocation. "
                    f"Your allocations will be automatically normalized."
                )
                scale_factor = 1.0 / new_total_allocation
                for key, info in st.session_state.portfolio.items():
                    if key != "cash_balance":
                        info["target_allocation"] *= scale_factor
                target_allocation *= scale_factor

            # Add or update the stock in portfolio
            if ticker in st.session_state.portfolio and ticker != "cash_balance":
                old_quantity = st.session_state.portfolio[ticker]["quantity"]
                st.session_state.portfolio[ticker]["quantity"] += quantity
                st.session_state.portfolio[ticker]["target_allocation"] = (
                    target_allocation
                )
                st.session_state.portfolio[ticker]["transaction_cost"] += (
                    transaction_cost
                )

                # Get company name
                company_name, _, _ = get_company_info(ticker)
                display_name = company_name if company_name else ticker

                st.success(
                    f"Updated {display_name} ({ticker}) in portfolio:\n"
                    f"- Quantity: {old_quantity:.2f} → {st.session_state.portfolio[ticker]['quantity']:.2f}\n"
                    f"- Target allocation: {target_allocation * 100:.1f}%"
                )
            else:
                # Get company name
                company_name, sector, industry = get_company_info(ticker)
                display_name = company_name if company_name else ticker

                st.session_state.portfolio[ticker] = {
                    "quantity": quantity,
                    "dividends": 0.0,
                    "transaction_cost": transaction_cost,
                    "target_allocation": target_allocation,
                    "valid_ticker": valid,
                    "sector": sector if sector else "Unknown",
                    "industry": industry if industry else "Unknown",
                }

                st.success(
                    f"Added {display_name} ({ticker}) to portfolio:\n"
                    f"- Quantity: {quantity:.2f}\n"
                    f"- Target allocation: {target_allocation * 100:.1f}%"
                )

            # Save to file
            save_portfolio(st.session_state.portfolio, portfolio_path)

            # Force refresh cache for other pages
            st.cache_data.clear()

            # Show reset button
            if st.button("Add Another Stock"):
                # This will trigger a page refresh
                st.experimental_rerun()

# Current Portfolio Summary
st.subheader("Current Portfolio")
if (
    st.session_state.portfolio
    and len([k for k in st.session_state.portfolio.keys() if k != "cash_balance"]) > 0
):
    # Create a cleaner display of portfolio
    portfolio_data = []
    for ticker, info in st.session_state.portfolio.items():
        if ticker != "cash_balance":
            company_name, _, _ = get_company_info(ticker)
            portfolio_data.append(
                {
                    "Ticker": ticker,
                    "Company": company_name if company_name else "Unknown",
                    "Quantity": f"{info['quantity']:.2f}",
                    "Target Allocation": f"{info['target_allocation'] * 100:.1f}%",
                }
            )

    # Display as a table
    st.dataframe(pd.DataFrame(portfolio_data), use_container_width=True)

    # Show cash balance
    st.info(f"Cash Balance: ${st.session_state.portfolio.get('cash_balance', 0.0):.2f}")
else:
    st.info("Your portfolio is empty. Add some stocks to get started!")

# Help information
with st.expander("Need Help?"):
    st.markdown("""
    ### How to Add Stocks to Your Portfolio
    
    1. **Search for a stock** by company name or ticker symbol, or enter a ticker directly
    2. **Enter the quantity** of shares you own or want to track
    3. **Set a target allocation** as a percentage of your total portfolio
    4. **Enter any transaction costs** associated with purchasing the stock
    5. Click **Add Stock** to add it to your portfolio
    
    ### Tips
    
    - Target allocations across your portfolio should add up to 100%
    - If your allocations exceed 100%, they will be automatically scaled down
    - Transaction costs are used to calculate your net portfolio value
    """)
