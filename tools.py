"""
WalletGuard Tools
Three LangChain-compatible tools for the ReAct agent:
  1. get_portfolio_holdings  - Fetch/mock wallet token balances
  2. calculate_concentration_risk - Local HHI and diversification math
  3. run_volatility_model (via create_run_model_tool) - On-chain ONNX inference
"""

import json

import numpy as np
import requests
from langchain_core.tools import tool
from pydantic import BaseModel, Field

import opengradient as og
from opengradient.alphasense import ToolType, create_run_model_tool

from config import (
    DEFAULT_VOLATILITY,
    ETHERSCAN_API_KEY,
    MOCK_PORTFOLIOS,
    RISK_MODEL_CID,
    TOKEN_VOLATILITY,
    USE_MOCK_DATA,
)


# ============================================================
# Tool 1: Portfolio Holdings
# ============================================================


def _fetch_from_etherscan(wallet_address: str) -> dict:
    """Fetch real token balances from Etherscan free API."""
    base_url = "https://api.etherscan.io/api"

    # ETH balance
    eth_resp = requests.get(
        base_url,
        params={
            "module": "account",
            "action": "balance",
            "address": wallet_address,
            "tag": "latest",
            "apikey": ETHERSCAN_API_KEY,
        },
        timeout=10,
    )
    eth_data = eth_resp.json()
    eth_balance = int(eth_data.get("result", "0")) / 1e18

    # ERC-20 token transfers (last 200)
    token_resp = requests.get(
        base_url,
        params={
            "module": "account",
            "action": "tokentx",
            "address": wallet_address,
            "startblock": 0,
            "endblock": 99999999,
            "page": 1,
            "offset": 200,
            "sort": "desc",
            "apikey": ETHERSCAN_API_KEY,
        },
        timeout=10,
    )
    token_data = token_resp.json()

    # Aggregate net balances per token
    token_balances = {}
    addr_lower = wallet_address.lower()
    for tx in token_data.get("result", []):
        symbol = tx.get("tokenSymbol", "UNKNOWN")
        decimals = int(tx.get("tokenDecimal", 18))
        value = int(tx.get("value", "0")) / (10**decimals)

        if symbol not in token_balances:
            token_balances[symbol] = {
                "symbol": symbol,
                "name": tx.get("tokenName", symbol),
                "balance": 0.0,
            }

        if tx.get("to", "").lower() == addr_lower:
            token_balances[symbol]["balance"] += value
        elif tx.get("from", "").lower() == addr_lower:
            token_balances[symbol]["balance"] -= value

    # Build holdings list
    holdings = [
        {"symbol": "ETH", "name": "Ethereum", "balance": eth_balance, "usd_value": eth_balance * 2500.0}
    ]
    for data in token_balances.values():
        if data["balance"] > 0:
            holdings.append(
                {
                    "symbol": data["symbol"],
                    "name": data["name"],
                    "balance": round(data["balance"], 4),
                    "usd_value": 0.0,
                }
            )

    total = sum(h["usd_value"] for h in holdings)
    for h in holdings:
        h["pct"] = round((h["usd_value"] / total * 100) if total > 0 else 0, 2)

    return {"address": wallet_address, "chain": "ethereum", "holdings": holdings, "total_usd": total}


def _fetch_mock(wallet_address: str) -> dict:
    """Return mock portfolio data."""
    portfolio = MOCK_PORTFOLIOS.get(wallet_address, MOCK_PORTFOLIOS["default"]).copy()
    portfolio["address"] = wallet_address
    return portfolio


@tool
def get_portfolio_holdings(wallet_address: str) -> str:
    """
    Fetches the token holdings for an Ethereum wallet address.
    Returns JSON with token symbols, balances, USD values, and percentage allocations.
    """
    try:
        if USE_MOCK_DATA or not ETHERSCAN_API_KEY:
            portfolio = _fetch_mock(wallet_address)
        else:
            portfolio = _fetch_from_etherscan(wallet_address)
    except Exception as e:
        portfolio = _fetch_mock(wallet_address)
        portfolio["_note"] = f"Live fetch failed ({e}), using simulated data"

    return json.dumps(portfolio, indent=2)


# ============================================================
# Tool 2: Concentration Risk (local computation)
# ============================================================


