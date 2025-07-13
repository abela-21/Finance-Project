import streamlit as st
import sys
import os
import time
from datetime import datetime
from portfolio_tracker import (
    load_portfolio,
    calculate_risk_metrics,
    portfolio_volatility_plot,
)
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Define the portfolio file path
script_dir = os.path.dirname(os.path.abspath(__file__))
portfolio_path = os.path.join(script_dir, "..", "portfolio.csv")
# Initialize session state
if 'portfolio' not in st.session_state:
    portfolio_path = os.path.join(os.path.dirname(__file__), "..", "portfolio.csv")
    st.session_state.portfolio = load_portfolio(portfolio_path)
    st.session_state.last_update = datetime.now()

st.title("Risk Metrics")

# Get portfolio from session state
portfolio = st.session_state.portfolio

# Load portfolio with enhanced error handling
with st.spinner("Loading portfolio data..."):
    try:
        # Get only stock tickers (exclude cash_balance)
        stock_tickers = [ticker for ticker in portfolio.keys() if ticker not in ["cash_balance"]]
        if not stock_tickers:
            st.warning("Portfolio contains no stocks. Add stocks first.")
            st.stop()
    except Exception as e:
        st.error(f"Error loading portfolio: {str(e)}")
        st.info("Make sure the portfolio file exists and is properly formatted.")
        st.stop()

# Calculate and display risk metrics
with st.spinner("Calculating risk metrics..."):
    try:
        volatility, sharpe, beta, alpha, r_squared, var = calculate_risk_metrics(portfolio)
        
        # Display metrics with error handling
        st.subheader("Risk Metrics")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Volatility", f"{volatility:.2%}")
            st.metric("Sharpe Ratio", f"{sharpe:.2f}")
            st.metric("Alpha", f"{alpha:.2%}")
        
        with col2:
            st.metric("Beta", f"{beta:.2f}")
            st.metric("R-squared", f"{r_squared:.2%}")
            st.metric("Value at Risk (95%)", f"${var:.2f}")

        # Display Portfolio Volatility Plot
        st.subheader("Volatility Analysis")
        try:
            volatility_fig = portfolio_volatility_plot(portfolio)
            if volatility_fig:
                st.plotly_chart(volatility_fig, use_container_width=True)
            else:
                st.warning("Could not generate volatility plot")
        except Exception as e:
            st.error(f"Error generating volatility plot: {str(e)}")
            logger.error(f"Volatility plot error: {e}")
    
    except Exception as e:
        st.error(f"Error calculating risk metrics: {str(e)}")
        logger.error(f"Risk metrics calculation error: {e}")
        st.info("""
        Please check your portfolio data and ensure you have:
        1. Valid stock tickers
        2. Sufficient historical data (at least 6 months)
        3. Properly formatted portfolio file
        """)

# Add portfolio update button
if st.button("Update Portfolio"):
    portfolio_path = os.path.join(os.path.dirname(__file__), "..", "portfolio.csv")
    st.session_state.portfolio = load_portfolio(portfolio_path)
    st.session_state.last_update = datetime.now()
    st.experimental_rerun()

# Display last update time
st.markdown(f"**Last Updated:** {st.session_state.last_update.strftime('%Y-%m-%d %H:%M:%S')}")
