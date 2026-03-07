import { useState } from 'react';
import './index.css';
import type { AnalysisResult } from './types';
import { analyzeWallet } from './api';
import Header from './components/Header';
import WalletInput from './components/WalletInput';
import RiskScoreCard from './components/RiskScoreCard';
import HoldingsTable from './components/HoldingsTable';
import ProofSection from './components/ProofSection';
import LoadingState from './components/LoadingState';

export default function App() {
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleAnalyze = async (address: string) => {
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const data = await analyzeWallet(address);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-surface relative">
      {/* Mesh gradient background */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute -top-[30%] -left-[10%] w-[60%] h-[60%] rounded-full bg-brand-600/[0.06] blur-[120px]" />
        <div className="absolute -bottom-[20%] -right-[10%] w-[50%] h-[50%] rounded-full bg-accent-cyan/[0.04] blur-[120px]" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[40%] h-[30%] rounded-full bg-brand-400/[0.02] blur-[100px]" />
      </div>

      {/* Content */}
      <div className="relative z-10 max-w-5xl mx-auto px-4 sm:px-6 pb-24">
        <Header />
        <WalletInput onSubmit={handleAnalyze} loading={loading} />

        {loading && <LoadingState />}

        {error && (
          <div className="max-w-2xl mx-auto mb-8 animate-slide-up">
            <div className="glass-card rounded-xl px-5 py-4 border-risk-critical/20">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-risk-critical/10 flex items-center justify-center shrink-0">
                  <svg className="w-4 h-4 text-risk-critical" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <circle cx="12" cy="12" r="10" />
                    <path strokeLinecap="round" d="M12 8v4m0 4h.01" />
                  </svg>
                </div>
                <p className="text-risk-critical text-sm">{error}</p>
              </div>
            </div>
          </div>
        )}

        {result && !loading && (
          <div className="animate-fade-in space-y-6">
            {/* Risk Score + Holdings */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <RiskScoreCard
                volatility={result.volatility}
                concentration={result.concentration}
              />
              <HoldingsTable portfolio={result.portfolio} />
            </div>

            {/* AI Report */}
            {result.report && (
              <div className="glass-card rounded-2xl p-6 animate-slide-up" style={{ animationDelay: '0.15s' }}>
                <div className="flex items-center gap-3 mb-5">
                  <div className="w-8 h-8 rounded-lg bg-accent-cyan/10 flex items-center justify-center">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#06b6d4" strokeWidth="2">
                      <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2" strokeLinecap="round" />
                      <rect x="9" y="3" width="6" height="4" rx="1" />
                      <path d="M9 12h6m-6 4h4" strokeLinecap="round" />
                    </svg>
                  </div>
                  <h2 className="text-lg font-semibold">AI Risk Report</h2>
                  <span className="ml-auto px-3 py-1 rounded-full text-[11px] font-medium bg-accent-cyan/10 text-accent-cyan">
                    GPT-4.1 via TEE
                  </span>
                </div>
                <div className="text-text-secondary text-sm leading-relaxed whitespace-pre-wrap"
                     style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '12.5px', lineHeight: '1.8' }}>
                  {result.report}
                </div>
              </div>
            )}

            {/* Proofs */}
            <ProofSection proofs={result.proofs} />
          </div>
        )}

        {/* Empty state */}
        {!result && !loading && !error && (
          <div className="text-center py-24 animate-fade-in">
            <div className="relative inline-block mb-6">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" className="opacity-20">
                <path
                  d="M12 2L3 7v5c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-9-5z"
                  stroke="currentColor"
                  strokeWidth="1"
                />
              </svg>
            </div>
            <p className="text-text-muted text-sm">
              Enter a wallet address to get a verified risk analysis
            </p>
          </div>
        )}

        {/* Footer */}
        <footer className="mt-16 pt-8 border-t border-white/[0.04] text-center">
          <p className="text-text-muted text-xs">
            Built on <span className="text-brand-400">OpenGradient</span> &middot; TEE-Verified AI &middot; x402 Settlement
          </p>
        </footer>
      </div>
    </div>
  );
}
