# Triage prompt (use for GLM worker subagent)

Query the findings table for target {{TARGET_ID}} in storage/audit.db:

    sqlite3 -json storage/audit.db \
      "SELECT scanner, severity, title, detail, location FROM findings
       WHERE target_id = {{TARGET_ID}} ORDER BY severity"

For EACH finding produce a verdict:

- TRUE_POSITIVE — real exploitable issue; explain attack path briefly
- FALSE_POSITIVE — explain why (test code, non-pickle binary, dev-only config)
- NEEDS_CONTEXT — say exactly what extra info would resolve it

Rules:
- Read the flagged file/snippet before judging — never classify from title alone.
- picklescan "invalid magic number" on non-pickle formats (CoreML, OpenVINO,
  protobuf, safetensors) is a FALSE_POSITIVE.
- Findings inside test/, examples/, docs/, tutorial/ dirs are usually
  FALSE_POSITIVE unless they ship to production code paths.
- Output format: `verdict | severity | title | location | one-line reason`
- End with a summary count and a verdict for the whole target:
  SAFE / RISKY / MALICIOUS / INCONCLUSIVE.
