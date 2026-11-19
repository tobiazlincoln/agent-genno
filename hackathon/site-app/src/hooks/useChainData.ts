import { useEffect, useState } from "react";

const RPCS = [
  "https://bsc.publicnode.com",
  "https://bsc-dataseed.binance.org",
  "https://binance.llamarpc.com",
];
let rpcIdx = 0;

async function eth(method: string, params: unknown[]) {
  for (let i = 0; i < RPCS.length; i++) {
    const url = RPCS[(rpcIdx + i) % RPCS.length];
    try {
      const r = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ jsonrpc: "2.0", id: 1, method, params }),
      });
      const j = await r.json();
      if (j.result !== undefined) {
        rpcIdx = (rpcIdx + i) % RPCS.length;
        return j.result as unknown;
      }
      if (j.error && !/limit/i.test(j.error.message ?? "")) throw new Error(j.error.message);
    } catch {
      /* try next rpc */
    }
  }
  throw new Error("all rpcs failed");
}

const CONTRACT = "0xD6ED0279E381612e32F1Fa9DD7f5329bC1c6b811";
const DEPLOY_BLOCK = 134452670;
const SEL = { uniqueAgents: "8b5bca1e", totalBadges: "a490a697", questClaimCount: "4516f432" };
const TOPIC_CLAIMED = "0xd0a8a075deace9291b01be18a2c8f6c8ac4ff7e5280495cd89cd09b663d0771c";

const call = (data: string) => eth("eth_call", [{ to: CONTRACT, data }, "latest"]);
const num = (h: unknown) => parseInt(h as string, 16);
const pad64 = (n: number) => n.toString(16).padStart(64, "0");
function decodeStr(data: string) {
  const hex = data.slice(2);
  const len = parseInt(hex.slice(64, 128), 16);
  if (!len) return "";
  const raw = hex.slice(128, 128 + len * 2);
  let s = "";
  for (let i = 0; i < raw.length; i += 2) s += String.fromCharCode(parseInt(raw.substr(i, 2), 16));
  return s;
}

export interface ClaimRow {
  badge: number;
  quest: number;
  handle: string;
  when: string;
}

export function useChainData() {
  const [stats, setStats] = useState({ unique: 0, total: 0, quest1: 0 });
  const [rows, setRows] = useState<ClaimRow[]>([]);
  const [status, setStatus] = useState<"loading" | "live" | "error">("loading");

  useEffect(() => {
    let alive = true;
    async function load() {
      try {
        const [uni, tot, q1] = await Promise.all([
          call("0x" + SEL.uniqueAgents),
          call("0x" + SEL.totalBadges),
          call("0x" + SEL.questClaimCount + pad64(1)),
        ]);
        const logs = (await eth("eth_getLogs", [{
          address: CONTRACT,
          fromBlock: "0x" + DEPLOY_BLOCK.toString(16),
          toBlock: "latest",
          topics: [TOPIC_CLAIMED],
        }])) as Array<{ topics: string[]; data: string; blockNumber: string }>;

        const recent = logs.slice(-20).reverse();
        const out: ClaimRow[] = [];
        for (const log of recent) {
          const badge = parseInt(log.topics[3], 16);
          const quest = parseInt(log.topics[2], 16);
          const handle = decodeStr(log.data) || "unknown";
          let when = "";
          try {
            const blk = (await eth("eth_getBlockByNumber", [log.blockNumber, false])) as { timestamp: string };
            when = new Date(parseInt(blk.timestamp, 16) * 1000).toLocaleString([], {
              month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
            });
          } catch { /* skip timestamp */ }
          out.push({ badge, quest, handle, when });
        }
        if (!alive) return;
        setStats({ unique: num(uni), total: num(tot), quest1: num(q1) });
        setRows(out);
        setStatus("live");
      } catch {
        if (alive) setStatus("error");
      }
    }
    load();
    const t = setInterval(load, 15000);
    return () => { alive = false; clearInterval(t); };
  }, []);

  return { stats, rows, status };
}
