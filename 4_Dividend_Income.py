import streamlit as st
import sys
import os

# Add parent directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import from portfolio_tracker.py
from portfolio_tracker import load_portfolio, save_portfolio

# Define portfolio path
PORTFOLIO_PATH = "/Users/abela/Desktop/Finance Project/FP - 1/portfolio.csv"


def calculate_dividend_income(portfolio):
    total_dividends = 0
    for ticker, details in portfolio.items():
        if ticker != "cash_balance":
            total_dividends += details["dividends"]
            print(f"{ticker}: Dividends = ${details['dividends']:.2f}")
    return total_dividends


# Load portfolio from CSV file
portfolio = load_portfolio(PORTFOLIO_PATH)

# Main logic
st.title("Dividend Income")
if not portfolio or len([k for k in portfolio.keys() if k != "cash_balance"]) == 0:
    st.error("No portfolio data available. Please add stocks on the Dashboard.")
else:
    total_dividends = calculate_dividend_income(portfolio)
    st.write(f"**Total Dividend Income:** ${total_dividends:.2f}")
    # Save portfolio only if it contains stocks
    if portfolio and len([k for k in portfolio.keys() if k != "cash_balance"]) > 0:
        save_portfolio(portfolio, PORTFOLIO_PATH)
