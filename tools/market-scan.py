#!/usr/bin/env python3
"""Deterministic market + narrative scanner (CoinGecko + DefiLlama, no API key).

Fetches once, caches raw JSON, and writes a compact DIGEST.md so analysis reads
one small file instead of re-fetching.

  python3 tools/market-scan.py            # use cache younger than 6h
  python3 tools/market-scan.py --refresh  # force re-fetch
  python3 tools/market-scan.py --ttl 1    # cache TTL in hours
"""
import json, os, sys, time, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
OUT = os.environ.get('BRAIN_DIR') or os.path.join(ROOT, 'BRAIN', 'research', 'market')
os.makedirs(OUT, exist_ok=True)
UA = {'User-Agent': 'Mozilla/5.0 (research-scanner)', 'Accept': 'application/json'}
CG = 'https://api.coingecko.com/api/v3'
TTL = 6.0
if '--ttl' in sys.argv:
    TTL = float(sys.argv[sys.argv.index('--ttl') + 1])
REFRESH = '--refresh' in sys.argv

SOURCES = {
    'cg-global': f'{CG}/global',
    'cg-categories': f'{CG}/coins/categories',
    'cg-trending': f'{CG}/search/trending',
    'cg-solana-eco': f'{CG}/coins/markets?vs_currency=usd&category=solana-ecosystem&order=market_cap_desc'
                     '&per_page=250&page=1&price_change_percentage=24h,7d,30d',
    'cg-privacy': f'{CG}/coins/markets?vs_currency=usd&category=privacy-coins&order=market_cap_desc'
                  '&per_page=100&page=1&price_change_percentage=24h,7d,30d',
    'cg-pumpfun': f'{CG}/coins/markets?vs_currency=usd&category=pump-fun&order=market_cap_desc'
                  '&per_page=100&page=1&price_change_percentage=24h,7d,30d',
    'cg-ai-agents': f'{CG}/coins/markets?vs_currency=usd&category=ai-agents&order=market_cap_desc'
                    '&per_page=100&page=1&price_change_percentage=24h,7d,30d',
    'llama-chains': 'https://api.llama.fi/v2/chains',
    'llama-fees-solana': 'https://api.llama.fi/overview/fees/solana?excludeTotalDataChart=true'
                         '&excludeTotalDataChartBreakdown=true',
    'llama-dexs-solana': 'https://api.llama.fi/overview/dexs/solana?excludeTotalDataChart=true'
                         '&excludeTotalDataChartBreakdown=true',
    'llama-stables': 'https://stablecoins.llama.fi/stablecoinchains',
}


def get(name, url):
    path = os.path.join(OUT, name + '.json')
    if not REFRESH and os.path.exists(path) and time.time() - os.path.getmtime(path) < TTL * 3600:
        return json.load(open(path)), 'cache'
    for attempt in range(4):
        try:
            data = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40))
            json.dump(data, open(path, 'w'))
            time.sleep(2.5 if 'coingecko' in url else 0.3)
            return data, 'fetched'
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(20 * (attempt + 1))
                continue
            return None, f'HTTP {e.code}'
        except Exception as e:
            err = f'{type(e).__name__}'
    return None, locals().get('err', 'rate-limited')


def usd(n):
    if n is None:
        return '-'
    for unit, div in (('B', 1e9), ('M', 1e6), ('K', 1e3)):
        if abs(n) >= div:
            return f'${n / div:.1f}{unit}'
    return f'${n:.0f}'


def pct(n):
    return '-' if n is None else f'{n:+.1f}%'


def coin_rows(coins, n, key, reverse=True, min_mcap=5e6):
    rows = [c for c in coins if c.get(key) is not None and (c.get('market_cap') or 0) >= min_mcap]
    rows.sort(key=lambda c: c[key], reverse=reverse)
    return [f"| {c['symbol'].upper()} | {c['name'][:28]} | {usd(c.get('market_cap'))} | {usd(c.get('total_volume'))} | "
            f"{pct(c.get('price_change_percentage_24h_in_currency'))} | {pct(c.get('price_change_percentage_7d_in_currency'))} | "
            f"{pct(c.get('price_change_percentage_30d_in_currency'))} |" for c in rows[:n]]


COIN_HDR = '| sym | name | mcap | vol24h | 24h | 7d | 30d |\n|---|---|---|---|---|---|---|'


