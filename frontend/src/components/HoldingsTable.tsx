import type { Portfolio } from '../types';

interface HoldingsTableProps {
  portfolio: Portfolio;
}

function formatUsd(value: number): string {
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(2)}M`;
  if (value >= 1_000) return `$${(value / 1_000).toFixed(1)}K`;
  return `$${value.toFixed(2)}`;
}

const TOKEN_COLORS: Record<string, string> = {
  ETH: '#627eea', BTC: '#f7931a', USDC: '#2775ca', USDT: '#26a17b',
  STETH: '#00a3ff', UNI: '#ff007a', LINK: '#2a5ada', AAVE: '#b6509e',
  PEPE: '#4ca843', SHIB: '#ffa409', DOGE: '#c2a633', ARB: '#28a0f0',
  SOL: '#9945ff', DAI: '#f5ac37', GHO: '#8b5cf6', WBTC: '#f7931a',
};

export default function HoldingsTable({ portfolio }: HoldingsTableProps) {
  const maxPct = Math.max(...portfolio.holdings.map((h) => h.pct), 1);

  return (
    <div className="glass-card rounded-2xl p-6 animate-slide-up" style={{ animationDelay: '0.08s' }}>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold">Holdings</h2>
        <div className="flex items-baseline gap-2">
          <span className="text-text-primary text-base font-semibold font-mono tabular-nums">
            {formatUsd(portfolio.total_usd)}
          </span>
          <span className="text-text-muted text-xs">
            {portfolio.holdings.length} assets
          </span>
        </div>
      </div>

      <div className="space-y-1">
        {portfolio.holdings.map((h, i) => {
          const tokenColor = TOKEN_COLORS[h.symbol] || '#6366f1';
          return (
            <div
              key={h.symbol}
              className="group flex items-center gap-3 px-3 py-2.5 -mx-3 rounded-xl
                         hover:bg-white/[0.03] transition-colors duration-200
                         animate-fade-in"
              style={{ animationDelay: `${i * 0.04}s` }}
            >
              {/* Token icon */}
              <div
                className="w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold text-white shrink-0
                           ring-1 ring-white/10"
                style={{ backgroundColor: tokenColor }}
              >
                {h.symbol.slice(0, 2)}
              </div>

              {/* Token info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <span className="text-text-primary font-medium text-sm">{h.symbol}</span>
                    <span className="text-text-muted text-xs hidden sm:inline truncate max-w-[120px]">{h.name}</span>
                  </div>
                  <div className="text-right flex items-baseline gap-2">
                    <span className="text-text-primary text-sm font-mono tabular-nums">{formatUsd(h.usd_value)}</span>
                    <span className="text-text-muted text-xs font-mono tabular-nums w-12 text-right">{h.pct.toFixed(1)}%</span>
                  </div>
                </div>

                {/* Bar */}
                <div className="h-1 bg-white/[0.04] rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-700 ease-out"
                    style={{
                      width: `${Math.max(1, (h.pct / maxPct) * 100)}%`,
                      backgroundColor: tokenColor,
                      opacity: 0.7,
                    }}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Wallet address footer */}
      <div className="mt-5 pt-4 border-t border-white/[0.06] flex items-center justify-between">
        <span className="text-text-muted text-xs">Wallet</span>
        <span className="text-text-muted text-xs font-mono">
          {portfolio.address.slice(0, 6)}...{portfolio.address.slice(-4)}
        </span>
      </div>
    </div>
  );
}
