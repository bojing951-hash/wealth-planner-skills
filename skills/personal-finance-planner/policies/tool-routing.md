# Host capability routing and permissions v0.4

**Not a magic tool autodiscovery library.** The host AI enumerates available tools/permissions at runtime, then may supply a declaration using `schemas/capabilities-v0.4.schema.json` (inside Skill). The v0.4 Python program validates declarations and produces tool *requests*, not network calls.

| Logical capability | Host example | Fallback |
|---|---|---|
| `source_discovery` | Search engine / approved browser | Legal + macro evidence unverified |
| `source_fetch` | Open original regulator/statistics page | No binding legal conclusion |
| `execute_math` | Python/terminal/isolated runtime | Host can present only checkable simple arithmetic |
| `parse_user_files` | Local file read, approved conversion | Ask for user-reported fields; requires consent |
| `authorized_account_read` | Read-only bank/MCP plugin | No data inference; requires authorization |
| `private_state` | Explicit local encrypted/private data store | Ephemeral report; requires consent |
| `scheduled_execution` | Approved external scheduler | No background monitoring claim |
| `professional_handoff` | Export for advisor/lawyer review | Keep unresolved facts |

A capability declaration contains `available: true|false`, `permission: granted|ask|denied`, optionally `tool_label`. **An external action is allowed only when the actual host supports it and permissions were granted**; an example manifest is never a credential. `READY_FOR_HOST_EXECUTION` is not the same as executed.

A completed source receipt has `action_id`, `status`, `source_url`, `retrieved_on`, `content_sha256`, and `tax_year` for law sources. Domain hints are used to reject obvious lookalike URLs; a matching official domain does **not** prove the retrieved text is effective, relevant, complete or correctly interpreted.

Permission levels: L0 public read with host approval; L1 read private user material only with permission and minimization; L2 write private persistent state only with explicit consent; L3 money movement, financial trades, tax filing and sharing sensitive information with third parties are NOT implemented and must never be fabricated as completed.
