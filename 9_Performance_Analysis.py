import streamlit as st
import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import logging
import sys
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple, Union
from pathlib import Path
from config import PortfolioConfig
from portfolio_tracker import (
    load_portfolio,
    fetch_historical_data,
    calculate_portfolio_value,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Initialize session state at the top of the file
if 'portfolio' not in st.session_state:
    portfolio_path = os.path.join(os.path.dirname(__file__), "..", "portfolio.csv")
    st.session_state.portfolio = load_portfolio(portfolio_path)
    st.session_state.last_update = datetime.now()

st.title("Performance Analysis")

# Sidebar options
st.sidebar.header("Analysis Options")
period = st.sidebar.selectbox(
    "Time Period",
    ["1m", "3m", "6m", "1y", "3y", "5y"],
    index=3,
    help="Select the time period for analysis"
)

benchmark = st.sidebar.selectbox(
    "Benchmark Index",
    ["SPY", "QQQ", "DIA", "IWM"],
    help="Select a benchmark index for comparison"
)

# Get portfolio from session state
portfolio = st.session_state.portfolio

# Add portfolio update button
if st.sidebar.button("Update Portfolio"):
    portfolio_path = os.path.join(os.path.dirname(__file__), "..", "portfolio.csv")
    st.session_state.portfolio = load_portfolio(portfolio_path)
    st.session_state.last_update = datetime.now()
    st.rerun()

# Display last update time
st.sidebar.markdown(f"**Last Updated:** {st.session_state.last_update.strftime('%Y-%m-%d %H:%M:%S')}")

# Check portfolio contents
if not portfolio or len([k for k in portfolio.keys() if k != "cash_balance"]) == 0:
    st.warning("Portfolio is empty. Add stocks using the 'Add Stocks' tab.")
    st.stop()
else:
    # Fetch historical data
    with st.spinner("Loading historical data..."):
        try:
            historical_data = fetch_historical_data(portfolio, period=period)
            
            if historical_data.empty:
                st.warning("No historical data available for the selected period.")
                st.stop()
        except Exception as e:
            st.error(f"Error fetching historical data: {str(e)}")
            st.stop()

    # Validate and prepare data
    try:
        # Get only valid stock tickers (exclude cash_balance and invalid tickers)
        valid_tickers = [ticker for ticker, info in portfolio.items() 
                        if ticker != "cash_balance" and info.get("valid_ticker", False)]
        
        if not valid_tickers:
            st.warning("No valid tickers found in portfolio. Please ensure all tickers are valid.")
            st.stop()

        # Filter historical data to only include valid stocks
        returns = historical_data[valid_tickers].pct_change()
        
        # Remove any remaining NaN values
        returns = returns.dropna()
        
        if returns.empty:
            st.warning("No valid return data available for analysis.")
            st.stop()

        cumulative_returns = (1 + returns).cumprod() - 1
        
        # Calculate performance metrics
        try:
            total_return = cumulative_returns.iloc[-1].mean()
            annualized_return = (1 + total_return) ** (252 / len(returns)) - 1
            volatility = returns.std() * np.sqrt(252)
            sharpe_ratio = annualized_return / volatility
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {str(e)}")
            st.error(f"Error calculating performance metrics: {str(e)}")
            st.stop()

        # Display metrics
        try:
            st.header("Performance Metrics")
            col1, col2, col3, col4 = st.columns(4)

            col1.metric(
                "Total Return",
                f"{total_return:.2%}",
                help="Return over the selected period"
            )

            col2.metric(
                "Annualized Return",
                f"{annualized_return:.2%}",
                help="Annualized return based on daily returns"
            )

            col3.metric(
                "Volatility",
                f"{volatility:.2%}",
                help="Annualized volatility of returns"
            )

            col4.metric(
                "Sharpe Ratio",
                f"{sharpe_ratio:.2f}",
                help="Risk-adjusted return"
            )
        except Exception as e:
            logger.error(f"Error displaying metrics: {str(e)}")
            st.error(f"Error displaying metrics: {str(e)}")
            st.stop()

        # Plot cumulative returns
        try:
            st.header("Cumulative Returns")
            fig = go.Figure()
            for column in cumulative_returns.columns:
                fig.add_trace(
                    go.Scatter(
                        x=cumulative_returns.index,
                        y=cumulative_returns[column],
                        name=column,
                        mode='lines'
                    )
                )

            fig.update_layout(
                title="Cumulative Returns",
                yaxis_title="Cumulative Return",
                xaxis_title="Date",
                legend_title="Assets",
                height=500
            )
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            logger.error(f"Error creating cumulative returns plot: {str(e)}")
            st.error(f"Error creating cumulative returns plot: {str(e)}")
            st.stop()

        # Correlation matrix
        try:
            st.header("Correlation Matrix")
            correlation_matrix = returns.corr()
            fig = px.imshow(
                correlation_matrix,
                labels=dict(x="Assets", y="Assets", color="Correlation"),
                x=correlation_matrix.columns,
                y=correlation_matrix.columns,
                color_continuous_scale='RdBu_r'
            )
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            logger.error(f"Error creating correlation matrix: {str(e)}")
            st.error(f"Error creating correlation matrix: {str(e)}")
            st.stop()

        # Drawdown analysis
        try:
            st.header("Drawdown Analysis")
            drawdowns = (cumulative_returns - cumulative_returns.cummax())
            max_drawdown = drawdowns.min()

            st.metric(
                "Maximum Drawdown",
                f"{max_drawdown.min():.2%}",
                help="Largest peak-to-trough decline"
            )

            # Plot drawdowns
            fig = go.Figure()
            for column in drawdowns.columns:
                fig.add_trace(
                    go.Scatter(
                        x=drawdowns.index,
                        y=drawdowns[column],
                        name=column,
                        mode='lines'
                    )
                )

            fig.update_layout(
                title="Drawdown Analysis",
                yaxis_title="Drawdown",
                xaxis_title="Date",
                legend_title="Assets",
                height=500
            )
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            logger.error(f"Error creating drawdown analysis: {str(e)}")
            st.error(f"Error creating drawdown analysis: {str(e)}")
            st.stop()
    except Exception as e:
        logger.error(f"Error in performance analysis: {str(e)}")
        st.error(f"Error in performance analysis: {str(e)}")
        st.stop()
