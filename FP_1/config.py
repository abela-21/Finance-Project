import os
from dotenv import load_dotenv

load_dotenv()

class PortfolioConfig:
    """
    Configuration class for the portfolio tracker application.

    Attributes:
        portfolio_file (str): The path to the portfolio CSV file.
    """
    def __init__(self, portfolio_file):
        self.portfolio_file = portfolio_file

    @classmethod
    def from_env(cls):
        """
        Creates a PortfolioConfig instance from environment variables.

        Returns:
            PortfolioConfig: A new instance of the PortfolioConfig class.
        """
        portfolio_file = os.getenv("PORTFOLIO_FILE", "portfolio.csv")
        return cls(portfolio_file)
