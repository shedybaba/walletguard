import { useState } from 'react';

interface WalletInputProps {
  onSubmit: (address: string) => void;
  loading: boolean;
}

export default function WalletInput({ onSubmit, loading }: WalletInputProps) {
  const [address, setAddress] = useState('');
  const [error, setError] = useState('');
  const [focused, setFocused] = useState(false);

  const validate = (addr: string) => {
    if (!addr) return 'Enter a wallet address';
    if (!addr.startsWith('0x')) return 'Address must start with 0x';
    if (addr.length !== 42) return 'Address must be 42 characters';
    if (!/^0x[0-9a-fA-F]{40}$/.test(addr)) return 'Invalid hex characters';
    return '';
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const err = validate(address);
    if (err) {
      setError(err);
      return;
    }
    setError('');
    onSubmit(address);
  };

  return (
    <div className="max-w-2xl mx-auto mb-12">
      <form onSubmit={handleSubmit}>
        <div
          className={`relative rounded-2xl p-[1px] transition-all duration-300 ${
            focused
              ? 'bg-gradient-to-r from-brand-500/50 via-accent-cyan/50 to-brand-500/50'
              : 'bg-glass-border'
          }`}
        >
          {/* Glow behind input when focused */}
          {focused && (
            <div className="absolute -inset-1 rounded-2xl bg-brand-500/10 blur-xl pointer-events-none" />
          )}

          <div className="relative flex gap-2 p-2 rounded-2xl bg-surface-raised">
            <div className="flex-1 relative">
              <div className="absolute left-4 top-1/2 -translate-y-1/2 text-text-muted pointer-events-none">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="11" cy="11" r="8" />
                  <path d="M21 21l-4.35-4.35" strokeLinecap="round" />
                </svg>
              </div>
              <input
                type="text"
                value={address}
                onChange={(e) => { setAddress(e.target.value); setError(''); }}
                onFocus={() => setFocused(true)}
                onBlur={() => setFocused(false)}
                placeholder="Enter Ethereum wallet address (0x...)"
                disabled={loading}
                className="w-full pl-11 pr-4 py-4 bg-transparent
                           text-text-primary placeholder:text-text-muted font-mono text-sm
                           focus:outline-none disabled:opacity-50 transition-all"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="px-8 py-4 bg-gradient-to-r from-brand-600 to-brand-500 hover:from-brand-500 hover:to-brand-400
                         text-white font-semibold rounded-xl
                         transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed
                         hover:shadow-lg hover:shadow-brand-500/20 active:scale-[0.98]
                         shrink-0"
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Scanning
                </span>
              ) : (
                <span className="flex items-center gap-2">
                  Analyze
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
                    <path d="M5 12h14M12 5l7 7-7 7" />
                  </svg>
                </span>
              )}
            </button>
          </div>
        </div>

        {error && (
          <p className="mt-3 ml-4 text-risk-critical text-xs flex items-center gap-1.5">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <path d="M12 8v4m0 4h.01" strokeLinecap="round" />
            </svg>
            {error}
          </p>
        )}
      </form>
    </div>
  );
}