def coin_section(title, coins, top=15, movers=10):
    if not coins:
        return [f'## {title}', 'UNAVAILABLE', '']
    med = lambda k: sorted(c[k] for c in coins if c.get(k) is not None)
    def median(k):
        v = med(k)
        return v[len(v) // 2] if v else None
    out = [f'## {title} ({len(coins)} coins)',
           f"median change: 24h {pct(median('price_change_percentage_24h_in_currency'))}, "
           f"7d {pct(median('price_change_percentage_7d_in_currency'))}, "
           f"30d {pct(median('price_change_percentage_30d_in_currency'))}", '',
           f'top {top} by market cap', COIN_HDR, *coin_rows(coins, top, 'market_cap', min_mcap=0), '',
           f'best 30d (mcap >= $5M)', COIN_HDR, *coin_rows(coins, movers, 'price_change_percentage_30d_in_currency'), '',
           f'best 7d (mcap >= $5M)', COIN_HDR, *coin_rows(coins, movers, 'price_change_percentage_7d_in_currency'), '']
    return out


def main():
    d, status = {}, {}
    for name, url in SOURCES.items():
        d[name], status[name] = get(name, url)
        print(f'  {name:20} {status[name]}')

    L = [f'# MARKET DIGEST — generated {time.strftime("%Y-%m-%d %H:%M")} local',
         'sources: ' + ', '.join(f'{k}={v}' for k, v in status.items()), '']

    g = (d['cg-global'] or {}).get('data')
    if g:
        L += ['## Global', f"total mcap {usd(g['total_market_cap']['usd'])} ({pct(g.get('market_cap_change_percentage_24h_usd'))} 24h), "
              f"vol24h {usd(g['total_volume']['usd'])}, BTC dom {g['market_cap_percentage']['btc']:.1f}%, "
              f"ETH {g['market_cap_percentage']['eth']:.1f}%, SOL {g['market_cap_percentage'].get('sol', 0):.1f}%", '']

    cats = [c for c in (d['cg-categories'] or []) if c.get('market_cap') and c.get('market_cap_change_24h') is not None]
    if cats:
        hdr = '| category | mcap | vol24h | 24h |\n|---|---|---|---|'
        row = lambda c: f"| {c['name'][:44]} | {usd(c['market_cap'])} | {usd(c.get('volume_24h'))} | {pct(c['market_cap_change_24h'])} |"
        big = [c for c in cats if c['market_cap'] >= 1e8]
        L += [f'## Categories ({len(cats)} total; tables limited to mcap >= $100M)',
              'best 24h', hdr, *map(row, sorted(big, key=lambda c: -c['market_cap_change_24h'])[:20]), '',
              'worst 24h', hdr, *map(row, sorted(big, key=lambda c: c['market_cap_change_24h'])[:12]), '',
              'highest volume/mcap ratio (attention)', hdr,
              *map(row, sorted(big, key=lambda c: -(c.get('volume_24h') or 0) / c['market_cap'])[:15]), '']
        watch = ('privacy', 'solana', 'pump', 'ai agent', 'depin', 'meme', 'rwa', 'stablecoin', 'x402', 'payment',
                 'launchpad', 'perp', 'prediction', 'zero knowledge', 'agentic')
        L += ['watchlist categories', hdr,
              *map(row, sorted((c for c in cats if any(w in c['name'].lower() for w in watch)),
                               key=lambda c: -c['market_cap'])[:45]), '']

    t = d['cg-trending'] or {}
    if t.get('coins'):
        L += ['## Trending searches (CoinGecko)', '| sym | name | rank | 24h |', '|---|---|---|---|']
        for c in t['coins']:
            i = c['item']
            ch = ((i.get('data') or {}).get('price_change_percentage_24h') or {}).get('usd')
            L.append(f"| {i['symbol']} | {i['name'][:30]} | {i.get('market_cap_rank') or '-'} | {pct(ch)} |")
        if t.get('categories'):
            L += ['', 'trending categories: ' + ', '.join(c['name'] for c in t['categories'])]
        L.append('')

    L += coin_section('Solana ecosystem (top 250 by mcap)', d['cg-solana-eco'])
    L += coin_section('Privacy coins', d['cg-privacy'], top=20)
    L += coin_section('Pump.fun ecosystem', d['cg-pumpfun'], top=20)
    L += coin_section('AI agents', d['cg-ai-agents'], top=15)

    chains = d['llama-chains']
    if chains:
        chains = sorted(chains, key=lambda c: -(c.get('tvl') or 0))
        L += ['## Chain TVL (DefiLlama)', ', '.join(f"{c['name']} {usd(c['tvl'])}" for c in chains[:10]), '']
    st = d['llama-stables']
    if st:
        st = sorted(st, key=lambda c: -((c.get('totalCirculatingUSD') or {}).get('peggedUSD') or 0))
        L += ['## Stablecoin supply by chain', ', '.join(f"{c['name']} {usd(c['totalCirculatingUSD']['peggedUSD'])}" for c in st[:8]), '']

    for key, title in (('llama-fees-solana', 'Solana protocol FEES (who actually earns)'),
                       ('llama-dexs-solana', 'Solana DEX volume')):
        o = d[key]
        if not o:
            L += [f'## {title}', 'UNAVAILABLE', '']
            continue
        ps = [p for p in o.get('protocols', []) if p.get('total30d')]
        L += [f'## {title}', f"chain total: 24h {usd(o.get('total24h'))}, 7d {usd(o.get('total7d'))}, 30d {usd(o.get('total30d'))}, "
              f"change 7d {pct(o.get('change_7d'))}, 30d-over-30d {pct(o.get('change_30dover30d'))}", '',
              '| protocol | category | 24h | 7d | 30d | 30d trend |', '|---|---|---|---|---|---|']
        for p in sorted(ps, key=lambda p: -p['total30d'])[:30]:
            L.append(f"| {p['name'][:26]} | {(p.get('category') or '-')[:20]} | {usd(p.get('total24h'))} | {usd(p.get('total7d'))} | "
                     f"{usd(p['total30d'])} | {pct(p.get('change_30dover30d'))} |")
        by = {}
        for p in ps:
            by[p.get('category') or '-'] = by.get(p.get('category') or '-', 0) + p['total30d']
        L += ['', 'by category (30d): ' + ', '.join(f'{k} {usd(v)}' for k, v in sorted(by.items(), key=lambda x: -x[1])[:12]), '']

    path = os.path.join(OUT, 'DIGEST.md')
    open(path, 'w').write('\n'.join(L) + '\n')
    print(f'digest -> {os.path.relpath(path)} ({os.path.getsize(path)} bytes)')
    bad = [k for k, v in status.items() if v not in ('cache', 'fetched')]
    if bad:
        print('UNAVAILABLE:', ', '.join(f'{k} ({status[k]})' for k in bad))
        sys.exit(1)


if __name__ == '__main__':
    main()