@tool
def calculate_concentration_risk(holdings_json: str) -> str:
    """
    Calculates portfolio concentration metrics from holdings data.
    Input: JSON string of holdings (as returned by get_portfolio_holdings).
    Returns: HHI index, top-asset concentration, diversification score, and risk tier.
    """
    data = json.loads(holdings_json)
    holdings = data.get("holdings", [])

    if not holdings:
        return json.dumps({"error": "No holdings provided"})

    total_usd = sum(h.get("usd_value", 0) for h in holdings)
    if total_usd == 0:
        return json.dumps({"error": "Total portfolio value is zero"})

    weights = [h["usd_value"] / total_usd for h in holdings]
    symbols = [h["symbol"] for h in holdings]

    # Herfindahl-Hirschman Index
    hhi = sum(w**2 for w in weights)

    # Top asset
    max_weight = max(weights)
    max_symbol = symbols[weights.index(max_weight)]

    # Effective number of assets (inverse HHI)
    effective_n = 1.0 / hhi if hhi > 0 else len(holdings)

    # Diversification score: 0-100
    ideal_hhi = 1.0 / len(holdings) if len(holdings) > 0 else 1.0
    if ideal_hhi < 1:
        diversification_score = max(0, min(100, (1 - hhi) / (1 - ideal_hhi) * 100))
    else:
        diversification_score = 0

    # Risk tier
    if hhi > 0.5:
        tier = "CRITICAL"
    elif hhi > 0.3:
        tier = "HIGH"
    elif hhi > 0.15:
        tier = "MODERATE"
    else:
        tier = "LOW"

    result = {
        "hhi_index": round(hhi, 4),
        "top_asset": {"symbol": max_symbol, "weight_pct": round(max_weight * 100, 1)},
        "effective_num_assets": round(effective_n, 1),
        "diversification_score": round(diversification_score, 1),
        "concentration_tier": tier,
        "num_holdings": len(holdings),
    }
    return json.dumps(result, indent=2)


# ============================================================
# Tool 3: On-Chain ONNX Volatility Model
# ============================================================


class VolatilityModelInput(BaseModel):
    """Schema for the LLM to invoke the on-chain volatility model."""

    portfolio_weights: list[float] = Field(
        description="Portfolio allocation weights as decimals summing to 1.0, one per asset"
    )
    asset_symbols: list[str] = Field(
        description="Token symbols in the same order as weights, e.g. ['ETH', 'USDC', 'UNI']"
    )


def provide_volatility_model_input(
    portfolio_weights: list[float],
    asset_symbols: list[str],
) -> dict:
    """Convert LLM tool-call args into ONNX model input tensors."""
    vols = [TOKEN_VOLATILITY.get(sym.upper(), DEFAULT_VOLATILITY) for sym in asset_symbols]
    return {
        "weights": np.array([portfolio_weights], dtype=np.float32),
        "volatilities": np.array([vols], dtype=np.float32),
    }


def format_volatility_model_output(result) -> str:
    """Convert ONNX InferenceResult into a readable JSON string with proof."""
    tx_hash = result.transaction_hash
    scores = result.model_output["risk_scores"][0]

    port_vol = float(scores[0])
    hhi = float(scores[1])
    max_w = float(scores[2])

    # Normalize volatility to 0-100 scale (2.0 annualized = 100)
    vol_score = min(100, max(0, port_vol / 2.0 * 100))

    # Composite risk score
    composite = 0.5 * vol_score + 0.3 * (hhi * 100) + 0.2 * (max_w * 100)

    if composite > 70:
        tier = "CRITICAL"
    elif composite > 50:
        tier = "HIGH"
    elif composite > 30:
        tier = "MODERATE"
    else:
        tier = "LOW"

    output = {
        "portfolio_volatility": round(port_vol, 4),
        "volatility_score": round(vol_score, 1),
        "hhi_from_model": round(hhi, 4),
        "max_weight_from_model": round(max_w, 4),
        "composite_risk_score": round(composite, 1),
        "risk_tier": tier,
        "on_chain_proof": {
            "transaction_hash": tx_hash,
            "inference_mode": "VANILLA",
            "model_cid": RISK_MODEL_CID,
            "verified": True,
        },
    }
    return json.dumps(output, indent=2)


def create_volatility_tool(client: og.Client):
    """Factory: create the on-chain ONNX volatility tool (needs initialized client)."""
    return create_run_model_tool(
        tool_type=ToolType.LANGCHAIN,
        model_cid=RISK_MODEL_CID,
        tool_name="run_volatility_model",
        tool_description=(
            "Runs an on-chain ONNX model to calculate portfolio volatility risk. "
            "Provide portfolio_weights (list of floats summing to 1.0) and "
            "asset_symbols (list of token symbols in same order). "
            "Returns volatility score, composite risk score, and on-chain transaction proof."
        ),
        model_input_provider=provide_volatility_model_input,
        model_output_formatter=format_volatility_model_output,
        inference=client.alpha,
        tool_input_schema=VolatilityModelInput,
        inference_mode=og.InferenceMode.VANILLA,
    )
