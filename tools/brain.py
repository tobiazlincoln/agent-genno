#!/usr/bin/env python3
"""BRAIN: local knowledge cache router. Keeps research on disk and points the
agent at the right cached file instead of re-fetching or re-reading everything.

  brain.py hook              UserPromptSubmit hook: regex-match the prompt, inject a
                             short pointer to the relevant cache (stdin = event JSON)
  brain.py search <regex>    grep the cache, compact output (-n max hits, default 25)
  brain.py index             rebuild BRAIN/INDEX.md (one line per cached file)
  brain.py status            freshness of each topic's cache
"""
import json, os, re, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
BRAIN = os.environ.get('BRAIN_ROOT') or os.path.join(ROOT, 'BRAIN')
TEXT = ('.md', '.txt', '.json', '.rs', '.toml')

# topic -> (prompt regex, cached files, max age hours or None, refresh command)
TOPICS = {
    'market': (r'\b(market|pasar|narasi|narrative|trend(ing)?|hot|crash|bull|bear|cmc|coingecko|cg|defillama|'
               r'tvl|volume|fees?|kategori|categor(y|ies)|sektor|sector|pump\.?fun|memecoin|meme)\b',
               ['research/market/DIGEST.md'], 6, 'python3 tools/market-scan.py'),
    'helius': (r'\b(helius|privacy rings?|zolana|spr|shielded|utxo|groth16|photon|custom rings?|confidential|'
               r'privasi|privacy)\b',
               ['research/DEEPDIVE.md', 'research/deep/zolana-docs_spec.md', 'research/deep/cpr-docs_spec.md',
                'research/docs-privacy-all.txt'], None, 'python3 tools/scan-helius.py all'),
    'audit': (r'\b(audit|certora|zksecurity|ottersec|finding|severity|vulnerab\w+|soundness|trusted setup)\b',
              ['research/deep/zksecurity-audit.txt', 'research/deep/certora-audit.txt'], None, None),
    'hooks': (r'(hook failed|exit(ed)? with code 127|check-command|post-exec|hookrun|hooks\.v1)',
              [], None, 'python3 .devin/hookrun.py doctor --fix'),
}


def age_h(path):
    return (time.time() - os.path.getmtime(path)) / 3600 if os.path.exists(path) else None


def topic_line(name):
    _, files, ttl, refresh = TOPICS[name]
    parts = []
    for f in files:
        a = age_h(os.path.join(BRAIN, f))
        if a is None:
            parts.append(f'{f} (MISSING)')
        else:
            stale = ttl is not None and a > ttl
            parts.append(f"{f} ({a:.0f}h old{', STALE' if stale else ''})")
    line = f'[{name}] ' + ('; '.join(parts) if parts else 'no cache')
    if refresh:
        line += f' | refresh: {refresh}'
    return line


def hook():
    try:
        prompt = json.load(sys.stdin).get('prompt', '')
    except ValueError:
        return 0
    hits = [n for n, (rx, *_) in TOPICS.items() if re.search(rx, prompt, re.I)]
    if not hits:
        return 0
    rel = os.path.relpath(BRAIN, ROOT)
    ctx = (f'Local cache in {rel}/ covers this prompt. Read these before fetching anything; treat STALE or MISSING '
           f'entries as needing the refresh command. Search with: python3 tools/brain.py search "<regex>"\n'
           + '\n'.join(topic_line(n) for n in hits))
    print(json.dumps({'hookSpecificOutput': {'hookEventName': 'UserPromptSubmit', 'additionalContext': ctx}}))
    return 0


def files():
    for cur, dirs, names in os.walk(BRAIN):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for n in sorted(names):
            p = os.path.join(cur, n)
            if n.endswith(TEXT) and n != 'INDEX.md' and os.path.getsize(p) < 2_000_000:
                yield p


def search(pattern, limit):
    rx = re.compile(pattern, re.I)
    shown, total, per_file = 0, 0, {}
    for p in files():
        rel = os.path.relpath(p, BRAIN)
        try:
            lines = open(p, errors='replace').read().splitlines()
        except OSError:
            continue
        for i, line in enumerate(lines, 1):
            m = rx.search(line)
            if not m:
                continue
            total += 1
            per_file[rel] = per_file.get(rel, 0) + 1
            if shown < limit and per_file[rel] <= 5:
                s = max(0, m.start() - 70)
                print(f'{rel}:{i}: {line[s:s + 190].strip()}')
                shown += 1
    print(f'-- {total} matches in {len(per_file)} files (showing {shown}; max 5 per file)')
    for rel, c in sorted(per_file.items(), key=lambda x: -x[1])[:12]:
        print(f'   {c:5} {rel}')
    return 0 if total else 1


def index():
    rows = []
    for p in files():
        first = ''
        for line in open(p, errors='replace'):
            line = line.strip().lstrip('#').strip()
            if len(line) > 3:
                first = line[:90]
                break
        rows.append(f'| {os.path.relpath(p, BRAIN)} | {os.path.getsize(p) / 1024:.0f}K | {age_h(p) / 24:.0f}d | {first.replace("|", "/")} |')
    out = os.path.join(BRAIN, 'INDEX.md')
    open(out, 'w').write(f'# BRAIN index — {len(rows)} files, generated {time.strftime("%Y-%m-%d %H:%M")}\n\n'
                         '| file | size | age | first line |\n|---|---|---|---|\n' + '\n'.join(rows) + '\n')
    print(f'{len(rows)} files -> {os.path.relpath(out, ROOT)}')
    return 0


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'hook':
        sys.exit(hook())
    if cmd == 'search' and len(sys.argv) > 2:
        n = int(sys.argv[sys.argv.index('-n') + 1]) if '-n' in sys.argv else 25
        sys.exit(search(sys.argv[2], n))
    if cmd == 'index':
        sys.exit(index())
    if cmd == 'status':
        print('\n'.join(topic_line(n) for n in TOPICS))
        sys.exit(0)
    sys.exit(__doc__)
