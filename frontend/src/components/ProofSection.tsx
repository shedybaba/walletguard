import { useState } from 'react';
import type { ProofEntry } from '../types';

interface ProofSectionProps {
  proofs: ProofEntry[];
}

function truncateHash(hash: string): string {
  if (hash.length <= 16) return hash;
  return `${hash.slice(0, 10)}...${hash.slice(-6)}`;
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <button
      onClick={handleCopy}
      className="ml-2 text-text-muted hover:text-brand-400 transition-colors shrink-0"
      title="Copy to clipboard"
    >
      {copied ? (
        <svg className="w-3.5 h-3.5 text-risk-low" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
        </svg>
      ) : (
        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <rect x="9" y="9" width="13" height="13" rx="2" />
          <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1" />
        </svg>
      )}
    </button>
  );
}

function ProofRow({ label, value, copyable }: { label: string; value: string; copyable?: boolean }) {
  return (
    <div className="flex items-center gap-3 py-1.5">
      <span className="text-text-muted text-xs w-20 shrink-0 uppercase tracking-wider">{label}</span>
      <span className="font-mono text-xs text-text-secondary truncate">{copyable ? truncateHash(value) : value}</span>
      {copyable && <CopyButton text={value} />}
    </div>
  );
}

function StatusBadge({ verified }: { verified: boolean }) {
  if (verified) {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-risk-low/10 text-risk-low text-xs font-medium">
        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
        </svg>
        Verified
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-risk-moderate/10 text-risk-moderate text-xs font-medium">
      <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01" />
      </svg>
      Local
    </span>
  );
}

export default function ProofSection({ proofs }: ProofSectionProps) {
  const hasVerified = proofs.some(p => p.verified);

  return (
    <div className="glass-card rounded-2xl p-6 animate-slide-up" style={{ animationDelay: '0.2s' }}>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-brand-500/10 flex items-center justify-center">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#818cf8" strokeWidth="2">
              <path d="M12 2L3 7v5c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-9-5z" />
            </svg>
          </div>
          <h2 className="text-lg font-semibold">Verification Proofs</h2>
        </div>
        {hasVerified ? (
          <span className="px-3 py-1 rounded-full text-xs font-medium bg-risk-low/10 text-risk-low">
            Cryptographically Verified
          </span>
        ) : (
          <span className="px-3 py-1 rounded-full text-xs font-medium bg-risk-moderate/10 text-risk-moderate">
            Local Mode
          </span>
        )}
      </div>

      <div className="space-y-3">
        {proofs.map((proof, i) => (
          <div
            key={i}
            className="relative rounded-xl bg-white/[0.02] border border-white/[0.05] p-4
                       hover:bg-white/[0.03] hover:border-white/[0.08] transition-all duration-200
                       animate-scale-in"
            style={{ animationDelay: `${0.2 + i * 0.08}s` }}
          >
            {/* Header row */}
            <div className="flex items-center justify-between mb-3">
              <span className="text-brand-300 text-sm font-medium">{proof.type}</span>
              <div className="flex items-center gap-2">
                {proof.verified !== undefined && <StatusBadge verified={proof.verified} />}
              </div>
            </div>

            {/* Data rows */}
            <div className="space-y-0.5">
              {proof.tee_signature && <ProofRow label="TEE Sig" value={proof.tee_signature} copyable />}
              {proof.transaction_hash && <ProofRow label="TX Hash" value={proof.transaction_hash} copyable />}
              {proof.payment_hash && <ProofRow label="Payment" value={proof.payment_hash} copyable />}
              {proof.model_cid && <ProofRow label="Model" value={proof.model_cid} copyable />}
              {proof.model && <ProofRow label="LLM" value={proof.model} />}
              {proof.settlement_mode && <ProofRow label="Settle" value={proof.settlement_mode} />}
              {proof.source && <ProofRow label="Source" value={proof.source} />}
              {proof.chain && <ProofRow label="Chain" value={proof.chain} />}
              {proof.inference_mode && <ProofRow label="Mode" value={proof.inference_mode} />}
            </div>

            {/* Note */}
            {proof.note && (
              <p className="mt-3 pt-3 border-t border-white/[0.04] text-text-muted text-xs leading-relaxed">
                {proof.note}
              </p>
            )}

            {/* Timestamp */}
            <div className="mt-2 text-right">
              <span className="text-text-muted text-[10px] font-mono">{proof.timestamp}</span>
            </div>
          </div>
        ))}
      </div>

      <p className="mt-5 text-text-muted text-[11px] text-center leading-relaxed">
        Proofs recorded on Base Sepolia via OpenGradient x402 protocol
      </p>
    </div>
  );
}
