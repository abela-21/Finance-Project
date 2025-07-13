import streamlit as st
from portfolio_tracker import load_portfolio, summarize_transaction_costs

# Define the portfolio file path
portfolio_path = "/Users/abela/Desktop/Finance Project/FP - 1/portfolio.csv"

st.title("Transaction Costs")

portfolio = load_portfolio(portfolio_path)
if not portfolio:
    st.warning("Portfolio is empty. Add stocks first.")
else:
    total_transaction_costs = summarize_transaction_costs(portfolio)
    st.write(f"**Total Transaction Costs:** ${total_transaction_costs:.2f}")
