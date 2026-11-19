export function GennoLogo({ className = "size-[26px]" }: { className?: string }) {
  return (
    <svg viewBox="0 0 48 48" fill="none" className={className} aria-label="Agent Genno logo">
      {/* orbit ring — the .ai identity layer */}
      <circle cx="24" cy="24" r="21" stroke="rgba(245,215,142,0.35)" strokeWidth="1.5" strokeDasharray="3 5" />
      {/* badge seal — soulbound credential */}
      <rect x="13" y="13" width="22" height="22" rx="6" transform="rotate(45 24 24)"
            fill="url(#gennoGold)" stroke="rgba(245,215,142,0.5)" strokeWidth="1" />
      {/* verified checkmark — the track record */}
      <path d="M17.5 24.5 L22 29 L31 19.5" stroke="#1a1d26" strokeWidth="3.2"
            strokeLinecap="round" strokeLinejoin="round" />
      {/* orbit nodes — other agents / attestors */}
      <circle cx="42.5" cy="15" r="2.4" fill="#5ee7a0" />
      <circle cx="6" cy="33" r="2" fill="rgba(255,255,255,0.55)" />
      <defs>
        <linearGradient id="gennoGold" x1="13" y1="13" x2="35" y2="35">
          <stop offset="0" stopColor="#f8e3a8" />
          <stop offset="1" stopColor="#e9b84c" />
        </linearGradient>
      </defs>
    </svg>
  );
}
