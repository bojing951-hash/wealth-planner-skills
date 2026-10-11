# Opt-in local financial memory — **HOST executes, Skill specifies protocol** (v5.2)

**Scope:** A persistent financial state/decision memory for people who deliberately opt in. The Skill is a set of instructions; optional `scripts/memory_cli.py` is a local encrypted file adapter and **not** a continuously running Agent, a synchronized cloud database, a bank connector, or ChatGPT's native memory feature. The user owns the data and can decline persistence. No default folder is created merely by installing the Skill or asking for financial advice.

## Authorization and execution gates (strict)

1. **Discover host capability, never presume it.** For a read, host must be able to access the user's local filesystem (or an explicitly authorized private backing store). Cloud-hosted/isolated Codex, Work, or Claude session may not be able to access the user's computer. A host without persistence runs session-only; never claims continuity.
2. **Ask user whether to save anything.** Show categories, approximate location, retention implications, and encryption limits. If declined, do not write, do not silently enable native memory, do not assume previously available chat history is authorized persistent finance data.
3. **Consent L1 personal read, L2 private write** are separate. Before each proposed write, host shows a short precise diff or exact new data and obtains fresh user approval. `--consent-read` and `--consent-write` are attestations that host ALREADY obtained the user's action/approval; flags are not substitutes for it.
4. **Store minimum data only.** Default to normalized financial aggregates, residence at country/region/city level, sources, dates, uncertainty and plan summaries. No bank account numbers, tax IDs, passwords, API tokens, full statements, exact street addresses, tax return originals, broker credentials or personal health records.
5. **On access:** host reads only after L1 approval; `--view summary` is normally sufficient. For detailed audit, `--view full` may show history but must NOT be automatically pasted into chat/telemetry, copied to a project repo or sent to third parties.
6. **On change:** host first `read` then `preview` the proposed changes, obtains user confirmation of the exact preview, then runs `update --expected-revision N --approved-preview-sha256 <DIGEST>`, checks revision and errors, and can compare revisions. Reject concurrency conflicts; never retry silently with a new revision. Keep money in original currencies and source confidence (user-reported is never silently verified).
7. **Staleness:** old balances, income, residence and tax status are *review-needed*, not current proof. A major relocation, tax-year change, dependent, income interruption or new expenditure reopens relevant analysis. Memory is NOT a validated official tax rule or a substitute for retrieval of current official law.
8. **Forget/delete:** on user request use `forget`, category `purge`, or entire `delete`. Full delete removes the local encrypted vault and local key, not old OS backups, prior exports, connected apps or AI host transcripts. Explain limits. A plaintext export requires its own explicit acknowledgement.
9. **Host portability:** Codex and Claude Code share one profile only if BOTH have authorized access to the **same OS user, vault and key directories**. Do not sync secrets or finance data by uploading to a Git repository. Profiles are pseudonymous IDs; directory paths are determined by the local runtime platform or user-designated private paths.
10. **No L3 actions:** memory stores plans and decisions only. Nothing here trades, transfers, files taxes, opens accounts or authorizes future writes or autonomous background scheduling.

## Four conceptual memory layers (single encrypted vault)

| Concept | Actual storage | Typical contents |
|---|---|---|
| Profile | `facts_current` | city/country claims, household, income source, goals, preferences, dated provenance |
| Financial status | `facts_current` + `snapshots` | dated aggregates, money and currency, old/new snapshots, credibility/freshness |
| Decisions | `decisions` + `plans` | summary, rationale, cited source IDs, assumptions, approval; no full financial documents |
| Progress / review | `events`, `snapshots`, review warnings | revision changes, staleness, goal changes and explicit recomputation triggers |

