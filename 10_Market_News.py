import streamlit as st
import os
import logging
import sys
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple, Union
from pathlib import Path
from config import PortfolioConfig
from portfolio_tracker import load_portfolio, fetch_stock_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

st.title("Market News & Alerts")

# Sidebar options
st.sidebar.header("News Options")

# Initialize session state if needed
if 'portfolio' not in st.session_state:
    portfolio_path = os.path.join(os.path.dirname(__file__), "..", "portfolio.csv")
    st.session_state.portfolio = load_portfolio(portfolio_path)
    st.session_state.last_update = datetime.now()

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

# Get portfolio tickers
portfolio_tickers = [ticker for ticker in portfolio.keys() if ticker != "cash_balance"]

# Check portfolio contents
if not portfolio_tickers:
    st.warning("No stocks in portfolio. Please add stocks to see news and set alerts.")
    st.stop()

# News API configuration
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
if not NEWS_API_KEY:
    st.warning("NEWS_API_KEY environment variable not set. News functionality will be limited.")
BASE_URL = "https://newsapi.org/v2/everything"

# Function to get news
@st.cache_data(ttl=3600)
def get_news(tickers: List[str], days: int = 7) -> List[Dict]:
    """Fetch news articles for portfolio tickers."""
    news = []
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    for ticker in tickers:
        try:
            params = {
                'q': f"{ticker} stock",
                'from': start_date,
                'sortBy': 'publishedAt',
                'apiKey': NEWS_API_KEY,
                'language': 'en'
            }
            
            response = requests.get(BASE_URL, params=params)
            if response.status_code == 200:
                articles = response.json().get('articles', [])
                for article in articles:
                    article['ticker'] = ticker
                    news.append(article)
            else:
                logger.error(f"Error fetching news for {ticker}: {response.status_code}")
        except Exception as e:
            logger.error(f"Error in get_news: {str(e)}")
    
    return news

# Display news
st.header("Latest Market News")

# Get news articles
try:
    news = get_news(portfolio_tickers)
    
    if not news:
        st.info("No news articles found for your portfolio tickers.")
    else:
        # Sort news by date
        news.sort(key=lambda x: x['publishedAt'], reverse=True)
        
        # Display news in tabs
        for article in news:
            with st.expander(f"{article['title']} - {article['ticker']}"):
                st.write(f"**Source:** {article['source']['name']}")
                st.write(f"**Published:** {article['publishedAt']}")
                st.write(f"**Description:** {article['description']}")
                
                if article.get('url'):
                    st.markdown(f"[Read more]({article['url']})")
                    
                if article.get('urlToImage'):
                    st.image(article['urlToImage'], use_column_width=True)
                    
except Exception as e:
    st.error(f"Error fetching news: {str(e)}")

# Alerts section
st.header("Price Alerts")

# Alert configuration
alert_config = {
    'price_threshold': st.number_input(
        "Price Change Threshold (%)",
        min_value=0.0,
        value=5.0,
        step=0.1
    ),
    'check_interval': st.selectbox(
        "Check Interval",
        ["5 minutes", "15 minutes", "30 minutes", "1 hour"]
    )
}

# Display current alerts
if st.button("Check for Alerts"):
    try:
        # Get current prices
        prices = fetch_stock_data(portfolio_tickers)
        
        # Check for price changes
        alerts_triggered = []
        for ticker in portfolio_tickers:
            current_price = prices.get(ticker)
            if current_price is not None and current_price != "N/A":
                # Get previous price from portfolio (if stored)
                previous_price = portfolio[ticker].get('previous_price')
                if previous_price is not None:
                    price_change = ((current_price - previous_price) / previous_price) * 100
                    if abs(price_change) >= alert_config['price_threshold']:
                        alerts_triggered.append({
                            'ticker': ticker,
                            'current_price': current_price,
                            'previous_price': previous_price,
                            'change': price_change
                        })
                        
                        # Update portfolio with new price
                        portfolio[ticker]['previous_price'] = current_price
                        
        # Display alerts
        if alerts_triggered:
            st.success(f"Found {len(alerts_triggered)} price alerts!")
            for alert in alerts_triggered:
                direction = "increased" if alert['change'] > 0 else "decreased"
                st.info(f"{alert['ticker']} price {direction} by {abs(alert['change']):.2f}%")
        else:
            st.info("No price alerts triggered.")
            
    except Exception as e:
        st.error(f"Error checking alerts: {str(e)}")

# Add alert for specific ticker
st.header("Add Price Alert")
with st.form("add_alert"):
    ticker = st.selectbox("Select Ticker", portfolio_tickers)
    threshold = st.number_input(
        "Price Change Threshold (%)",
        min_value=0.0,
        value=5.0,
        step=0.1
    )
    direction = st.selectbox(
        "Direction",
        ["Above", "Below"]
    )
    
    if st.form_submit_button("Add Alert"):
        try:
            current_price = fetch_stock_data([ticker])[ticker]
            if current_price is not None and current_price != "N/A":
                portfolio[ticker]['alert_threshold'] = threshold
                portfolio[ticker]['alert_direction'] = direction
                portfolio[ticker]['previous_price'] = current_price
                st.success(f"Alert added for {ticker} with {threshold}% threshold")
            else:
                st.error(f"Could not get current price for {ticker}")
        except Exception as e:
            st.error(f"Error adding alert: {str(e)}")
