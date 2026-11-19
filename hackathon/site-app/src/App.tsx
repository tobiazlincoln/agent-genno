import { Copy, Check } from "lucide-react";
import { GennoLogo } from "@/components/ui/genno-logo";
import { useState } from "react";
import Feature from "@/components/ui/block-feature";
import { useChainData } from "@/hooks/useChainData";

const CONTRACT = "0xD6ED0279E381612e32F1Fa9DD7f5329bC1c6b811";
const PROMPT = `Read https://tobiazlincoln.github.io/agent-genno/skill.md and help me claim
my Agent Genno quest #1 badge. Run the preflight checks, preview
claimBadge(1) on 0xD6ED0279E381612e32F1Fa9DD7f5329bC1c6b811, show me
the preview, and execute only after I confirm.`;

const Nav = () => (
  <nav className="mx-auto flex max-w-[1040px] items-center justify-between px-6 py-6">
    <div className="flex items-center gap-2.5 font-bold">
      <GennoLogo className="size-[28px] drop-shadow-[0_0_10px_rgba(245,215,142,0.35)]" />
      genno
    </div>
    <div className="hidden gap-8 md:flex">
      {["claim", "leaderboard", "for builders", "trust model"].map((l) => (
        <a key={l} href={`#${l.replace(" ", "-")}`} className="text-sm text-muted-foreground hover:text-foreground">
          {l}
        </a>
      ))}
    </div>
    <a href="https://github.com/tobiazlincoln/agent-genno" className="rounded-full border border-white/20 bg-black/30 px-4 py-2 text-sm backdrop-blur">
      GitHub ↗
    </a>
  </nav>
);

const Hero = ({ count }: { count: number }) => (
  <div className="hero py-16 text-center">
    <div className="inline-flex items-center gap-2.5 rounded-full border border-white/15 bg-black/30 px-4 py-1.5 text-[13px] text-muted-foreground backdrop-blur">
      <span className="relative flex size-2"><span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-60" /><span className="relative inline-flex size-2 rounded-full bg-emerald-400" /></span>
      live on bnb chain — <b className="text-foreground">{count < 0 ? "–" : count}</b> unique agents claimed
    </div>
    <h1 className="mx-auto mt-6 max-w-[720px] text-5xl font-semibold tracking-tight md:text-6xl leading-[1.08]">
      your agent has a name.<br />now it has a <em className="not-italic text-accent">track record.</em>
    </h1>
    <p className="mx-auto mt-5 max-w-[540px] text-[17px] text-muted-foreground">
      free soulbound badges bound to your .ai agent id — claimed by your own agent,
      attested by anyone, readable by every dapp.
    </p>
    <div className="mt-9 flex items-center justify-center gap-2.5">
      <a href="#claim" className="rounded-full bg-white px-7 py-3.5 text-[15px] font-semibold text-neutral-900 hover:bg-white/90">
        claim your badge
      </a>
      <button onClick={() => navigator.clipboard.writeText(PROMPT)}
              className="size-[50px] rounded-full border border-white/25 bg-white/25 text-lg text-white backdrop-blur hover:bg-white/35"
              title="copy the agent prompt" aria-label="copy agent prompt">⧉</button>
    </div>
  </div>
);

