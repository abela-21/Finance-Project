import streamlit as st
import pandas as pd
import os
import sys
import plotly.graph_objects as go
from datetime import datetime, timedelta
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
    fetch_historical_data,
)

# Initialize session state
if 'portfolio' not in st.session_state:
    portfolio_path = os.path.join(os.path.dirname(__file__), "..", "portfolio.csv")
    st.session_state.portfolio = load_portfolio(portfolio_path)
    st.session_state.last_update = datetime.now()

st.title("Portfolio Value")

# Add sidebar options
st.sidebar.header("View Options")
view_period = st.sidebar.selectbox(
    "Performance Period",
    ["1m", "3m", "6m", "YTD", "1y", "3y", "5y"],
    index=4,
    help="Select time period for historical performance",
)

show_sector = st.sidebar.checkbox("Show Sector Breakdown", value=True)
refresh_data = st.sidebar.button("Refresh Data")

# Get portfolio from session state
portfolio = st.session_state.portfolio

# Load portfolio with spinner and proper error handling
with st.spinner("Loading portfolio data..."):
    try:
        if refresh_data:
            portfolio_path = os.path.join(os.path.dirname(__file__), "..", "portfolio.csv")
            st.session_state.portfolio = load_portfolio(portfolio_path)
            st.session_state.last_update = datetime.now()
            portfolio = st.session_state.portfolio
            st.experimental_rerun()
    except Exception as e:
        st.error(f"Error loading portfolio: {str(e)}")
        portfolio = {"cash_balance": 0.0}

# Check if portfolio is empty
if not portfolio or len([k for k in portfolio.keys() if k != "cash_balance"]) == 0:
    st.warning("Portfolio is empty. Add stocks using the 'Add Stocks' tab.")
else:
    # Fetch latest stock data with spinner
    with st.spinner("Fetching latest market data..."):
        tickers = [ticker for ticker in portfolio.keys() if ticker != "cash_balance"]
        prices = fetch_stock_data(tickers)

    # Calculate portfolio values
    try:
        total_value, net_value = calculate_portfolio_value(portfolio, prices)
        cash_balance = portfolio.get("cash_balance", 0.0)

        # Portfolio value metrics
        col1, col2, col3 = st.columns(3)
        col1.metric(
            "Total Value (Gross)",
            f"${total_value:.2f}",
            help="Total value of all assets including cash",
        )
        col2.metric(
            "Total Value (Net)",
            f"${net_value:.2f}",
            help="Portfolio value minus transaction costs",
        )
        col3.metric(
            "Cash Balance",
            f"${cash_balance:.2f}",
            help="Available cash for new investments",
        )

        # Create detailed portfolio table
        st.subheader("Portfolio Holdings")

        # Prepare data for display
        data = []
        sector_values = {}

        for ticker, info in portfolio.items():
            if ticker != "cash_balance":
                current_price = prices.get(ticker)
                if current_price is not None and current_price != "N/A":
                    value = info["quantity"] * current_price
                    percentage = (value / total_value) * 100 if total_value > 0 else 0
                else:
                    value = 0
                    percentage = 0

                # Track sector allocation
                sector = info.get("sector", "Unknown")
                if sector not in sector_values:
                    sector_values[sector] = 0
                sector_values[sector] += value

                data.append(
                    {
                        "Ticker": ticker,
                        "Quantity": f"{info['quantity']:.2f}",
                        "Current Price": f"${current_price:.2f}"
                        if current_price != "N/A"
                        else "N/A",
                        "Value": f"${value:.2f}",
                        "% of Portfolio": f"{percentage:.2f}%",
                        "Target Allocation": f"{info['target_allocation'] * 100:.2f}%",
                        "Sector": sector,
                    }
                )

        # Add cash to data
        cash_percentage = (cash_balance / total_value) * 100 if total_value > 0 else 0
        data.append(
            {
                "Ticker": "CASH",
                "Quantity": "N/A",
                "Current Price": "N/A",
                "Value": f"${cash_balance:.2f}",
                "% of Portfolio": f"{cash_percentage:.2f}%",
                "Target Allocation": "N/A",
                "Sector": "Cash",
            }
        )

        # Also track cash in sector values
        sector_values["Cash"] = cash_balance

        # Display as a DataFrame
        df = pd.DataFrame(data)
        st.dataframe(
            df.style.highlight_max(subset=["% of Portfolio"], color="lightgreen"),
            use_container_width=True,
        )

        # Historical Performance Section
        st.subheader("Historical Performance")

        with st.spinner("Loading historical data..."):
            historical_data = fetch_historical_data(portfolio, period=view_period)

            if (
                not historical_data.empty
                and "Portfolio_Value" in historical_data.columns
            ):
                # Calculate performance metrics
                start_value = historical_data["Portfolio_Value"].iloc[0]
                end_value = historical_data["Portfolio_Value"].iloc[-1]
                percent_change = (
                    ((end_value / start_value) - 1) * 100 if start_value > 0 else 0
                )

                # Show performance metrics
                st.metric(
                    f"Performance ({view_period})",
                    f"{percent_change:.2f}%",
                    delta=f"${end_value - start_value:.2f}",
                )

                # Create interactive chart
                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        x=historical_data.index,
                        y=historical_data["Portfolio_Value"],
                        mode="lines",
                        name="Portfolio Value",
                        line=dict(color="rgb(49, 130, 189)", width=2),
                    )
                )

                fig.update_layout(
                    title=f"Portfolio Value Over Time ({view_period})",
                    xaxis_title="Date",
                    yaxis_title="Value ($)",
                    hovermode="x unified",
                    height=400,
                    template="plotly_white",
                )

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(
                    "Not enough historical data available to display performance chart."
                )

        # Sector Allocation Section
        if show_sector:
            st.subheader("Sector Allocation")

            # Create sector allocation chart
            sector_fig = go.Figure(
                data=[
                    go.Pie(
                        labels=list(sector_values.keys()),
                        values=list(sector_values.values()),
                        hole=0.3,
                        textinfo="label+percent",
                        insidetextorientation="radial",
                    )
                ]
            )

            sector_fig.update_layout(title_text="Portfolio by Sector", height=500)

            st.plotly_chart(sector_fig, use_container_width=True)

            # Sector allocation table
            sector_data = []
            for sector, value in sector_values.items():
                percentage = (value / total_value) * 100 if total_value > 0 else 0
                sector_data.append(
                    {
                        "Sector": sector,
                        "Value": f"${value:.2f}",
                        "% of Portfolio": f"{percentage:.2f}%",
                    }
                )

            st.dataframe(pd.DataFrame(sector_data), use_container_width=True)

    except Exception as e:
        st.error(f"Error analyzing portfolio: {str(e)}")

# Footer with last update timestamp
st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
if refresh_data:
    st.success("Data refreshed successfully!")
