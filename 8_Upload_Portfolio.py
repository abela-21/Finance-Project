import streamlit as st
import pandas as pd
import os

st.title("Upload Portfolio")

# File uploader widget
uploaded_file = st.file_uploader("Upload your portfolio CSV file", type=["csv"])

if uploaded_file is not None:
    try:
        # Read the uploaded CSV
        df = pd.read_csv(uploaded_file)

        # Validate columns
        expected_columns = [
            "Ticker",
            "Quantity",
            "Dividends",
            "TransactionCost",
            "TargetAllocation",
            "CashBalance",
        ]
        if not all(col in df.columns for col in expected_columns):
            st.error(f"Invalid CSV format. Expected columns: {expected_columns}")
        else:
            # Validate data types and values
            df["Ticker"] = df["Ticker"].astype(str)
            df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").astype(int)
            df["Dividends"] = pd.to_numeric(df["Dividends"], errors="coerce")
            df["TransactionCost"] = pd.to_numeric(
                df["TransactionCost"], errors="coerce"
            )
            df["TargetAllocation"] = pd.to_numeric(
                df["TargetAllocation"], errors="coerce"
            )
            df["CashBalance"] = pd.to_numeric(df["CashBalance"], errors="coerce")

            # Check for NaN values after conversion
            if (
                df[
                    [
                        "Quantity",
                        "Dividends",
                        "TransactionCost",
                        "TargetAllocation",
                        "CashBalance",
                    ]
                ]
                .isna()
                .any()
                .any()
            ):
                st.error(
                    "Invalid data in CSV: Some numeric fields contain non-numeric values."
                )
            else:
                # Validate TargetAllocation range and sum
                if not (
                    (df["TargetAllocation"] >= 0) & (df["TargetAllocation"] <= 1)
                ).all():
                    st.error("TargetAllocation must be between 0 and 1.")
                elif not abs(df["TargetAllocation"].sum() - 1.0) < 1e-2:
                    st.error(
                        f"Target allocations must sum to 1. Current sum: {df['TargetAllocation'].sum():.2f}"
                    )
                else:
                    # Handle CashBalance (take the first non-NaN value)
                    cash_balance = df["CashBalance"].iloc[0]
                    df["CashBalance"] = cash_balance  # Ensure consistency across rows

                    # Save to portfolio.csv
                    portfolio_path = os.path.join(
                        os.path.dirname(__file__), "../portfolio.csv"
                    )
                    df.to_csv(portfolio_path, index=False)

                    # Clear Streamlit cache to force reload of portfolio data
                    st.cache_data.clear()

                    st.success(
                        "Portfolio updated successfully! Please refresh the Dashboard page to see the changes."
                    )
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
