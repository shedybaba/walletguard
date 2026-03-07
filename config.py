"""
WalletGuard Configuration
Environment variables, mock data, and constants.
"""

import os

# --- OpenGradient ---
OG_PRIVATE_KEY = os.environ.get("OG_PRIVATE_KEY")

# CID of the uploaded ONNX risk model on OpenGradient Model Hub
RISK_MODEL_CID = os.environ.get("RISK_MODEL_CID", "<your-model-cid-here>")

# --- Etherscan (optional, for live data) ---
ETHERSCAN_API_KEY = os.environ.get("ETHERSCAN_API_KEY", "")
USE_MOCK_DATA = os.environ.get("USE_MOCK_DATA", "true").lower() == "true"

# --- Settlement ---
SETTLEMENT_MODE = "SETTLE_METADATA"

# --- LLM Selection ---
LLM_MODEL = "GPT_4_1_2025_04_14"
LLM_MAX_TOKENS = 600

# --- Mock Portfolio Data ---
MOCK_PORTFOLIOS = {
    "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045": {
        "address": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        "chain": "ethereum",
        "holdings": [
            {"symbol": "ETH", "name": "Ethereum", "balance": 3500.0, "usd_value": 8_750_000.0, "pct": 62.5},
            {"symbol": "USDC", "name": "USD Coin", "balance": 2_100_000.0, "usd_value": 2_100_000.0, "pct": 15.0},
            {"symbol": "STETH", "name": "Lido Staked ETH", "balance": 800.0, "usd_value": 2_000_000.0, "pct": 14.3},
            {"symbol": "UNI", "name": "Uniswap", "balance": 50_000.0, "usd_value": 600_000.0, "pct": 4.3},
            {"symbol": "LINK", "name": "Chainlink", "balance": 25_000.0, "usd_value": 350_000.0, "pct": 2.5},
            {"symbol": "AAVE", "name": "Aave", "balance": 1_200.0, "usd_value": 200_000.0, "pct": 1.4},
        ],
        "total_usd": 14_000_000.0,
    },
    "default": {
        "address": "unknown",
        "chain": "ethereum",
        "holdings": [
            {"symbol": "ETH", "name": "Ethereum", "balance": 10.5, "usd_value": 26_250.0, "pct": 45.0},
            {"symbol": "USDT", "name": "Tether", "balance": 15_000.0, "usd_value": 15_000.0, "pct": 25.7},
            {"symbol": "PEPE", "name": "Pepe", "balance": 500_000_000.0, "usd_value": 5_500.0, "pct": 9.4},
            {"symbol": "SHIB", "name": "Shiba Inu", "balance": 80_000_000.0, "usd_value": 4_800.0, "pct": 8.2},
            {"symbol": "DOGE", "name": "Dogecoin", "balance": 20_000.0, "usd_value": 3_800.0, "pct": 6.5},
            {"symbol": "ARB", "name": "Arbitrum", "balance": 2_500.0, "usd_value": 3_000.0, "pct": 5.2},
        ],
        "total_usd": 58_350.0,
    },
}

# --- Volatility Reference Data ---
# 30-day annualized volatility estimates per token
TOKEN_VOLATILITY = {
    "ETH": 0.65, "BTC": 0.55, "USDC": 0.01, "USDT": 0.01,
    "STETH": 0.66, "UNI": 0.85, "LINK": 0.78, "AAVE": 0.82,
    "PEPE": 1.95, "SHIB": 1.80, "DOGE": 1.40, "ARB": 0.90,
    "SOL": 0.88, "MATIC": 0.92, "DAI": 0.01,
}
DEFAULT_VOLATILITY = 1.0
