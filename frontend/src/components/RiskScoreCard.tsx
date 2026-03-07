import type { RiskTier, VolatilityResult, ConcentrationRisk } from '../types';

interface RiskScoreCardProps {
  volatility: VolatilityResult;
  concentration: ConcentrationRisk;
}

const TIER_CONFIG: Record<RiskTier, { color: string; bg: string; label: string; stroke: string; glow: string }> = {
  LOW:      { color: 'text-risk-low',      bg: 'bg-risk-low/10',      label: 'Low Risk',      stroke: '#22c55e', glow: 'rgba(34,197,94,0.15)' },
  MODERATE: { color: 'text-risk-moderate',  bg: 'bg-risk-moderate/10', label: 'Moderate Risk', stroke: '#f59e0b', glow: 'rgba(245,158,11,0.15)' },
  HIGH:     { color: 'text-risk-high',      bg: 'bg-risk-high/10',     label: 'High Risk',     stroke: '#f97316', glow: 'rgba(249,115,22,0.15)' },
  CRITICAL: { color: 'text-risk-critical',  bg: 'bg-risk-critical/10', label: 'Critical Risk', stroke: '#ef4444', glow: 'rgba(239,68,68,0.15)' },
};

function ScoreArc({ score, tier }: { score: number; tier: RiskTier }) {
  const radius = 58;
  const circumference = 2 * Math.PI * radius;
  const progress = (score / 100) * circumference;
  const offset = circumference - progress;
  const tierCfg = TIER_CONFIG[tier];

  return (
    <div className="relative inline-flex items-center justify-center">
      {/* Glow ring */}
      <div
        className="absolute inset-0 rounded-full blur-xl opacity-60"
        style={{ background: tierCfg.glow }}
      />
      <svg width="160" height="160" className="-rotate-90 relative z-10">
        {/* Track */}
        <circle cx="80" cy="80" r={radius} fill="none" stroke="rgba(255,255,255,0.04)" strokeWidth="10" />
        {/* Progress */}
        <circle
          cx="80" cy="80" r={radius} fill="none"
          stroke={tierCfg.stroke} strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 1.2s cubic-bezier(0.16, 1, 0.3, 1)' }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center z-10">
        <span className={`text-4xl font-bold tabular-nums ${tierCfg.color}`}>{Math.round(score)}</span>
        <span className="text-text-muted text-xs mt-0.5">/100</span>
      </div>
    </div>
  );
}

function MetricBar({ label, value, max = 100, unit = '' }: { label: string; value: number; max?: number; unit?: string }) {
  const pct = Math.min(100, (value / max) * 100);
  return (
    <div>
      <div className="flex justify-between text-sm mb-2">
        <span className="text-text-muted">{label}</span>
        <span className="text-text-primary font-medium font-mono tabular-nums">{value.toFixed(1)}{unit}</span>
      </div>
      <div className="h-1.5 bg-white/[0.04] rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-1000 ease-out"
          style={{
            width: `${pct}%`,
            background: 'linear-gradient(90deg, #6366f1, #06b6d4)',
          }}
        />
      </div>
    </div>
  );
}

export default function RiskScoreCard({ volatility, concentration }: RiskScoreCardProps) {
  const tier = volatility.risk_tier;
  const tierCfg = TIER_CONFIG[tier];

  return (
    <div className="glass-card rounded-2xl p-6 animate-slide-up">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold">Risk Assessment</h2>
        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${tierCfg.color} ${tierCfg.bg}`}>
          {tierCfg.label}
        </span>
      </div>

      <div className="flex flex-col items-center mb-8">
        <ScoreArc score={volatility.composite_risk_score} tier={tier} />
      </div>

      <div className="space-y-5">
        <MetricBar label="Volatility Exposure" value={volatility.volatility_score} />
        <MetricBar label="Concentration (HHI)" value={concentration.hhi_index} max={1} />
        <MetricBar label="Diversification" value={concentration.diversification_score} />
      </div>

      <div className="mt-6 pt-5 border-t border-white/[0.06] grid grid-cols-2 gap-4">
        <div className="text-center">
          <div className="text-text-muted text-xs mb-1.5 uppercase tracking-wider">Top Asset</div>
          <div className="text-text-primary font-semibold text-lg">
            {concentration.top_asset.symbol}
          </div>
          <div className="text-text-muted text-xs">
            {concentration.top_asset.weight_pct.toFixed(1)}% of portfolio
          </div>
        </div>
        <div className="text-center">
          <div className="text-text-muted text-xs mb-1.5 uppercase tracking-wider">Effective Assets</div>
          <div className="text-text-primary font-semibold text-lg">
            {concentration.effective_num_assets.toFixed(1)}
          </div>
          <div className="text-text-muted text-xs">
            of {concentration.num_holdings} total
          </div>
        </div>
      </div>
    </div>
  );
}
