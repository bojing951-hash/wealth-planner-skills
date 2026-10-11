# Claude Code host integration — v5 developer preview

Current skill documentation: https://code.claude.com/docs/en/skills

Install entire `skills/personal-finance-planner/` to `~/.claude/skills/personal-finance-planner/` or project `.claude/skills/`.

```bash
mkdir -p "$HOME/.claude/skills"
cp -R skills/personal-finance-planner "$HOME/.claude/skills/personal-finance-planner"
```

In Claude Code, explicitly invoke `personal-finance-planner` (or ask a matching personal wealth planning question). The instructions describe how to invoke Python, but Claude decides actual tool calls subject to user permissions; the Skill **cannot override Claude's Tool permissions, shell sandbox, account access or schedule**.

Test: `wealth_v5.py validate/run`, unavailable-network honesty, real official-source research with real receipts if available, and no account access unless explicitly allowed. No authenticated accounts are required for synthetic demo.

**Not equivalent to Claude AI API upload or persistent independent Agent.**
