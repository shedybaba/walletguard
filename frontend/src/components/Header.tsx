export default function Header() {
  return (
    <header className="relative pt-20 pb-12 text-center">
      {/* Shield icon with glow */}
      <div className="relative inline-block mb-6 animate-float">
        <svg width="56" height="56" viewBox="0 0 24 24" fill="none" className="relative z-10">
          <path
            d="M12 2L3 7v5c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-9-5z"
            fill="url(#shg)"
            opacity="0.12"
          />
          <path
            d="M12 2L3 7v5c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-9-5z"
            stroke="url(#shg)"
            strokeWidth="1.5"
            fill="none"
          />
          <path d="M9 12l2 2 4-4" stroke="#22c55e" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          <defs>
            <linearGradient id="shg" x1="3" y1="2" x2="21" y2="24">
              <stop stopColor="#818cf8" />
              <stop offset="1" stopColor="#06b6d4" />
            </linearGradient>
          </defs>
        </svg>
        <div className="absolute inset-0 rounded-full bg-brand-500/30 blur-2xl animate-pulse-glow" />
      </div>

      {/* Title */}
      <h1 className="text-5xl sm:text-6xl font-extrabold tracking-tight mb-4">
        <span className="gradient-text">Wallet</span>
        <span className="text-text-primary">Guard</span>
      </h1>

      {/* Subtitle */}
      <p className="text-text-secondary text-base sm:text-lg max-w-lg mx-auto leading-relaxed mb-8">
        AI-powered wallet risk scoring with cryptographic proof.
        <br className="hidden sm:block" />
        Every analysis is TEE-verified and settled on-chain.
      </p>

      {/* Feature pills */}
      <div className="flex flex-wrap items-center justify-center gap-3">
        {[
          { label: 'TEE-Verified LLM', color: 'bg-risk-low' },
          { label: 'ONNX Model Hub', color: 'bg-brand-400' },
          { label: 'x402 Settlement', color: 'bg-accent-cyan' },
        ].map((f) => (
          <span
            key={f.label}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass-card text-xs sm:text-sm text-text-secondary"
          >
            <span className={`w-1.5 h-1.5 rounded-full ${f.color}`} />
            {f.label}
          </span>
        ))}
      </div>
    </header>
  );
}