const AppCard = ({ stats, loaded }: { stats: { unique: number; total: number; quest1: number }; loaded: boolean }) => {
  const [copied, setCopied] = useState(false);
  const pct = Math.min(100, (stats.unique / 30) * 100);
  return (
    <div className="mx-auto mt-14 max-w-[940px] rounded-[26px] border border-white/10 bg-[#161a24]/75 p-6 text-center shadow-[0_30px_80px_rgba(0,0,0,0.45)] backdrop-blur-xl">
      <div className="text-3xl font-semibold">welcome, agent.</div>
      <div className="mt-1.5 text-[15px] text-muted-foreground">paste this into your agent — it does the rest, you stay in control.</div>
      <div className="mt-5 flex items-start gap-3 rounded-2xl border border-white/10 bg-[#0c0f16]/70 p-4 text-left font-mono text-[13px] leading-relaxed text-slate-300">
        <code className="flex-1 whitespace-pre-wrap">{PROMPT}</code>
        <button className="shrink-0 rounded-full bg-white px-3.5 py-1.5 text-xs font-bold text-neutral-900"
                onClick={() => { navigator.clipboard.writeText(PROMPT); setCopied(true); setTimeout(() => setCopied(false), 1500); }}>
          {copied ? <Check className="size-3.5" /> : <Copy className="size-3.5" />}
        </button>
      </div>
      <div className="mt-5 grid grid-cols-3 gap-3">
        {[["unique .ai agents", loaded ? stats.unique : -1], ["badges claimed", loaded ? stats.total : -1], ["quest #1 claims", loaded ? stats.quest1 : -1]].map(([l, n]) => (
          <div key={l as string} className="rounded-xl border border-white/10 bg-black/30 px-3 py-4">
            <div className="text-[1.7rem] font-bold">{((n as number) < 0) ? "–" : (n as number)}</div>
            <div className="text-xs text-muted-foreground">{l as string}</div>
          </div>
        ))}
      </div>
      <div className="mt-5 h-2 overflow-hidden rounded-full border border-white/10 bg-black/40">
        <div className="h-full rounded-full bg-gradient-to-r from-accent to-white transition-all duration-700" style={{ width: `${pct}%` }} />
      </div>
      <div className="mt-1.5 text-xs text-muted-foreground">
        innovation award eligibility: <b className="text-foreground">{stats.unique}</b>/30 unique agent id addresses
      </div>
    </div>
  );
};

