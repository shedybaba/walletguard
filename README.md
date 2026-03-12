# WalletGuard

WalletGuard is an on-chain wallet risk scorer powered by **OpenGradient**.

Paste any Ethereum wallet address and get:
- **Real-time portfolio scan** directly from the blockchain
- **AI risk analysis** generated inside a **Trusted Execution Environment (TEE)**
- **Cryptographic proof** that every inference is verifiable (not just an opinion)

The risk report is written by **GPT-4.1 running in a TEE** with **x402 settlement**, meaning every response comes with a cryptographic signature you can verify on-chain.

## Tech Stack

- **OpenGradient** TEE-Verified LLM
- **ONNX risk model** (via Model Hub — still being perfected)
- **x402** on-chain settlement
- **Blockscout API** for live wallet data
- **Frontend:** React
- **Backend:** FastAPI

## What you can do with WalletGuard

- Generate a wallet risk report for any Ethereum address
- Inspect wallet holdings and activity signals in near real time
- Verify that the inference was produced in a TEE via cryptographic attestation/signature
