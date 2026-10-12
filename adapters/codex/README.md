# Codex integration — Wealth Planner Skill v5.3 Developer Preview

This repository uses the open Agent Skills `SKILL.md` contract. The Codex host performs **all actual reasoning, tool calls, file access and report creation**. The Skill only describes professional methods and optional finite Python validators. Do not use the legacy `host-queue` as a required runtime step or treat it as proof of executing a tool.

Install the **entire** directory `skills/personal-finance-planner/` in `~/.agents/skills/personal-finance-planner/` (or a Codex-supported project Skill directory). Check your actual Codex version and supported Skills search paths.

For a comprehensive scenario use the exact invocation:

> Use `$personal-finance-planner` to act as a professional financial planning research assistant. Treat my information as synthetic unless verified. Diagnose my binding constraints, quantify the financial goal gap without using emergency cash, compare >=2 actionable alternatives with costs and conditions, and give a 30/90/365-day user-owned plan with explicit review criteria. Include current-law caveats and check your professional-report quality before responding.

Read `workflows/professional-consultation.md` after `SKILL.md` for complete plans, then load the interview/diagnosis/action references on demand. Narrow questions should receive narrow answers.

Optional if Python is available and permission given:

```bash
python skills/personal-finance-planner/scripts/consultation_math.py --input <PRIVATE_HYPOTHETICAL_INPUT_JSON>
python skills/personal-finance-planner/scripts/plan_quality.py --input <PRIVATE_REPORT_JSON>
```

Do not write real financial data to the public repository, run financial transactions or create/read/write persistent memory without specific user permission. Current tax, legal, research citations and return forecasts are not supplied automatically by a Skill install.

End-to-end live Codex consultation + blinded baseline-vs-Skill comparison remain **NOT_TESTED** in this project release, see `tests/host_e2e/ACCEPTANCE_CONSULTATION_v5.3.md`.
