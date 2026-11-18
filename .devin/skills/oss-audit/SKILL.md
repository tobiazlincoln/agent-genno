---
name: oss-audit
description: Mass security audit pipeline for open-source targets (GitHub repos, HuggingFace models). Deterministic scanners do the scanning; the agent seeds targets, runs the pipeline, and triages findings into a report.
triggers:
  - user
  - model
---

# OSS Audit Skill

Pipeline at `pipeline/audit.py` (venv: `pipeline/.venv/bin/python3`).
Storage: `storage/audit.db` (sqlite — targets, scans, findings tables).

## Workflow

### 1. Seed targets
```bash
pipeline/.venv/bin/python3 pipeline/audit.py seed-gh "QUERY" --limit N
pipeline/.venv/bin/python3 pipeline/audit.py seed-hf --limit N
```
GitHub queries use the standard search syntax (`language:python stars:>1000 topic:llm`).
HF seeding pulls top-downloaded models. Authenticate with `HF_TOKEN` env for higher rate limits.

### 2. Scan
```bash
pipeline/.venv/bin/python3 pipeline/audit.py scan --limit N
```
Runs available scanners per target: `bandit` (SAST), `pip-audit` (dep vulns),
`picklescan` (malicious pickles in model files), plus `osv-scanner`/`gitleaks`
if installed. Results land in the `findings` table. Workdir is cleaned after each target.

### 3. Check state
```bash
pipeline/.venv/bin/python3 pipeline/audit.py status
pipeline/.venv/bin/python3 pipeline/audit.py findings [--target ID]
```

### 4. Triage (your job as the agent)
Raw scanner output is noisy. For each scanned target:
- Query findings by severity: CRITICAL/HIGH first, MEDIUM spot-check.
- Classify each as: TRUE POSITIVE / FALSE POSITIVE / NEEDS CONTEXT.
- Known false-positive patterns: picklescan "invalid magic number" on
  non-pickle binaries (.mlmodelc, OpenVINO .bin), bandit `assert_used`
  in test files, `debug=True` in example/tutorial code.
- Record triage verdicts in the `triage` table if present, or write
  `storage/reports/<target>.md` with verdict + evidence.

### 5. Report
Produce `storage/reports/audit-<date>.md`:
- Summary counts by severity and by verdict
- True positives only, with file:line evidence
- Recommended actions per target

## Rules
- Never let the agent eyeball source files for vulns instead of running scanners —
  findings must come from the `findings` table (deterministic evidence).
- Never claim a target is "clean" unless all applicable scanners ran and
  returned zero findings — say "scanned clean by: <list>".
- Respect AGENTS.md: verify claims against DB queries, not memory.
- Cost discipline: fetch shallow (`--depth 1`), skip blobs >50MB,
  delete workdir after each target.
