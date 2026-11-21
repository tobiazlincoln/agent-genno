# NAMING VERDICT — 22 Nov 2026

Method: every candidate checked against CoinGecko (coins), GitHub (crypto/wallet repos),
npm (exact names), DNS resolution (resolving = taken), and web search for concept collisions
in the Solana privacy landscape (Rings.run, Cloak, Umbra, Vanish, GoDark, Hinkal, Elusiv,
Arcium, Light, ShadowWire, Lumenless, Voidify, Mixoor, Turbine, Houdini, zkRune, Doei, Lana,
ShieldedSOL, Iris, ringexplorer, Muffle).

## Rejected (verified collisions)

| name | why out |
|---|---|
| muffle | pump.fun token "Muffle" (@muffledotcash) doing shielded-pool -> burner wallet buys ON SOLANA — concept-adjacent, not just name collision |
| dither | Dither (DITH) token, rank ~2954, Solana trading AI — same chain |
| murmur | MurMur token exists (r~11558) |
| static | Statics Protocol (r~1759) |
| riak | Riak = existing database (npm taken) |
| anything with ring/veil/shadow/ghost/cloak/priv/elite | crowded space, guaranteed similarity |

## RECOMMENDED: Chaff

- CoinGecko: no coin. GitHub: no crypto/wallet project. npm: no exact package.
  No similarity to any name in the Solana privacy landscape.
- Domain: chaff.com/.xyz/.io/.app taken; chaff.pro, chaff.dev, getchaff.xyz, chaffed.xyz,
  dropchaff.xyz have no DNS (verify at registrar — no-DNS is not proof of unregistered,
  and X handle availability still unchecked).
- Lineage (this is the strongest part): "chaffing and winnowing" — Ronald Rivest, MIT, 1998
  ("Confidentiality without Encryption"). Chaff = the decoy packets mixed with real ones so
  an observer cannot separate them. Also standard countermeasure terminology in traffic
  analysis (chaff + timing jitter). The name is not made up; it is the correct technical
  term for exactly what the product does.
- Fit to mechanism: a plane drops chaff so radar cannot lock on. The product splits public
  deposits/withdrawals into multiple parts with shaped amounts and randomized timing so
  chain observers cannot lock on to the private transfer between them.
- One syllable, pronounceable in Indonesian too ("caf"), no crypto-bro connotation.

## Narrative frame (lowercase, concrete — no inflated claims)

- what it is: a local autopilot for private balances.
- one line: "your public edges stop matching. the middle stays private."
- honest limits (must ship WITH the product, per our compliance rules):
  protocol-level leaks (zkSec #01, Certora L-05) are out of scope; we shape what the
  client controls — amounts, timing, routing, UTXO hygiene.

## Status of the build decision

Still gated on the final leak report (collector ~65% of deposit/withdraw signatures).
Pre-registered rule: cross-address unique-match rate high above chance -> build Chaff.
Low -> idea dies; fallback candidates re-examined with the same method.
