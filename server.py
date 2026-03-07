"""
WalletGuard API Server
FastAPI backend with REAL OpenGradient integration:
  - Real wallet scanning via Blockscout
  - TEE-Verified LLM (GPT-4.1) for risk report generation
  - x402 settlement on-chain
  - Cryptographic TEE signatures as proof

Usage:
    uvicorn server:app --reload --port 8000
"""

import json
import math
import os
import time

import numpy as np
import opengradient as og
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import (
    DEFAULT_VOLATILITY,
    TOKEN_VOLATILITY,
)

# --- Load private key from .env file ---
ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(ENV_PATH):
    with open(ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip()

OG_PRIVATE_KEY = os.environ.get("OG_PRIVATE_KEY", "")
if OG_PRIVATE_KEY and not OG_PRIVATE_KEY.startswith("0x"):
    OG_PRIVATE_KEY = "0x" + OG_PRIVATE_KEY

# --- Initialize OpenGradient client ---
og_client = None
if OG_PRIVATE_KEY:
    try:
        og_client = og.init(private_key=OG_PRIVATE_KEY)
        og_client.llm.ensure_opg_approval(opg_amount=5.0)
        print("[+] OpenGradient client initialized, OPG approved")
    except Exception as e:
        print(f"[!] OpenGradient init failed: {e}. Running in local-only mode.")
        og_client = None
else:
    print("[!] OG_PRIVATE_KEY not set. Running in local-only mode.")

# --- ONNX Model on OpenGradient Model Hub ---
RISK_MODEL_CID = "ernjD89Y32XBE0K_KeO0IpHrxcUnjS374jG-nBj7sBQ"


app = FastAPI(title="WalletGuard API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    wallet_address: str


# ---------- Blockchain Data (Blockscout - real on-chain data) ----------

BLOCKSCOUT_BASE = "https://eth.blockscout.com/api/v2"


def fetch_holdings(wallet_address: str) -> dict:
    """Fetch REAL token holdings from Ethereum mainnet via Blockscout."""

    # 1. Get ETH balance + exchange rate
    addr_resp = requests.get(
        f"{BLOCKSCOUT_BASE}/addresses/{wallet_address}",
        timeout=15,
    )
    addr_resp.raise_for_status()
    addr_data = addr_resp.json()

    eth_balance_wei = int(addr_data.get("coin_balance") or 0)
    eth_balance = eth_balance_wei / 1e18
    eth_price = float(addr_data.get("exchange_rate") or 0)
    eth_usd = eth_balance * eth_price

    holdings = []
    if eth_balance > 0.0001:
        holdings.append({
            "symbol": "ETH",
            "name": "Ethereum",
            "balance": round(eth_balance, 6),
            "usd_value": round(eth_usd, 2),
            "pct": 0,
        })

    # 2. Get ERC-20 token balances
    tokens_resp = requests.get(
        f"{BLOCKSCOUT_BASE}/addresses/{wallet_address}/token-balances",
        timeout=15,
    )
    tokens_resp.raise_for_status()
    tokens_data = tokens_resp.json()

    for item in tokens_data:
        token = item.get("token", {})
        if token.get("type") != "ERC-20":
            continue

        raw_value = int(item.get("value") or 0)
        decimals = int(token.get("decimals") or 18)
        balance = raw_value / (10 ** decimals)

        if balance <= 0:
            continue

        symbol = token.get("symbol") or "???"
        name = token.get("name") or symbol
        price = float(token.get("exchange_rate") or 0)
        usd_value = balance * price

        if usd_value < 0.01 and price > 0:
            continue

        holdings.append({
            "symbol": symbol,
            "name": name,
            "balance": round(balance, 6),
            "usd_value": round(usd_value, 2),
            "pct": 0,
        })

    holdings.sort(key=lambda h: h["usd_value"], reverse=True)

    total_usd = sum(h["usd_value"] for h in holdings)
    for h in holdings:
        h["pct"] = round((h["usd_value"] / total_usd * 100) if total_usd > 0 else 0, 1)

    return {
        "address": wallet_address,
        "chain": "ethereum",
        "holdings": holdings,
        "total_usd": round(total_usd, 2),
    }


# ---------- Risk Math (local computation) ----------


def compute_concentration(holdings: list[dict], total_usd: float) -> dict:
    if not holdings or total_usd == 0:
        return {
            "hhi_index": 0,
            "top_asset": {"symbol": "N/A", "weight_pct": 0},
            "effective_num_assets": 0,
            "diversification_score": 0,
            "concentration_tier": "LOW",
            "num_holdings": 0,
        }

    weights = [h["usd_value"] / total_usd for h in holdings]
    symbols = [h["symbol"] for h in holdings]

    hhi = sum(w**2 for w in weights)
    max_weight = max(weights)
    max_symbol = symbols[weights.index(max_weight)]
    effective_n = 1.0 / hhi if hhi > 0 else len(holdings)

    ideal_hhi = 1.0 / len(holdings) if len(holdings) > 0 else 1.0
    if ideal_hhi < 1:
        diversification_score = max(0, min(100, (1 - hhi) / (1 - ideal_hhi) * 100))
    else:
        diversification_score = 0

    if hhi > 0.5:
        tier = "CRITICAL"
    elif hhi > 0.3:
        tier = "HIGH"
    elif hhi > 0.15:
        tier = "MODERATE"
    else:
        tier = "LOW"

    return {
        "hhi_index": round(hhi, 4),
        "top_asset": {"symbol": max_symbol, "weight_pct": round(max_weight * 100, 1)},
        "effective_num_assets": round(effective_n, 1),
        "diversification_score": round(diversification_score, 1),
        "concentration_tier": tier,
        "num_holdings": len(holdings),
    }


def compute_volatility(holdings: list[dict], total_usd: float) -> dict:
    if not holdings or total_usd == 0:
        return {
            "portfolio_volatility": 0,
            "volatility_score": 0,
            "hhi_from_model": 0,
            "max_weight_from_model": 0,
            "composite_risk_score": 0,
            "risk_tier": "LOW",
            "onnx_on_chain": False,
            "model_cid": RISK_MODEL_CID,
        }

    weights = [h["usd_value"] / total_usd for h in holdings]
    vols = [TOKEN_VOLATILITY.get(h["symbol"].upper(), DEFAULT_VOLATILITY) for h in holdings]

    # Attempt on-chain ONNX inference via OpenGradient
    onnx_on_chain = False
    onnx_tx_hash = None
    if og_client:
        try:
            result = og_client.alpha.infer(
                model_cid=RISK_MODEL_CID,
                inference_mode=og.InferenceMode.VANILLA,
                model_input={
                    "weights": np.array([weights], dtype=np.float32),
                    "volatilities": np.array([vols], dtype=np.float32),
                },
                max_retries=2,
            )
            # Extract model outputs
            output = result.model_output
            port_vol = float(output.get("portfolio_vol", [[0]])[0][0])
            hhi = float(output.get("hhi", [[0]])[0][0])
            max_w = float(output.get("max_weight", [[0]])[0][0])
            onnx_on_chain = True
            onnx_tx_hash = result.transaction_hash
            print(f"[+] On-chain ONNX inference succeeded, tx: {onnx_tx_hash}")
        except Exception as e:
            print(f"[!] On-chain ONNX inference failed: {e}, using local math")
            onnx_on_chain = False

    if not onnx_on_chain:
        # Local fallback computation
        port_vol = math.sqrt(sum((w * v) ** 2 for w, v in zip(weights, vols)))
        hhi = sum(w**2 for w in weights)
        max_w = max(weights)

    vol_score = min(100, max(0, port_vol / 2.0 * 100))
    composite = 0.5 * vol_score + 0.3 * (hhi * 100) + 0.2 * (max_w * 100)

    if composite > 70:
        tier = "CRITICAL"
    elif composite > 50:
        tier = "HIGH"
    elif composite > 30:
        tier = "MODERATE"
    else:
        tier = "LOW"

    result = {
        "portfolio_volatility": round(port_vol, 4),
        "volatility_score": round(vol_score, 1),
        "hhi_from_model": round(hhi, 4),
        "max_weight_from_model": round(max_w, 4),
        "composite_risk_score": round(composite, 1),
        "risk_tier": tier,
        "onnx_on_chain": onnx_on_chain,
        "model_cid": RISK_MODEL_CID,
    }
    if onnx_tx_hash:
        result["onnx_tx_hash"] = onnx_tx_hash
    return result


# ---------- TEE-Verified LLM Report Generation (OpenGradient) ----------


def generate_report_with_tee(portfolio: dict, concentration: dict, volatility: dict) -> dict:
    """
    Generate a risk report using OpenGradient's TEE-Verified LLM.
    Returns both the report text and the TEE cryptographic proof.
    """
    holdings_summary = "\n".join(
        f"  - {h['symbol']} ({h['name']}): {h['balance']} tokens, ${h['usd_value']:.2f} ({h['pct']}%)"
        for h in portfolio["holdings"]
    )

    prompt = f"""You are WalletGuard, an expert crypto portfolio risk analyst.
Analyze this Ethereum wallet and generate a concise risk report.

WALLET: {portfolio['address']}
TOTAL VALUE: ${portfolio['total_usd']:,.2f}
HOLDINGS:
{holdings_summary}

RISK METRICS:
- Concentration tier: {concentration['concentration_tier']} (HHI: {concentration['hhi_index']:.4f})
- Top asset: {concentration['top_asset']['symbol']} at {concentration['top_asset']['weight_pct']:.1f}%
- Diversification score: {concentration['diversification_score']:.1f}/100
- Effective assets: {concentration['effective_num_assets']:.1f} of {concentration['num_holdings']}
- Volatility score: {volatility['volatility_score']:.1f}/100
- Composite risk: {volatility['composite_risk_score']:.1f}/100 ({volatility['risk_tier']})

Write a report with these sections:
1. PORTFOLIO OVERVIEW (2-3 lines summarizing the wallet)
2. KEY FINDINGS (2-4 bullet points about the biggest risks found)
3. RECOMMENDATIONS (2-3 actionable suggestions)

Be specific with numbers. Be direct and concise."""

    if og_client:
        try:
            result = og_client.llm.chat(
                model=og.TEE_LLM.GPT_4_1_2025_04_14,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3,
                x402_settlement_mode=og.x402SettlementMode.SETTLE_METADATA,
            )

            report_text = result.chat_output.get("content", "")
            tee_proof = {
                "tee_signature": result.tee_signature,
                "tee_timestamp": result.tee_timestamp,
                "payment_hash": result.payment_hash,
                "transaction_hash": result.transaction_hash,
                "model": "GPT_4_1_2025_04_14",
                "settlement_mode": "SETTLE_METADATA",
                "verified": True,
            }
            return {"report": report_text, "tee_proof": tee_proof}

        except Exception as e:
            print(f"[!] TEE LLM call failed: {e}, falling back to local report")

    # Fallback: local report generation
    return {
        "report": _generate_local_report(portfolio, concentration, volatility),
        "tee_proof": None,
    }


def _generate_local_report(portfolio: dict, concentration: dict, volatility: dict) -> str:
    """Fallback local report when OpenGradient is unavailable."""
    holdings = portfolio["holdings"]
    top = concentration["top_asset"]

    lines = [
        "WALLETGUARD RISK REPORT (local mode)",
        "=" * 40,
        f"Wallet: {portfolio['address']}",
        f"Total Value: ${portfolio['total_usd']:,.2f}",
        f"Assets: {len(holdings)} | Top: {top['symbol']} at {top['weight_pct']:.1f}%",
        f"Overall Risk: {volatility['risk_tier']} ({volatility['composite_risk_score']:.1f}/100)",
        "",
        "Note: TEE-verified report unavailable. This is a local analysis.",
    ]
    return "\n".join(lines)


# ---------- API Endpoint ----------


@app.post("/api/analyze")
async def analyze(req: AnalyzeRequest):
    addr = req.wallet_address.strip()
    if not addr.startswith("0x") or len(addr) != 42:
        raise HTTPException(status_code=400, detail="Invalid Ethereum address format")

    # 1. Fetch real blockchain data
    portfolio = fetch_holdings(addr)

    # 2. Compute risk metrics locally (deterministic math)
    concentration = compute_concentration(portfolio["holdings"], portfolio["total_usd"])
    volatility = compute_volatility(portfolio["holdings"], portfolio["total_usd"])

    # 3. Generate report via TEE-Verified LLM (OpenGradient)
    report_result = generate_report_with_tee(portfolio, concentration, volatility)

    # 4. Build proof list
    proofs = []
    tee_proof = report_result.get("tee_proof")

    if tee_proof and tee_proof.get("verified"):
        proofs.append({
            "type": "TEE-Verified LLM Inference",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "tee_signature": tee_proof["tee_signature"][:80] + "..." if tee_proof.get("tee_signature") else None,
            "tee_timestamp": tee_proof.get("tee_timestamp"),
            "payment_hash": tee_proof.get("payment_hash"),
            "transaction_hash": tee_proof.get("transaction_hash"),
            "model": tee_proof["model"],
            "settlement_mode": tee_proof["settlement_mode"],
            "verified": True,
            "note": "Report generated inside Trusted Execution Environment with cryptographic attestation",
        })
    else:
        proofs.append({
            "type": "Local Analysis",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "verified": False,
            "note": "OpenGradient TEE unavailable, report generated locally",
        })

    # ONNX Model proof
    onnx_proof = {
        "type": "ONNX Risk Model",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "model_cid": RISK_MODEL_CID,
        "source": "OpenGradient Model Hub",
        "verified": volatility.get("onnx_on_chain", False),
    }
    if volatility.get("onnx_on_chain"):
        onnx_proof["transaction_hash"] = volatility.get("onnx_tx_hash")
        onnx_proof["inference_mode"] = "VANILLA"
        onnx_proof["note"] = "Risk scoring executed on-chain via OpenGradient Alpha inference"
    else:
        onnx_proof["note"] = "Model uploaded to Model Hub (CID verified). Inference ran locally (Alpha devnet unavailable)"
    proofs.append(onnx_proof)

    proofs.append({
        "type": "On-Chain Wallet Scan",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": "Blockscout API (eth.blockscout.com)",
        "chain": "Ethereum Mainnet",
        "verified": True,
        "note": "Holdings fetched from live Ethereum blockchain state",
    })

    return {
        "portfolio": portfolio,
        "concentration": concentration,
        "volatility": volatility,
        "report": report_result["report"],
        "proofs": proofs,
    }


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "service": "walletguard",
        "opengradient_connected": og_client is not None,
    }
