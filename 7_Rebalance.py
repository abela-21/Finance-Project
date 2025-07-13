import streamlit as st
from portfolio_tracker import load_portfolio, fetch_stock_data, calculate_rebalancing

# Define the portfolio file path
portfolio_path = "/Users/abela/Desktop/Finance Project/FP - 1/portfolio.csv"

st.title("Rebalance Portfolio")

# Load portfolio data
portfolio = load_portfolio(portfolio_path)
if not portfolio or len([k for k in portfolio.keys() if k != "cash_balance"]) == 0:
    st.error("No portfolio data available. Please add stocks.")
else:
    # Fetch current prices
    tickers = [ticker for ticker in portfolio.keys() if ticker != "cash_balance"]
    prices = fetch_stock_data(tickers)

    # Calculate rebalancing actions
    rebalancing_actions, total_transaction_costs = calculate_rebalancing(
        portfolio, prices
    )

    # Generate recommendations with additional details
    recommendations = []
    if rebalancing_actions:
        # Calculate current allocations
        current_values = {}
        for ticker in tickers:
            quantity = portfolio[ticker]["quantity"]
            price = prices.get(ticker, 0)
            current_values[ticker] = quantity * price
        total_value = sum(current_values.values()) + portfolio.get("cash_balance", 0)
        current_allocations = {
            ticker: (value / total_value) * 100
            for ticker, value in current_values.items()
        }  # As percentage

        # Get target allocations (as percentage)
        target_allocations = {
            ticker: portfolio[ticker]["target_allocation"] * 100 for ticker in tickers
        }  # As percentage

        # Generate recommendations
        for ticker, actions in rebalancing_actions.items():
            if actions["buy"] > 0:
                trade_cost = portfolio[ticker]["transaction_cost"]
                recommendations.append(
                    {
                        "action": "Buy",
                        "shares": actions["buy"],
                        "ticker": ticker,
                        "current_allocation": current_allocations.get(ticker, 0),
                        "target_allocation": target_allocations.get(ticker, 0),
                        "trade_cost": trade_cost,
                    }
                )
            if actions["sell"] > 0:
                trade_cost = portfolio[ticker]["transaction_cost"]
                recommendations.append(
                    {
                        "action": "Sell",
                        "shares": actions["sell"],
                        "ticker": ticker,
                        "current_allocation": current_allocations.get(ticker, 0),
                        "target_allocation": target_allocations.get(ticker, 0),
                        "trade_cost": trade_cost,
                    }
                )

    # Display recommendations
    if recommendations:
        st.subheader("Rebalancing Recommendations")
        for rec in recommendations:
            st.write(
                f"{rec['action']} {rec['shares']} shares of {rec['ticker']} "
                f"(Current: {rec['current_allocation']:.1f}%, Target: {rec['target_allocation']:.1f}%, "
                f"Trade Cost: ${rec['trade_cost']:.2f})"
            )
        st.write(
            f"**Total Estimated Transaction Costs:** ${total_transaction_costs:.2f}"
        )
    else:
        st.write("No rebalancing actions needed.")
