> **Historical/compatibility reference (pre-v5.1).** The normative host-call and lifecycle protocols are now `workflows/host-research-protocol.md`, `workflows/skill-first-execution.md`, and `workflows/dynamic-review-protocol.md`. **Do not treat this document as an instruction to run `host-queue` before the host can use its actual tools.**

# Dynamic financial planning (re-invocation, not an immortal Agent)

**Manual/on-demand implementation exists. Persistent agents and background notifications do not.**

- Revisit financial cash flow at user's request or monthly; review asset drift/risk quarterly; research local-year tax regulations when applicable or they change; annually revisit life-cycle goals and 10–30y assumptions.
- Immediate review triggers: tax-year/locality/citizenship or residency change; work/medical/family events; material income/expenditure shifts; upcoming capital need; new debt; user-set risk breach; research/effective law update.
- `run --previous <old_plan.json>` computes versioned input/assumption/source hashes. `review --previous ... --current ...` reports material deltas. The separate reports must be created by the host/user; compare doesn't monitor remote systems.
- Distinguish re-run of calculations from changing long-term investments. Fresh macro inputs alter model scenarios; user confirmation required for strategy change, more so for trading.
- Keep versions and explanatory change log in user-private storage only if explicitly requested. Do not place real personal profiles/reports in a public repository. No host-independent auto-scheduler in package.
