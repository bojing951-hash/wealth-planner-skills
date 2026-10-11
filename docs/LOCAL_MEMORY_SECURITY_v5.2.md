# v5.2 Opt-in Local Financial Memory — design, consent and threat model

**Status:** Developer Preview; Linux POSIX behavior covered by local tests. macOS and Windows are specified but NOT independently tested. This optional support utility is not an Agent, backend daemon, scheduler, financial account integration or hosted data store.

## Product contract

The Skill is always usable without memory. On first launch, **do not create or read a private profile**. A host Agent may offer persistence after completing a normal planning task; only user approval unlocks each operation. The host (not this package) executes all command-line actions using the permissions actually available. The host must not derive approval from the presence of a vault, a chat history snippet, a `--consent-*` flag, or the preview checksum.

| User action | Host flow | Who performs the operation | Permission | Result |
|---|---|---|---|---|
| Ask one-off financial question | No private memory access | Host + Skill guidance | Normal task | No vault |
| Enable local memory | Explain scope, storage location, risks; ask before initialization | Host invokes `init` | Explicit L2 | Encrypted vault, key in separate private folder |
| Resume planning from prior records | Ask permission to access existing vault, read minimal summary | Host invokes `read` | Explicit L1 each read | Date-stamped facts, freshness warnings |
| Propose new observations/plan | Normalize facts, check evidence/ownership, preview exact JSON | Host invokes `preview` | Explicit L1 | Preview + `change_sha256`, no write |
| Save new observations/plan | Show proposed changes and digest, wait for approval; use expected revision and checksum | Host invokes `update` | Explicit L2 each write | Atomic revision increment |
| Compare old/new | Inspect two revision snapshots and explain *observed differences* | Host invokes `compare` | Explicit L1 | Change list, no automatic financial action |
| Correct/forget facts | Explain consequences for derived plans and other records | Host invokes `forget`/`purge` | Explicit L2 | Encrypted state overwritten with redaction |
| Remove local profile | Explain effect and deletion limits, verify exact profile ID | Host invokes `delete` | Explicit L2 | Deletes vault and matching local key |
| Export JSON | Explain plaintext risk; user prepares private output directory | Host invokes `export` | L1 + acknowledgement | New mode-0600 plaintext JSON; never public repo |

**Preview fingerprint:** `change_sha256` hashes the profile id, revision and normalized change payload. It is **not authentication, a signature, evidence of human approval, or secret authorization token**. It prevents accidental substitution of payload between the displayed preview and subsequent update. The update also verifies the expected revision to avoid silently overwriting concurrent edits. Re-preview/reapprove if revision changes.

## Data minimization and meaning

- Four logical layers are kept inside ONE encrypted blob: `facts_current` (profile and latest aggregates), `snapshots` (past financial status), `plans` / `decisions` (short rationales, assumptions and approvals), `events` (revision/timestamp/fields changed).
- Allowlisted fields are city/region/country claims, household status, income type and aggregate realized/gross/net money, basic expenses, restricted assets, liabilities, goals, risk preference. All facts include `as_of` date and `confidence`/`source_type`; money fields require an ISO currency code, and PF *bank received* differs from PF simulated account profit.
- **No** account numbers, tax identifiers, exact addresses, passwords, OAuth keys, brokerage orders, raw transaction feeds, social security numbers, scanned IDs or complete bank statements. Free-text summaries are length-limited and filtered for common secrets, but this is NOT comprehensive DLP.
- Verified financial facts need a verified source type, reviewed reference and verification date; the tool **cannot** independently inspect the original document. User-reported fields remain user-reported on resumption. Old balances, income and residency claims are marked stale for review; future-dated records are flagged.
- Monetary values retain original currencies: the vault does not aggregate CNY and USD into one sum or silently apply FX rates.
- The host may use retrieved facts for a new plan only within the user's authorized scope; any law, price, account value or macro input still needs independent current source verification.

## Local storage paths and portability

| Platform | Encrypted vault root | Key directory |
|---|---|---|
| Linux | `${XDG_DATA_HOME:-~/.local/share}/wealth-planner-skill` | `${XDG_CONFIG_HOME:-~/.config}/wealth-planner-skill/private-keys` |
| macOS | `~/Library/Application Support/WealthPlannerSkill` | `~/Library/Preferences/WealthPlannerSkillKeys` |
| Windows | `%LOCALAPPDATA%\WealthPlannerSkill` | `%LOCALAPPDATA%\WealthPlannerSkillKeys` |

Inside the vault root: `profiles/<pseudonymous-id>/vault.enc` and a lock metadata file. The 32-byte key lives in the separate local key directory, `<id>.key`. Data paths may be customized to two *distinct*, private folders (`--data-dir`, `--keys-dir`), but are forbidden inside a detected Git repository or via symlink paths.

Codex and Claude Code can reuse the same data only if BOTH run with permitted access to exactly the same **local OS-user** data and key roots. Containers, different users and cloud environments do not automatically share these files. The system never uploads or synchronizes vaults or keys on its own. No personal data is included in the public Skill/release ZIP.

## Encryption and limitations

- AES-256-GCM with fresh random 12-byte nonce for each save; authenticated ciphertext and profile-associated data binding. Separate local 256-bit key. Missing cryptography library fails closed.
- Directories configured as 0700 and files as 0600 on tested POSIX hosts, private-file ownership/link checks, symlink defense, atomic replacement, file locking and revision checks. Windows filesystem ACL inheritance is **not a completed independent security evaluation**; review target-machine security before storing valuable personal financial data.
- Encryption reduces damage from copying the `vault.enc` file **without its key**, but does not protect a compromised OS user or host that can read both, backups/filesystem snapshots/swap, AI session traces or private financial data already pasted into cloud chat.
- Revocation/deletion destroys live local vault and key only. The program cannot remotely erase previous exports, prior backups, host conversations or connected-system copies. The `.write.lock` and empty profile directories may remain after deletion to avoid unsafe concurrent locking changes; they contain no finance contents but may reveal that a profile existed.
- Do not promise complete forensic secure erase from solid-state drives, snapshots or backups. Consider disk-level encryption and private backup policies if needed.

## Testable invariants and blockers

1. Default execution does not create private storage or read personal files.
2. Authorization flags are *runtime assertions*; the Skill's workflow requires real user approval before host action. No model can authenticate consent solely through this CLI.
3. No plaintext fallback; reject unexpected fields, malformed data, missing keys, weakened POSIX permissions, linked files and Git paths.
4. Second CLI process with access to the same authorized data/key roots can read the same revised state. No implied sync to different machines.
5. Out-of-date user data is review-needed, not treated as verified and current. Host must never silently promote it.
6. Approved preview digest and revision must match update; conflicting updates fail and must be re-reviewed.
7. Forget/clear remove derived summaries that may disclose the forgotten field; full deletion removes local vault/key. User must be told the limits.
8. No background scheduler, monetary transfer, automated trade or tax filing capability is enabled by memory.

**Actual host E2E remains NOT_TESTED** for both Codex and Claude Code. Independent subprocess tests are an offline portability proxy only.
