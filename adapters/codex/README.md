# Codex host integration — v5 developer preview

Follow current Codex Skills documentation: https://developers.openai.com/codex/skills

Install **the entire Skill folder** (macOS/Linux example):

```bash
mkdir -p "$HOME/.agents/skills"
cp -R skills/personal-finance-planner "$HOME/.agents/skills/personal-finance-planner"
```

Then instruct Codex to use `$personal-finance-planner` and provide either a synthetic profile or user-authorized data. The installed Skill must guide Codex to **actually inspect tools available to this runtime** before claiming browsing, source collection, shell execution or private file access.

Expected flow:

1. Read `SKILL.md` and relevant `workflows/` based on question.
2. Call `scripts/wealth_v5.py validate --input ...` (host shell access permitting).
3. Truthfully declare host capabilities as ephemeral JSON; don't borrow `EXAMPLE` manifest to claim tool permission.
4. Call `host-queue` then use actual available source tools if permitted; record downloaded public-source metadata and per-source effective date.
5. Run `run` again with actual `--receipts` (if collected), plus explicit scenario inputs, then explain and flag unresolved law; never invent tool completion.
6. With prior report, use `review`; no continuous monitoring unless separate authorized scheduling supported.

Test standard finance, no-network fallback, CN/HK PF, NY/Chicago research scope and local privacy. Do not run against live brokerage or use a user bank password.

**No GitHub URL or client E2E validation is claimed in this zip.**
