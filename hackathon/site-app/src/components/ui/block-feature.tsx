import { useEffect, useState, type ReactNode } from "react";
import {
  BadgeCheck, Stamp, Database, FileCode2, Boxes, Wallet,
  BadgeCheck as BadgeIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";

/* ------------------------------ | PRIMITIVES | ------------------------------ */

export function Card({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <article
      className={cn(
        "relative flex min-h-[288px] flex-col overflow-hidden rounded-[20px] border border-white/10 bg-card/80 shadow-[0_1px_2px_rgba(16,24,40,0.2)] backdrop-blur-sm",
        className,
      )}
    >
      {children}
    </article>
  );
}

export function Title({ children }: { children: ReactNode }) {
  return (
    <h3 className="px-6 text-center text-[20px] leading-7 font-medium text-foreground">
      {children}
    </h3>
  );
}

/* ------------------------------ | CARD 1 — REGISTRY GRID | ------------------------------ */

function RegistryGrid() {
  const cols = 5;
  const rows = 3;
  const highlight = 1 * cols + 2;
  return (
    <div className="relative flex-1">
      <div className="absolute inset-0 flex items-center justify-center overflow-hidden">
        <div
          className="grid [mask-image:radial-gradient(ellipse_75%_75%_at_50%_50%,#000_35%,transparent_88%)]"
          style={{ gridTemplateColumns: `repeat(${cols}, 72px)`, gridTemplateRows: `repeat(${rows}, 72px)` }}
        >
          {Array.from({ length: cols * rows }).map((_, i) => (
            <div
              key={i}
              className={cn(
                "flex size-[72px] items-center justify-center border border-white/10",
                i === highlight && "bg-amber-100/10",
              )}
            >
              {i === highlight && <BadgeIcon className="size-9 text-amber-200" />}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ------------------------------ | CARD 3 — IDENTITY ORBIT | ------------------------------ */

function IdentityOrbit() {
  return (
    <div className="relative flex-1">
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="relative h-[122px] w-[229px] shrink-0">
          <svg viewBox="0 0 229 109" className="absolute top-[13px] left-0 h-[109px] w-[229px]" fill="none">
            <ellipse cx="114.5" cy="54.5" rx="110" ry="50" stroke="rgba(255,255,255,.25)" strokeDasharray="4 6" />
            <circle cx="14" cy="70" r="5" fill="#f5d78e" />
            <circle cx="212" cy="36" r="4" fill="#5ee7a0" />
          </svg>
          <div className="absolute top-0 left-1/2 flex h-[93px] w-[93px] -translate-x-1/2 items-center justify-center rounded-[24px] bg-white/10 border border-white/20 backdrop-blur-sm">
            <BadgeCheck className="size-12 text-amber-200" />
          </div>
          <Stamp className="absolute top-[68px] left-[188px] size-[15px] text-white/80" />
          <Boxes className="absolute top-[100px] left-[30px] size-[13px] text-white/70" />
        </div>
      </div>
    </div>
  );
}

/* ------------------------------ | CARD 4 — CODE EDITOR | ------------------------------ */

function CodeEditor() {
  const lines: ReactNode[] = [
    <>
      <span className="text-violet-400">function </span>
      <span className="text-sky-400">claimBadge</span>
      <span className="text-white/80">(uint256 questId) external {"{"}</span>
    </>,
    <>
      {"  "}
      <span className="text-violet-400">if</span>
      <span className="text-white/80"> (registry.</span>
      <span className="text-sky-400">balanceOf</span>
      <span className="text-white/80">(msg.sender) == 0)</span>
    </>,
    <>
      {"    "}
      <span className="text-rose-400">revert</span>
      <span className="text-white/80"> NotAgentIdHolder();</span>
    </>,
    <>
      {"  "}
      <span className="text-rose-400">_mint</span>
      <span className="text-white/80">(msg.sender, ++_nextTokenId);</span>
    </>,
    <>
      {"  "}
      <span className="text-emerald-400">emit</span>
      <span className="text-white/80"> BadgeClaimed(…handleOf(msg.sender));</span>
    </>,
    <>
      {"}"}
    </>,
  ];

  return (
    <div className="relative flex-1">
      <div aria-hidden="true" className="absolute right-6 bottom-2 left-6 h-40 rounded-3xl bg-amber-200/10 blur-2xl" />
      <div className="absolute right-4 -bottom-6 left-[-14px] overflow-hidden rounded-2xl border border-b-0 border-white/10 bg-[#0d1220] shadow-[0_-8px_30px_rgba(0,0,0,0.35)]">
        <div className="flex items-center justify-between px-4 py-3 pl-6">
          <div className="flex items-center gap-4">
            <div className="flex gap-1.5">
              <span className="size-2.5 rounded-full bg-red-400" />
              <span className="size-2.5 rounded-full bg-amber-400" />
              <span className="size-2.5 rounded-full bg-green-400" />
            </div>
            <span className="text-xs text-muted-foreground">AgentBadge.sol</span>
          </div>
          <span className="text-xs text-muted-foreground">solidity 0.8.24 · verified</span>
        </div>
        <div className="border-t border-white/10" />
        <pre className="overflow-hidden px-5 py-4 font-mono text-[13px] leading-6 text-foreground">
          {lines.map((line, i) => (
            <div key={i} className="whitespace-pre">{line}</div>
          ))}
        </pre>
      </div>
    </div>
  );
}

/* ------------------------------ | CARD 5 — ECOSYSTEM BELT | ------------------------------ */

const BELT_PATH = "M-40 172C20 172 55 112 185.5 112C316 112 351 172 411 172";
const BELT_DURATION = 22;
const BELT_RIDERS = 6;

const beltIcons = [
  { name: "agent id", node: <BadgeCheck className="size-7 text-amber-200" />, bg: "bg-neutral-950 border border-amber-200/30" },
  { name: "baw", node: <Wallet className="size-7 text-white" />, bg: "bg-[#F0B90B]" },
  { name: "skill.md", node: <FileCode2 className="size-7 text-white" />, bg: "bg-neutral-950 border border-white/20" },
  { name: "attest", node: <Stamp className="size-7 text-white" />, bg: "bg-[#38BDF8]" },
  { name: "read layer", node: <Database className="size-7 text-white" />, bg: "bg-neutral-950 border border-white/20" },
  { name: "dapps", node: <Boxes className="size-7 text-white" />, bg: "bg-[#5EE7A0]" },
];

function TechBelt() {
  const step = BELT_DURATION / BELT_RIDERS;
  return (
    <div className="relative flex-1">
      <svg viewBox="0 0 371 258" fill="none" preserveAspectRatio="xMidYMid slice" aria-hidden="true"
           className="absolute inset-0 h-full w-full motion-reduce:hidden">
        {Array.from({ length: BELT_RIDERS }).map((_, i) => {
          const icon = beltIcons[i % beltIcons.length];
          return (
            <g key={`${icon.name}-${i}`}>
              <animateMotion dur={`${BELT_DURATION}s`} begin={`${-i * step}s`} repeatCount="indefinite"
                             calcMode="linear" rotate="auto" path={BELT_PATH} />
              <foreignObject x="-30" y="-30" width="60" height="60" className="overflow-visible">
                <div className={cn("flex size-[65px] items-center justify-center rounded-[18px] shadow-[0_16px_32px_rgba(0,0,0,0.35)]", icon.bg)}>
                  {icon.node}
                </div>
              </foreignObject>
            </g>
          );
        })}
      </svg>
      <div aria-hidden="true" className="absolute inset-0 hidden items-center justify-center gap-3 motion-reduce:flex">
        {beltIcons.map((icon) => (
          <div key={icon.name} className={cn("flex size-[52px] items-center justify-center rounded-[16px] shadow-md", icon.bg)}>
            {icon.node}
          </div>
        ))}
      </div>
    </div>
  );
}

/* ------------------------------ | CARD 2 — AGENT TERMINAL | ------------------------------ */

const TERM_LINES = [
  { t: 400, c: "text-sky-400", x: '> Read my skill for "Agent Genno" (skill.md). Do the preflight checks, then preview claimBadge(1).' },
  { t: 1500, c: "text-white/50", x: "reading skill.md … preflight required" },
  { t: 2100, c: "text-white/50", x: "$ baw wallet status" },
  { t: 2600, c: "text-emerald-400", x: "  ✓ wallet unlocked · network: BNB Smart Chain (56)" },
  { t: 3100, c: "text-white/50", x: "$ baw wallet agent-id" },
  { t: 3600, c: "text-emerald-400", x: "  ✓ Agent ID: yourname.ai (soulbound · holder)" },
  { t: 4600, c: "text-white/50", x: '$ baw wallet contract-call preview --data "claimBadge(uint256)" --args 1' },
  { t: 5600, c: "text-emerald-400", x: "  ✓ preview OK · requestId: 8f4c21e0-…" },
  { t: 6100, c: "text-white/50", x: "  action: mint 1 soulbound badge · value: 0 BNB · fee: gas only" },
  { t: 6600, c: "text-amber-300", x: "  ⏳ waiting for USER confirmation in Binance Wallet …" },
  { t: 7900, c: "text-emerald-400", x: "  ✓ USER CONFIRMED in wallet" },
  { t: 8700, c: "text-emerald-400", x: "  ✓ BadgeClaimed(yourname.ai, quest #1, badge #27)" },
];

function AgentTerminal() {
  const [shown, setShown] = useState(0);
  useEffect(() => {
    const timers = TERM_LINES.map((l, i) => setTimeout(() => setShown(i + 1), l.t));
    return () => timers.forEach(clearTimeout);
  }, []);
  return (
    <div className="relative flex-1 px-6 pb-6">
      <div className="rounded-2xl border border-white/10 bg-[#0a0f1c] overflow-hidden">
        <div className="flex items-center justify-between px-4 py-2.5 border-b border-white/10">
          <div className="flex gap-1.5">
            <span className="size-2.5 rounded-full bg-red-400" />
            <span className="size-2.5 rounded-full bg-amber-400" />
            <span className="size-2.5 rounded-full bg-green-400" />
          </div>
          <span className="text-xs text-muted-foreground">agent session — preview → confirm → execute</span>
        </div>
        <div className="px-4 py-3 font-mono text-[12.5px] leading-6 min-h-[232px]">
          {TERM_LINES.slice(0, shown).map((l, i) => (
            <div key={i} className={cn("whitespace-pre-wrap", l.c)}>{l.x}</div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ------------------------------ | FEATURE | ------------------------------ */

export default function Feature() {
  return (
    <section className="px-4 py-10 sm:px-8">
      <div className="mx-auto flex w-full max-w-[1200px] flex-col gap-5">
        <div className="grid gap-5 lg:grid-cols-[1fr_1.25fr_1fr]">
          <Card className="pt-8">
            <Title>gated by the Agent ID registry — verifiable, on-chain</Title>
            <RegistryGrid />
          </Card>

          <Card className="pt-6">
            <h3 className="sr-only">agent flow: preflight, preview, confirm, mint</h3>
            <div className="px-6 pb-2 text-center text-[20px] leading-7 font-medium">your agent does the work. you stay in control.</div>
            <AgentTerminal />
          </Card>

          <Card className="pb-7">
            <IdentityOrbit />
            <Title>badges bind to your .ai identity — portable, readable by every dapp</Title>
          </Card>
        </div>

        <div className="grid gap-5 lg:grid-cols-3">
          <Card className="min-h-[264px] pt-6">
            <Title>full control over your keys. zero lock-in.</Title>
            <CodeEditor />
          </Card>

          <Card className="min-h-[264px]">
            <h3 className="sr-only">works with agent id, baw, skill.md, attestations, read layer, dapps</h3>
            <TechBelt />
          </Card>

          <Card className="min-h-[264px]">
            <h3 className="sr-only">no owner, zero approvals, immutable</h3>
            <div className="flex flex-1 flex-col items-center justify-center gap-3 px-8 text-center">
              <Wallet className="size-10 text-amber-200" />
              <div className="text-[20px] leading-7 font-medium">no owner · no fees · zero approvals</div>
              <div className="text-sm text-muted-foreground">immutable registry reference · mit licensed · verified on bscscan</div>
            </div>
          </Card>
        </div>
      </div>
    </section>
  );
}
