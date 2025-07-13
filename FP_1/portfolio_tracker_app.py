import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path
import logging
from .config import PortfolioConfig
from .portfolio_tracker import (
    load_portfolio,
    calculate_portfolio_value,
    calculate_dividend_income,
    calculate_risk_metrics,
    plot_portfolio_allocation,
    plot_historical_performance,
    portfolio_volatility_plot,
    calculate_transaction_costs
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize configuration
config = PortfolioConfig.from_env()

# Set up page
st.set_page_config(
    page_title="Portfolio Tracker",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to",
    ["Dashboard", "Portfolio Management", "Performance Analysis", "Risk Analysis"]
)

# Main content
st.title("Portfolio Tracker")

try:
    portfolio = load_portfolio(config.portfolio_file)
    
    if page == "Dashboard":
        st.header("Portfolio Dashboard")
        
        # Portfolio summary
        col1, col2, col3 = st.columns(3)
        with col1:
            total_value, net_value = calculate_portfolio_value(portfolio, {})
            st.metric("Total Value", f"${total_value:,.2f}", "")
        with col2:
            dividends = calculate_dividend_income(portfolio)
            st.metric("Dividend Income", f"${dividends:,.2f}", "")
        with col3:
            transaction_costs = calculate_transaction_costs(portfolio)
            st.metric("Transaction Costs", f"${transaction_costs:,.2f}", "")
            
        # Portfolio allocation chart
        st.header("Portfolio Allocation")
        fig = plot_portfolio_allocation(portfolio, {})
        st.plotly_chart(fig, use_container_width=True)
        
    elif page == "Portfolio Management":
        st.header("Portfolio Management")
        # Add portfolio management features here
        
    elif page == "Performance Analysis":
        st.header("Performance Analysis")
        # Add performance analysis features here
        
    elif page == "Risk Analysis":
        st.header("Risk Analysis")
        risk_metrics = calculate_risk_metrics(portfolio)
        st.dataframe(pd.DataFrame([risk_metrics]))
        
except Exception as e:
    logger.error(f"Error in app: {str(e)}", exc_info=True)
    st.error(f"An error occurred: {str(e)}")