Metadata is stored in encrypted JSON inside `vault.enc` (AES-256-GCM), using a random key stored separately under a private user configuration directory (file mode 0600). Directories are user-only (0700), writes are atomic under a process lock, and a revision compare-and-swap protects changes from cross-host conflicts. `cryptography` is an **optional dependency** (`requirements-memory.txt`); when absent, no unencrypted fallback is used. Key lives on the same OS user's storage, not in hardware or the OS Keychain: **same-user malware, shell/host transcripts, backup snapshots and old exports are not protected**. This is local encryption against disclosure of a vault file copied without its key, NOT a guarantee against local-device compromise.

## CLI examples (private user terminal or authorized host)

Use the Skill-installed path `<SKILL_DIR>/scripts/memory_cli.py` (optional Python 3.10+ and `cryptography`). Run example only for an **actual consenting user** with synthetic demo input; demo data itself is NOT evidence about the real user.

```bash
python3 -m pip install -r <SKILL_DIR>/requirements-memory.txt
python3 <SKILL_DIR>/scripts/memory_cli.py --profile user_001 status
# After user approves persistent storage (L2):
python3 <SKILL_DIR>/scripts/memory_cli.py --profile user_001 init --consent-write
# After user approves reading (L1):
python3 <SKILL_DIR>/scripts/memory_cli.py --profile user_001 read --consent-read
# Host can pipe normalized JSON via stdin from an authorized private source (not CLI args):
python3 <SKILL_DIR>/scripts/memory_cli.py --profile user_001 preview --expected-revision 0 --consent-read --stdin
python3 <SKILL_DIR>/scripts/memory_cli.py --profile user_001 update --expected-revision 0 --approved-preview-sha256 <DIGEST_FROM_APPROVED_PREVIEW> --consent-write --stdin
python3 <SKILL_DIR>/scripts/memory_cli.py --profile user_001 compare --old-revision 1 --new-revision 2 --consent-read
python3 <SKILL_DIR>/scripts/memory_cli.py --profile user_001 forget --field income.monthly_net_realized --expected-revision 2 --consent-write
python3 <SKILL_DIR>/scripts/memory_cli.py --profile user_001 purge --category all_history --expected-revision 3 --consent-write
python3 <SKILL_DIR>/scripts/memory_cli.py --profile user_001 delete --confirm-profile user_001 --consent-write
```

**Pipe correctly:** `preview`/`update` read their full JSON object from stdin (`--stdin`); do not include raw sensitive data in shell command arguments, a tracked README, chat logs, or a repository file. The supplied `examples/memory-demo-v5.2.json` is **synthetic only**. CLI outputs can expose financial facts to host transcripts; users must explicitly permit using those facts in the host execution environment. Do not redirect plaintext outputs into a public repository.

**The `change_sha256` digest is a mismatch guard, not authentication or consent.** If the preview is stale or any field/value changes, preview again and obtain new approval. Never confuse a user approving a financial *plan* with consent to persist it.

**Default paths:** Linux `${XDG_DATA_HOME:-~/.local/share}/wealth-planner-skill` and `${XDG_CONFIG_HOME:-~/.config}/wealth-planner-skill/private-keys`; macOS `~/Library/Application Support/WealthPlannerSkill` and `~/Library/Preferences/WealthPlannerSkillKeys`; Windows `%LOCALAPPDATA%/WealthPlannerSkill` and `%LOCALAPPDATA%/WealthPlannerSkillKeys`. Customize via `--data-dir`/`--keys-dir`, but never place either under a Git repo. For cloud sandboxes, configure an explicitly user-approved persistent private location if available; never assume local host folders remain between sessions.

**Consent status never persists as a blanket grant to access anything.** The user must authorize each reading or writing activity as appropriate; the host cannot infer current permission solely because `vault.enc` exists.

## Staged review pattern

```text
User changes salary → Host gets L1 read consent → Read dated prior facts
  → ask about stale assets, costs, tax jurisdiction as needed
  → host performs fresh research/math with Skill core policies
  → host previews proposed memory changes (N→N+1)
  → user approves the specific save (L2) → encrypted atomic update
  → host compares historical facts and records explanation, no trade executed
```

If user withdraws consent, stop using memory and comply with the requested privacy action. No agent scheduler is started by this module.
