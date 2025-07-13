# Portfolio Tracker

## Overview
The **Portfolio Tracker** is a comprehensive web application built using Streamlit to help users manage, analyze, and optimize their investment portfolios. It provides tools for tracking portfolio performance, calculating risk metrics, visualizing allocation, and making informed decisions about rebalancing. The application is designed to be user-friendly and interactive, making it suitable for both novice and experienced investors.

## Features
### 1. **Dashboard**
   - View a summary of your portfolio, including:
     - **Total Portfolio Value**: The combined market value of all assets.
     - **Dividend Income**: The cumulative dividend income from all stocks.
     - **Transaction Costs**: The total transaction costs incurred during trades.
   - Visualize portfolio allocation using interactive charts powered by Plotly.

### 2. **Portfolio Management**
   - Add, remove, or update stocks in your portfolio.
   - Manage target allocations for each stock and adjust cash balances.
   - Load portfolio data from a CSV file or manually input stock details.

### 3. **Performance Analysis**
   - Analyze historical performance trends of your portfolio.
   - Fetch historical stock prices using the `yfinance` library.
   - Visualize historical data with interactive line charts to identify trends and patterns.

### 4. **Risk Analysis**
   - Calculate and display key risk metrics, including:
     - **Volatility**: Measure the variability of portfolio returns.
     - **Sharpe Ratio**: Assess risk-adjusted returns.
     - **Beta**: Evaluate portfolio sensitivity to market movements.
     - **Alpha**: Measure portfolio performance relative to a benchmark.
   - View risk metrics in a tabular format for easy interpretation.

### 5. **Rebalancing Recommendations**
   - Automatically calculate rebalancing actions based on target allocations.
   - Provide recommendations for buying or selling stocks to optimize portfolio balance.
   - Account for transaction costs and cash buffers during rebalancing.

### 6. **Interactive Visualizations**
   - Use Plotly charts to visualize portfolio allocation, historical performance, and rebalancing actions.
   - Enable dynamic exploration of data with hover-over details and zoom functionality.

## Installation

### Prerequisites
- Python 3.12 or higher
- Streamlit
- Pandas
- Plotly
- Watchdog (optional for better performance)
- `yfinance` for fetching stock data

### Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/portfolio-tracker.git
   cd portfolio-tracker
   ```

2. Create a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   streamlit run FP_1/portfolio_tracker_app.py
   ```

## Usage
1. **Navigate the Sidebar**:
   - Select a page from the sidebar menu:
     - **Dashboard**: View portfolio summary and allocation.
     - **Portfolio Management**: Add, remove, or update stocks.
     - **Performance Analysis**: Analyze historical trends.
     - **Risk Analysis**: View risk metrics.
     - **Rebalancing Recommendations**: Optimize portfolio balance.

2. **Load Portfolio Data**:
   - Upload a CSV file containing portfolio details or manually input stock data.
   - Ensure the file is formatted correctly with columns such as `Ticker`, `Quantity`, `Dividends`, `TransactionCost`, `TargetAllocation`, and `CashBalance`.

3. **Explore Visualizations**:
   - Interact with charts to gain insights into portfolio allocation and performance.

4. **Analyze Risk Metrics**:
   - View calculated metrics such as volatility, Sharpe ratio, beta, and alpha.

5. **Rebalance Portfolio**:
   - Follow recommendations to buy or sell stocks and optimize portfolio balance.

## File Structure
```
Finance Project/
├── FP_1/
│   ├── portfolio_tracker_app.py       # Main application file
│   ├── portfolio_tracker.py           # Portfolio-related functions
│   ├── config.py                       # Configuration management
│   ├── pages/                          # Streamlit page files
│   │   ├── 1_Dashboard.py              # Dashboard page
│   │   ├── 6_Risk_metrics.py           # Risk metrics page
│   │   └── ...                         # Other pages
│   └── portfolio.csv                   # Example portfolio file
├── .venv/                              # Virtual environment
├── requirements.txt                    # Python dependencies
└── README.md                           # Project documentation
```

## Example Portfolio File
The portfolio file should be a CSV with the following format:
```csv
Ticker,Quantity,Dividends,TransactionCost,TargetAllocation,CashBalance
AAPL,12,1.01,5.0,0.22,100.0
AMZN,13,0.0,5.0,0.01,100.0
TSLA,14,0.0,4.0,0.28,100.0
KO,24,1.965,4.0,0.17,100.0
MSFT,18,2.41,5.0,0.32,100.0
```

## Key Functions
### `portfolio_tracker_app.py`
- **`load_portfolio`**: Loads portfolio data from a CSV file.
- **`calculate_portfolio_value`**: Calculates the total and net portfolio value.
- **`calculate_dividend_income`**: Computes the total dividend income.
- **`calculate_risk_metrics`**: Calculates risk metrics such as volatility, Sharpe ratio, beta, and alpha.
- **`plot_portfolio_allocation`**: Generates a chart showing portfolio allocation.
- **`plot_historical_performance`**: Visualizes historical performance trends.

### `portfolio_tracker.py`
- Contains helper functions for portfolio management, risk analysis, and visualization.

### `config.py`
- Manages configuration settings such as file paths and environment variables.

## Troubleshooting
### Common Errors
- **`TypeError: load_portfolio() missing 1 required positional argument: 'path'`**:
  Ensure the `portfolio_file` path is correctly passed to the `load_portfolio` function.
  
- **`NameError: name 'prices' is not defined`**:
  Ensure the `prices` variable is fetched and passed to functions that require it.

### Updating Dependencies
If you encounter issues, ensure all dependencies are up-to-date:
```bash
pip install --upgrade streamlit pandas plotly watchdog yfinance
```

## Contributing
Contributions are welcome! Feel free to open issues or submit pull requests to improve the project.

## License
This project is licensed under the MIT License. See the `LICENSE` file for details.

## Contact
For questions or feedback, please contact [your email or GitHub profile link].# Finance-Tracker
