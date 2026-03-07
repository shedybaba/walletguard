export interface Holding {
  symbol: string;
  name: string;
  balance: number;
  usd_value: number;
  pct: number;
}

export interface Portfolio {
  address: string;
  chain: string;
  holdings: Holding[];
  total_usd: number;
}

export interface ConcentrationRisk {
  hhi_index: number;
  top_asset: { symbol: string; weight_pct: number };
  effective_num_assets: number;
  diversification_score: number;
  concentration_tier: RiskTier;
  num_holdings: number;
}

export interface OnChainProof {
  transaction_hash: string;
  inference_mode: string;
  model_cid: string;
  verified: boolean;
}

export interface VolatilityResult {
  portfolio_volatility: number;
  volatility_score: number;
  hhi_from_model: number;
  max_weight_from_model: number;
  composite_risk_score: number;
  risk_tier: RiskTier;
}

export type RiskTier = 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL';

export interface AnalysisResult {
  portfolio: Portfolio;
  concentration: ConcentrationRisk;
  volatility: VolatilityResult;
  report: string;
  proofs: ProofEntry[];
}

export interface ProofEntry {
  type: string;
  timestamp: string;
  transaction_hash?: string;
  tee_signature?: string;
  tee_timestamp?: number;
  payment_hash?: string;
  model?: string;
  settlement_mode?: string;
  inference_mode?: string;
  model_cid?: string;
  source?: string;
  chain?: string;
  verified?: boolean;
  note?: string;
}
