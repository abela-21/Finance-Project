import streamlit as st
import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import minimize
import logging
import sys
from datetime import datetime
from typing import Dict, Optional, List, Tuple, Union
from pathlib import Path
from config import PortfolioConfig
from portfolio_tracker import (
    load_portfolio,
    fetch_historical_data,
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

st.title("Portfolio Optimization")

# Sidebar options
st.sidebar.header("Optimization Options")
period = st.sidebar.selectbox(
    "Time Period",
    ["1y", "3y", "5y"],
    index=0,
    help="Historical data period for optimization"
)

risk_free_rate = st.sidebar.number_input(
    "Risk-Free Rate (%)",
    min_value=0.0,
    max_value=10.0,
    value=2.0,
    step=0.1,
    help="Annual risk-free rate for optimization"
) / 100

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
else:
    try:
        # Fetch historical data
        with st.spinner("Loading historical data..."):
            historical_data = fetch_historical_data(portfolio, period=period)
            
        if historical_data.empty:
            st.warning("No historical data available for optimization.")
        else:
            try:
                # Get only stock tickers (exclude cash_balance)
                stock_tickers = [ticker for ticker in portfolio.keys() if ticker not in ["cash_balance"]]
                
                # Calculate returns and covariance matrix for stocks only
                returns = historical_data[stock_tickers].pct_change().dropna()
                cov_matrix = returns.cov()
                mean_returns = returns.mean()
                
                # Optimization functions
                def portfolio_return(weights):
                    return np.sum(mean_returns * weights)
                    
                def portfolio_volatility(weights):
                    return np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
                    
                def negative_sharpe_ratio(weights):
                    p_return = portfolio_return(weights)
                    p_volatility = portfolio_volatility(weights)
                    return -(p_return - risk_free_rate) / p_volatility
                
                # Constraints and bounds
                constraints = (
                    {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},  # weights sum to 1
                    {'type': 'ineq', 'fun': lambda x: x}  # weights >= 0
                )
                bounds = tuple((0, 1) for _ in range(len(mean_returns)))
                
                # Initial guess (equal weights)
                initial_weights = np.ones(len(mean_returns)) / len(mean_returns)
                
                # Run optimization
                with st.spinner("Optimizing portfolio..."):
                    result = minimize(
                        negative_sharpe_ratio,
                        initial_weights,
                        method='SLSQP',
                        bounds=bounds,
                        constraints=constraints
                    )
                
                # Display results
                st.header("Optimization Results")
                
                # Current portfolio vs optimized portfolio
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Current Portfolio")
                    current_weights = np.array([portfolio[ticker]['target_allocation'] 
                                             for ticker in mean_returns.index])
                    current_return = portfolio_return(current_weights)
                    current_volatility = portfolio_volatility(current_weights)
                    current_sharpe = (current_return - risk_free_rate) / current_volatility
                    
                    st.write(f"Current Return: {current_return:.4f}")
                    st.write(f"Current Volatility: {current_volatility:.4f}")
                    st.write(f"Current Sharpe Ratio: {current_sharpe:.4f}")
                    
                    # Display current portfolio allocation
                    current_df = pd.DataFrame({
                        'Ticker': mean_returns.index,
                        'Allocation': current_weights
                    })
                    st.dataframe(current_df)
                
                with col2:
                    st.subheader("Optimized Portfolio")
                    optimized_weights = result.x
                    optimized_return = portfolio_return(optimized_weights)
                    optimized_volatility = portfolio_volatility(optimized_weights)
                    optimized_sharpe = (optimized_return - risk_free_rate) / optimized_volatility
                    
                    st.write(f"Optimized Return: {optimized_return:.4f}")
                    st.write(f"Optimized Volatility: {optimized_volatility:.4f}")
                    st.write(f"Optimized Sharpe Ratio: {optimized_sharpe:.4f}")
                    
                    # Display optimized portfolio allocation
                    optimized_df = pd.DataFrame({
                        'Ticker': mean_returns.index,
                        'Allocation': optimized_weights
                    })
                    st.dataframe(optimized_df)
                
                # Create allocation comparison plot
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=mean_returns.index,
                    y=current_weights,
                    name='Current Allocation'
                ))
                fig.add_trace(go.Bar(
                    x=mean_returns.index,
                    y=optimized_weights,
                    name='Optimized Allocation'
                ))
                
                fig.update_layout(
                    title='Portfolio Allocation Comparison',
                    yaxis_title='Allocation',
                    barmode='group'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
            except Exception as e:
                st.error(f"Error in optimization calculations: {str(e)}")
    except Exception as e:
        st.error(f"Error during portfolio optimization: {str(e)}")
        
        with col1:
            st.subheader("Current Portfolio")
            current_weights = np.array([portfolio[ticker]['target_allocation'] 
                                     for ticker in mean_returns.index])
            current_return = portfolio_return(current_weights)
            current_volatility = portfolio_volatility(current_weights)
            current_sharpe = (current_return - risk_free_rate) / current_volatility
            
            st.metric("Return", f"{current_return:.2%}")
            st.metric("Volatility", f"{current_volatility:.2%}")
            st.metric("Sharpe Ratio", f"{current_sharpe:.2f}")
            
        with col2:
            st.subheader("Optimized Portfolio")
            optimized_return = portfolio_return(result.x)
            optimized_volatility = portfolio_volatility(result.x)
            optimized_sharpe = (optimized_return - risk_free_rate) / optimized_volatility
            
            st.metric("Return", f"{optimized_return:.2%}")
            st.metric("Volatility", f"{optimized_volatility:.2%}")
            st.metric("Sharpe Ratio", f"{optimized_sharpe:.2f}")
            
        # Portfolio weights comparison
        st.header("Portfolio Weights")
        weights_df = pd.DataFrame({
            'Ticker': mean_returns.index,
            'Current Weight': current_weights,
            'Optimized Weight': result.x
        })
        
        st.dataframe(weights_df.style.highlight_max(subset=['Optimized Weight'], color='lightgreen'))
        
        # Efficient frontier
        st.header("Efficient Frontier")
        
        n_points = 100
        target_returns = np.linspace(
            min(mean_returns),
            max(mean_returns),
            n_points
        )
        
        frontier_volatility = []
        for target in target_returns:
            def target_return_constraint(x):
                return portfolio_return(x) - target
                
            constraints = (
                {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
                {'type': 'eq', 'fun': target_return_constraint},
                {'type': 'ineq', 'fun': lambda x: x}
            )
            
            result = minimize(
                portfolio_volatility,
                initial_weights,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints
            )
            
            frontier_volatility.append(result.fun)
            
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=frontier_volatility,
                y=target_returns,
                mode='lines',
                name='Efficient Frontier'
            )
        )
        
        # Add current and optimized portfolios
        fig.add_trace(
            go.Scatter(
                x=[current_volatility],
                y=[current_return],
                mode='markers',
                name='Current Portfolio',
                marker=dict(color='red', size=10)
            )
        )
        
        fig.add_trace(
            go.Scatter(
                x=[optimized_volatility],
                y=[optimized_return],
                mode='markers',
                name='Optimized Portfolio',
                marker=dict(color='green', size=10)
            )
        )
        
        fig.update_layout(
            title="Efficient Frontier",
            xaxis_title="Volatility",
            yaxis_title="Return",
            legend_title="Portfolios"
        )
        
        st.plotly_chart(fig, use_container_width=True)
