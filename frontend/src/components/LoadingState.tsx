import { useEffect, useState } from 'react';

const STEPS = [
  { label: 'Scanning wallet on Ethereum', sublabel: 'Blockscout API' },
  { label: 'Computing risk metrics', sublabel: 'ONNX Model' },
  { label: 'Generating AI risk report', sublabel: 'TEE-Verified LLM' },
  { label: 'Settling on-chain proof', sublabel: 'x402 Protocol' },
];

export default function LoadingState() {
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentStep((prev) => (prev < STEPS.length - 1 ? prev + 1 : prev));
    }, 2800);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="max-w-md mx-auto py-20 animate-fade-in">
      {/* Pulsing shield */}
      <div className="flex justify-center mb-10">
        <div className="relative">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" className="relative z-10">
            <path
              d="M12 2L3 7v5c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-9-5z"
              stroke="url(#lg)"
              strokeWidth="1.5"
              fill="url(#lg)"
              fillOpacity="0.1"
            />
            <defs>
              <linearGradient id="lg" x1="3" y1="2" x2="21" y2="24">
                <stop stopColor="#818cf8" />
                <stop offset="1" stopColor="#06b6d4" />
              </linearGradient>
            </defs>
          </svg>
          <div className="absolute inset-0 rounded-full bg-brand-500/25 blur-xl animate-pulse-glow" />
        </div>
      </div>

      {/* Steps */}
      <div className="space-y-2">
        {STEPS.map((step, i) => {
          const isActive = i === currentStep;
          const isDone = i < currentStep;

          return (
            <div
              key={step.label}
              className={`flex items-center gap-4 px-5 py-3.5 rounded-xl transition-all duration-500 ${
                isActive
                  ? 'glass-card glow-brand'
                  : isDone
                  ? 'bg-white/[0.02] border border-white/[0.04]'
                  : 'bg-transparent border border-transparent opacity-40'
              }`}
            >
              {/* Icon */}
              <div className="w-7 h-7 flex items-center justify-center shrink-0">
                {isDone ? (
                  <div className="w-6 h-6 rounded-full bg-risk-low/15 flex items-center justify-center">
                    <svg className="w-3.5 h-3.5 text-risk-low" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                ) : isActive ? (
                  <svg className="w-5 h-5 animate-spin text-brand-400" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-20" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
                    <path className="opacity-80" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                ) : (
                  <div className="w-6 h-6 rounded-full border border-white/10 flex items-center justify-center">
                    <span className="text-text-muted text-xs">{i + 1}</span>
                  </div>
                )}
              </div>

              {/* Label */}
              <div className="flex-1">
                <span className={`text-sm ${isActive ? 'text-text-primary font-medium' : isDone ? 'text-text-secondary' : 'text-text-muted'}`}>
                  {step.label}
                </span>
                {isActive && (
                  <div className="text-brand-400/70 text-xs mt-0.5">{step.sublabel}</div>
                )}
              </div>

              {/* Progress dots for active */}
              {isActive && (
                <div className="flex gap-1">
                  <span className="w-1 h-1 bg-brand-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-1 h-1 bg-brand-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-1 h-1 bg-brand-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              )}
            </div>
          );
        })}
      </div>

      <p className="mt-10 text-text-muted text-xs text-center">
        All inferences verified in TEE and settled on-chain
      </p>
    </div>
  );
}
