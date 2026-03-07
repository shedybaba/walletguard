"""
WalletGuard - On-Chain Wallet Risk Scorer
CLI entry point and ReAct agent orchestration.

Usage:
    python main.py                          # Interactive mode
    python main.py 0xABC123...              # Single-shot mode
"""

import json
import sys
import time

import opengradient as og
from langgraph.prebuilt import create_react_agent

from config import LLM_MAX_TOKENS, LLM_MODEL, OG_PRIVATE_KEY, SETTLEMENT_MODE
from tools import calculate_concentration_risk, create_volatility_tool, get_portfolio_holdings

BANNER = r"""
 __        __    _ _      _    ____                     _
 \ \      / /_ _| | | ___| |_ / ___|_   _  __ _ _ __ __| |
  \ \ /\ / / _` | | |/ _ \ __| |  _| | | |/ _` | '__/ _` |
   \ V  V / (_| | | |  __/ |_| |_| | |_| | (_| | | | (_| |
    \_/\_/ \__,_|_|_|\___|__|\____|\__,_|\__,_|_|  \__,_|

    On-Chain Wallet Risk Scorer | Powered by OpenGradient
"""

SYSTEM_PROMPT = """You are WalletGuard, an expert on-chain wallet risk analysis agent.

When given a wallet address, follow these steps IN ORDER:

1. FETCH HOLDINGS: Call get_portfolio_holdings with the wallet address to retrieve token balances.

2. ANALYZE CONCENTRATION: Call calculate_concentration_risk with the full holdings JSON string
   returned from step 1 to compute the HHI index, diversification score, and concentration tier.

3. RUN VOLATILITY MODEL: Call run_volatility_model with the portfolio weights and asset symbols
   extracted from the holdings data. The weights must be decimals summing to 1.0 (divide each
   token's pct by 100).

4. GENERATE REPORT: Using ALL the data from the three tools above, write a comprehensive
   risk assessment report in this exact format:

   WALLETGUARD RISK REPORT
   =======================
   Wallet: [address]
   Analysis Date: [current date]

   PORTFOLIO OVERVIEW
   - Total Value: $[amount]
   - Number of Assets: [N]
   - Top Holding: [SYMBOL] at [X]%

   RISK SCORES
   - Concentration Risk: [TIER] (HHI: [value])
   - Volatility Exposure: [score]/100
   - Diversification Score: [score]/100
   - Overall Risk: [TIER] ([composite]/100)

   KEY FINDINGS
   [2-3 bullet points about the biggest risks]

   RECOMMENDATIONS
   [2-3 actionable suggestions to improve the risk profile]

   ON-CHAIN VERIFICATION
   - Model TX: [transaction_hash from volatility model]
   - Model CID: [model_cid]
   - Settlement Mode: SETTLE_METADATA (full audit trail)

Always be specific with numbers. Never invent data -- only use values returned by the tools."""


class ProofCollector:
    """Accumulates and displays all on-chain proofs from a single run."""

    def __init__(self):
        self.proofs = []

    def add(self, proof_type: str, data: dict):
        self.proofs.append(
            {"type": proof_type, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **data}
        )

    def display(self):
        print("\n" + "=" * 60)
        print("  ON-CHAIN VERIFICATION PROOFS")
        print("=" * 60)
        for i, proof in enumerate(self.proofs, 1):
            print(f"\n  [{i}] {proof['type']}")
            for k, v in proof.items():
                if k != "type":
                    print(f"      {k}: {v}")
        print("\n" + "=" * 60)


def build_agent():
    """Initialize OpenGradient client, verified LLM, tools, and ReAct agent."""

    # 1. Client + token approval
    client = og.init(private_key=OG_PRIVATE_KEY)
    client.llm.ensure_opg_approval(opg_amount=5.0)
    print("[+] OpenGradient client initialized, OPG approved")

    # 2. Verified LLM
    settlement = getattr(og.x402SettlementMode, SETTLEMENT_MODE)
    llm_model = getattr(og.TEE_LLM, LLM_MODEL)

    llm = og.agents.langchain_adapter(
        private_key=OG_PRIVATE_KEY,
        model_cid=llm_model,
        max_tokens=LLM_MAX_TOKENS,
        x402_settlement_mode=settlement,
    )
    print(f"[+] Verified LLM ready: {LLM_MODEL} (settlement: {SETTLEMENT_MODE})")

    # 3. On-chain ONNX volatility tool
    volatility_tool = create_volatility_tool(client)
    print("[+] On-chain ONNX volatility model tool ready")

    # 4. Assemble ReAct agent
    tools = [get_portfolio_holdings, calculate_concentration_risk, volatility_tool]
    agent = create_react_agent(model=llm, tools=tools)
    print("[+] ReAct agent assembled\n")

    return agent


def run_analysis(agent, wallet_address: str):
    """Run the full risk analysis pipeline for a wallet address."""
    print(f"\n[*] Analyzing wallet: {wallet_address}")
    print("[*] Fetching holdings, running on-chain models, generating report...")
    print("[*] (All LLM calls are TEE-verified; ONNX inference is on-chain)\n")

    result = agent.invoke(
        {
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Analyze the risk profile for this Ethereum wallet: {wallet_address}"},
            ]
        }
    )

    # Display the agent's final response
    final_message = result["messages"][-1]
    print("\n" + "=" * 60)
    print(final_message.content)
    print("=" * 60)

    # Extract and display proofs
    collector = ProofCollector()
    for msg in result["messages"]:
        if hasattr(msg, "content") and isinstance(msg.content, str):
            try:
                data = json.loads(msg.content)
                if "on_chain_proof" in data:
                    collector.add("ONNX Model Inference", data["on_chain_proof"])
            except (json.JSONDecodeError, TypeError):
                pass

    collector.add(
        "Verified LLM Inference",
        {
            "model": LLM_MODEL,
            "settlement_mode": SETTLEMENT_MODE,
            "note": "All LLM reasoning steps TEE-attested via x402 protocol",
        },
    )
    collector.display()

    return result


def main():
    print(BANNER)

    agent = build_agent()

    if len(sys.argv) > 1:
        # Single-shot mode
        run_analysis(agent, sys.argv[1])
    else:
        # Interactive mode
        print("Enter an Ethereum wallet address to analyze (or 'quit' to exit):\n")
        while True:
            try:
                wallet_address = input("walletguard> ").strip()
                if wallet_address.lower() in ("quit", "exit", "q"):
                    print("Goodbye.")
                    break
                if not wallet_address:
                    continue
                if not wallet_address.startswith("0x") or len(wallet_address) != 42:
                    print("Invalid address format. Expected 0x followed by 40 hex characters.")
                    continue
                run_analysis(agent, wallet_address)
                print()
            except KeyboardInterrupt:
                print("\nGoodbye.")
                break
            except Exception as e:
                print(f"\n[ERROR] {e}\n")


if __name__ == "__main__":
    main()