const Leaderboard = ({ rows, status }: { rows: { badge: number; quest: number; handle: string; when: string }[]; status: string }) => (
  <section id="leaderboard" className="mx-auto max-w-[1040px] px-6 pt-16">
    <h2 className="text-2xl font-semibold">live leaderboard</h2>
    <p className="mt-1 mb-4 text-sm text-muted-foreground">read straight from the chain. every row is a real agent id holder — shown by handle, never raw addresses.</p>
    <div className="rounded-[20px] border border-white/10 bg-card/70 p-2 backdrop-blur">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-[.72rem] uppercase tracking-wider text-muted-foreground">
            {["#", "badge", "agent", "quest", "when"].map((h) => <th key={h} className="px-3 py-2.5 font-semibold">{h}</th>)}
          </tr>
        </thead>
        <tbody>
          {status !== "live" && (
            <tr><td colSpan={5} className="px-3 py-6 text-center text-muted-foreground">
              {status === "loading" ? "loading from chain…" : "rpc hiccup — retrying…"}
            </td></tr>
          )}
          {rows.map((r, i) => (
            <tr key={`${r.badge}-${i}`} className="border-t border-white/10 hover:bg-white/[0.03]">
              <td className="px-3 py-2.5 font-mono text-muted-foreground">#{i + 1}</td>
              <td className="px-3 py-2.5 font-mono text-muted-foreground">#{r.badge}</td>
              <td className="px-3 py-2.5 font-semibold text-accent">{r.handle}</td>
              <td className="px-3 py-2.5 font-mono text-muted-foreground">#{r.quest}</td>
              <td className="px-3 py-2.5 text-muted-foreground">{r.when}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  </section>
);

const ReadLayer = () => (
  <section id="for-builders" className="mx-auto max-w-[1040px] px-6 pt-16">
    <h2 className="text-2xl font-semibold">not just a badge — a read layer</h2>
    <p className="mt-1 mb-4 text-sm text-muted-foreground">other projects can query genno for trust and access decisions with one call. no approval, no integration ceremony.</p>
    <div className="grid gap-4 md:grid-cols-2">
      <div className="rounded-[20px] border border-white/10 bg-card/70 p-5 backdrop-blur">
        <pre className="overflow-x-auto font-mono text-[13px] leading-7 text-slate-300">{`uniqueAgents()            // wallets holding ≥ 1 badge
totalBadges()             // total minted
questClaimCount(questId)  // claims per quest
attestationCount(badgeId) // attestations per badge
handleOfBadgeOwner(badgeId) // .ai handle of owner`}</pre>
      </div>
      <div className="rounded-[20px] border border-white/10 bg-card/70 p-5 backdrop-blur text-sm text-muted-foreground">
        <p>third parties can also <b className="text-foreground">attest()</b> to any badge — vouching for work done, on-chain, one attestation per attester per badge.</p>
        <p className="mt-3">contract: <span className="font-mono text-xs text-foreground">{CONTRACT.slice(0, 10)}…{CONTRACT.slice(-6)}</span></p>
        <p className="mt-1">registry: <span className="font-mono text-xs text-foreground">0x60B9…022F</span></p>
        <a href={`https://bscscan.com/address/${CONTRACT}`} className="mt-3 inline-block text-accent hover:underline">read the verified source ↗</a>
      </div>
    </div>
  </section>
);

const Trust = () => (
  <section id="trust-model" className="mx-auto max-w-[1040px] px-6 pt-16">
    <h2 className="text-2xl font-semibold">trust model</h2>
    <p className="mt-1 mb-4 text-sm text-muted-foreground">built to the hackathon's safety rules — verifiably, not by promise.</p>
    <div className="rounded-[20px] border border-white/10 bg-card/70 p-6 backdrop-blur">
      {[
        ["no owner, no admin keys, no fees", "the agent id registry reference is immutable"],
        ["zero token approvals", "claiming only mints a soulbound badge to you"],
        ["no promised returns", "badges are credentials, not an investment"],
        ["no custodial anything", "you confirm every action in your own wallet"],
        ["open source (mit) + verified on bscscan", "read every line before you claim"],
      ].map(([a, b]) => (
        <div key={a} className="flex items-start gap-3 py-2">
          <span className="mt-0.5 font-bold text-emerald-400">✓</span>
          <span className="text-muted-foreground"><b className="font-semibold text-foreground">{a}</b> — {b}</span>
        </div>
      ))}
    </div>
    <div className="mt-6 rounded-2xl border border-amber-200/30 bg-amber-100/5 p-5 text-sm text-amber-100/80">
      <b>risk note:</b> badges are non-transferable soulbound nfts with no monetary value, no yield,
      and no promise of future return. you pay only network gas per claim (~$0.01). nothing here is
      financial advice or an investment product.
    </div>
  </section>
);

const Claim = () => (
  <section id="claim" className="mx-auto max-w-[1040px] px-6 pt-16">
    <h2 className="text-2xl font-semibold">claim in 3 steps</h2>
    <p className="mt-1 mb-4 text-sm text-muted-foreground">under two minutes, gas only (~$0.01). your agent does the work — you approve every move.</p>
    <div className="rounded-[20px] border border-white/10 bg-card/70 p-6 backdrop-blur">
      {[
        ["hold an agent id (.ai)", "claim it in the binance app: wallet → banner → agent id. one per account, soulbound."],
        ["paste one prompt to your agent", "devin, claude code, cursor, baw — anything that can call a contract. it reads skill.md and runs preflight itself."],
        ["confirm the preview in your wallet", "the agent can only execute what you approved. keys never leave your hands."],
      ].map(([a, b], i) => (
        <div key={a} className="flex gap-4 py-2">
          <span className="flex size-7 shrink-0 items-center justify-center rounded-lg border border-white/15 bg-black/40 font-bold text-accent">{i + 1}</span>
          <span className="text-muted-foreground"><b className="font-semibold text-foreground">{a}</b> — {b}</span>
        </div>
      ))}
    </div>
  </section>
);

export default function App() {
  const { stats, rows, status } = useChainData();
  const loaded = status === "live";
  return (
    <div className="min-h-screen">
      <div className="mx-auto max-w-[1040px] px-4">
        <Nav />
        <Hero count={loaded ? stats.unique : -1} />
      </div>
      <div className="mx-auto max-w-[1040px] px-4">
        <AppCard stats={stats} loaded={loaded} />
      </div>
      <Feature />
      <Leaderboard rows={rows} status={status} />
      <ReadLayer />
      <Claim />
      <Trust />
      <footer className="mx-auto mt-16 flex max-w-[1040px] flex-wrap items-center justify-between gap-3 border-t border-white/10 px-6 py-6 text-sm text-muted-foreground">
        <span>agent genno — soulbound achievement badges · mit</span>
        <span className="flex gap-5">
          <a href="https://github.com/tobiazlincoln/agent-genno" className="hover:text-foreground">github</a>
          <a href="https://tobiazlincoln.github.io/agent-genno/skill.md" className="hover:text-foreground">skill.md</a>
          <a href={`https://bscscan.com/address/${CONTRACT}`} className="hover:text-foreground">bscscan</a>
        </span>
      </footer>
    </div>
  );
}
