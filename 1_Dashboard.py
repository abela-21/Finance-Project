import streamlit as st
import pandas as pd
import sys
import os
import time
from datetime import datetime
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
from portfolio_tracker import (
    load_portfolio,
    fetch_stock_data,
    calculate_portfolio_value,
    calculate_risk_metrics,
    calculate_rebalancing,
    plot_portfolio_allocation,
    plot_rebalancing,
    fetch_historical_data,
)

# Set page title and layout
st.set_page_config(page_title="Portfolio Dashboard", layout="wide")

# Initialize session state
if 'portfolio' not in st.session_state:
    portfolio_path = os.path.join(os.path.dirname(__file__), "..", "portfolio.csv")
    st.session_state.portfolio = load_portfolio(portfolio_path)
    st.session_state.last_update = datetime.now()

# Portfolio file upload section
st.sidebar.header("Portfolio Management")
uploaded_file = st.sidebar.file_uploader(
    "Upload Portfolio CSV",
    type=["csv"],
    help="Upload your portfolio CSV file. The file should contain columns: Ticker, Quantity, Dividends, TransactionCost, TargetAllocation, ValidTicker, CashBalance"
)

if uploaded_file is not None:
    try:
        # Save uploaded file to portfolio path
        portfolio_path = os.path.join(os.path.dirname(__file__), "..", "portfolio.csv")
        with open(portfolio_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.session_state.portfolio = load_portfolio(portfolio_path)
        st.session_state.last_update = datetime.now()
        st.sidebar.success("Portfolio file uploaded successfully!")
        st.experimental_rerun()
    except Exception as e:
        st.sidebar.error(f"Error saving portfolio file: {str(e)}")

# Create sidebar for options
st.sidebar.header("Dashboard Options")
refresh_data = st.sidebar.button("Refresh Data")
benchmark = st.sidebar.selectbox(
    "Benchmark Index",
    ["SPY", "QQQ", "DIA", "IWM"],
    help="Select an index to compare your portfolio against",
)
time_period = st.sidebar.selectbox(
    "Time Period",
    ["1m", "3m", "6m", "1y", "YTD", "3y", "5y"],
    index=3,
    help="Select time period for performance comparison",
)

# Get portfolio from session state
portfolio = st.session_state.portfolio

# Load portfolio data with spinner
with st.spinner("Loading portfolio data..."):
    try:
        cash_balance = portfolio.get("cash_balance", 0.0)
        tickers = [ticker for ticker in portfolio.keys() if ticker != "cash_balance"]
    except Exception as e:
        st.error(f"Error loading portfolio: {str(e)}")
        portfolio = {"cash_balance": 0.0}
        tickers = []
        cash_balance = 0.0

# Fetch stock data with spinner
with st.spinner("Fetching latest market data..."):
    try:
        prices = fetch_stock_data(tickers)
    except Exception as e:
        st.error(f"Error fetching market data: {str(e)}")
        prices = {}

# Check if portfolio is empty
if not portfolio or len([k for k in portfolio.keys() if k != "cash_balance"]) == 0:
    st.warning(
        "No portfolio data available. Please add stocks using the 'Add Stocks' tab."
    )
    st.info(
        "If you already have a portfolio file, use the 'Upload Portfolio' tab to import it."
    )
else:
    # Section 1: Portfolio Summary
    st.header("Portfolio Summary")

    # Create columns for key metrics
    col1, col2, col3 = st.columns(3)

    # Calculate portfolio values
    try:
        gross_value, net_value = calculate_portfolio_value(portfolio, prices)

        # Display key metrics
        col1.metric(
            "Portfolio Value",
            f"${gross_value:.2f}",
            help="Total value of all assets including cash",
        )
        col2.metric(
            "Net Value",
            f"${net_value:.2f}",
            help="Portfolio value minus transaction costs",
        )
        col3.metric(
            "Cash Balance",
            f"${cash_balance:.2f}",
            help="Available cash for new investments",
        )
    except Exception as e:
        st.error(f"Error calculating portfolio value: {str(e)}")

    # Section 2: Portfolio Performance
    st.header("Portfolio Performance")

    # Fetch historical data for performance chart
    with st.spinner("Loading historical performance data..."):
        try:
            historical_data = fetch_historical_data(portfolio, period=time_period)
            # Create interactive performance chart (placeholder for now)
            if (
                not historical_data.empty
                and "Portfolio_Value" in historical_data.columns
            ):
                # Simple chart for now - enhance in full implementation
                st.line_chart(historical_data["Portfolio_Value"])
            else:
                st.info("Not enough historical data to display performance chart.")
        except Exception as e:
            st.error(f"Error loading historical data: {str(e)}")

    # Section 3: Risk Metrics
    st.header("Risk Metrics")
    with st.spinner("Calculating risk metrics..."):
        try:
            volatility, sharpe_ratio, beta, alpha, r_squared, var_95 = (
                calculate_risk_metrics(portfolio)
            )
            if volatility is not None:
                # Create columns for metrics
                col1, col2, col3 = st.columns(3)
                col1.metric("Volatility", f"{volatility:.2f}")
                col2.metric("Sharpe Ratio", f"{sharpe_ratio:.2f}")
                col3.metric("Beta", f"{beta:.2f}")

                col1, col2, col3 = st.columns(3)
                col1.metric("Alpha", f"{alpha:.2f}")
                col2.metric("R-squared", f"{r_squared:.2f}")
                col3.metric("VaR (95%)", f"${var_95:.2f}")

                # Add risk metrics tooltips
                st.info("""
                    **Risk Metrics Explained:**
                    - **Volatility:** Annualized standard deviation of returns
                    - **Sharpe Ratio:** Risk-adjusted return (higher is better)
                    - **Beta:** Portfolio's sensitivity to market movements
                    - **Alpha:** Excess return compared to benchmark
                    - **R-squared:** Correlation with benchmark
                    - **VaR (95%):** Maximum expected daily loss with 95% confidence
                """)
            else:
                st.warning(
                    "Unable to calculate risk metrics due to insufficient historical data."
                )
        except Exception as e:
            st.error(f"Error calculating risk metrics: {str(e)}")

    # Section 4: Portfolio Allocation
    st.header("Portfolio Allocation")
    with st.spinner("Generating allocation visualization..."):
        try:
            fig_allocation = plot_portfolio_allocation(portfolio, prices)
            st.plotly_chart(
                fig_allocation,
                use_container_width=True,
                key="portfolio_allocation_chart",
            )
        except Exception as e:
            st.error(f"Error generating allocation chart: {str(e)}")

    # Section 5: Rebalancing Recommendations
    st.header("Rebalancing Recommendations")
    with st.spinner("Calculating rebalancing suggestions..."):
        try:
            # Ensure minimum cash balance
            portfolio["cash_balance"] = max(portfolio.get("cash_balance", 0.0), 100.0)
            rebalancing_actions, total_transaction_costs = calculate_rebalancing(
                portfolio, prices
            )

            if not rebalancing_actions:
                st.success(
                    "No rebalancing actions needed. Your portfolio is well-balanced."
                )
            else:
                st.warning(
                    "Your portfolio could benefit from rebalancing. Here are the suggested actions:"
                )

                # Create dataframe for recommendations
                recommendations = []
                for ticker, actions in rebalancing_actions.items():
                    if actions["buy"] > 0:
                        recommendations.append(
                            {
                                "Action": "Buy",
                                "Shares": f"{actions['buy']:.2f}",
                                "Ticker": ticker,
                            }
                        )
                    if actions["sell"] > 0:
                        recommendations.append(
                            {
                                "Action": "Sell",
                                "Shares": f"{actions['sell']:.2f}",
                                "Ticker": ticker,
                            }
                        )

                # Show recommendations as a table
                st.dataframe(pd.DataFrame(recommendations))

                # Show rebalancing chart
                fig_rebalancing = plot_rebalancing(rebalancing_actions)
                st.plotly_chart(
                    fig_rebalancing, use_container_width=True, key="rebalancing_chart"
                )

                # Show cost summary
                available_cash = portfolio.get("cash_balance", 0.0)
                st.info(
                    f"Remaining Cash Balance After Rebalancing: ${available_cash:.2f}"
                )
                st.info(
                    f"Total Transaction Costs Incurred: ${total_transaction_costs:.2f}"
                )

                # Add call to action
                st.write(
                    "Visit the 'Rebalance' tab for more detailed information and to execute these trades."
                )
        except Exception as e:
            st.error(f"Error calculating rebalancing recommendations: {str(e)}")

    # Footer with last update timestamp
    st.markdown("---")
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if refresh_data:
        st.success("Data refreshed successfully!")
