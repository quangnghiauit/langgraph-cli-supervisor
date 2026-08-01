# agent-orchestrator

A LangGraph Supervisor that routes work between three CLI coding agents —
**Claude Code**, **OpenCode**, and **Codex** — on a local repository.

```
            ┌───────────────┐
   ┌───────▶│   supervisor   │◀────────────┐
   │        └───────┬───────┘              │
   │     next=claude_code / opencode / codex│FINISH→END
   │                │                       │
   │        ┌────────┴─────────┐            │
   │   claude_code          opencode         │
   │        │                  │             │
   │        ▼                  ▼             │
   └── (back to supervisor)  codex ──pass──▶─┘
                               │
                             fail
                    ┌──────────┴──────────┐
              attempts < max        attempts >= max
                    │                     │
                    ▼                     ▼
                opencode (retry)     human_review (interrupt)
```

- **claude_code**: complex source analysis, general CLI tasks.
- **opencode**: large-scale refactoring / multi-file project analysis.
- **codex**: generates and runs tests, reports pass/fail.
- **supervisor**: an LLM (Claude or GPT) that reads the state and decides what
  happens next.
- **human_review**: a hard stop reached once the retry budget is exhausted —
  implemented with LangGraph's `interrupt()`, resumable at any time.
- State is persisted per `thread_id` in a local SQLite file via
  `SqliteSaver`, so a run can be inspected or resumed later, not just at the
  human-review gate.

## Setup

```bash
cp .env.example .env
# then edit .env: set ANTHROPIC_API_KEY or OPENAI_API_KEY
```

The three CLIs must be on `PATH`: `claude`, `opencode`, `codex`. Each must be
logged in / have its own credentials configured independently (this project
only shells out to them — it does not manage their auth).

## Run

```bash
python3 main.py "Refactor the payment module and make sure tests pass" --dir /path/to/repo
```

Each step prints as it happens. If the retry budget is exhausted, the run
pauses and prints what a human should look at:

```bash
python3 main.py --thread-id default --resume "the flaky test is unrelated, ship it"
```

Use `--thread-id` to run multiple independent tasks/threads against the same
checkpoint database.

## Permission modes (read before running unattended)

Each CLI agent executes real commands / edits real files. Defaults in
`.env.example` are intentionally conservative:

| Env var | Default | Risk |
|---|---|---|
| `CLAUDE_PERMISSION_MODE` | `acceptEdits` | `bypassPermissions` skips all prompts |
| `CODEX_SANDBOX_MODE` | `workspace-write` | `danger-full-access` removes sandboxing |
| `OPENCODE_AUTO_APPROVE` | `false` | `true` (`--auto`) auto-approves every permission |

Only relax these if you understand and accept what the agent may do
unattended.

## Known scope cuts

- Routing/verification runs each CLI's own headless/non-interactive mode
  (`claude -p`, `opencode run`, `codex exec`) and reads their text output.
  It does **not** wire the three tools together over MCP — each CLI already
  has its own MCP client/server support, and connecting them directly is a
  reasonable follow-up but adds real complexity that the routing/retry logic
  above doesn't need.
- The Supervisor's routing/pass-fail judgment is only as good as the model
  and the text markers each CLI happens to print — there's no separate
  structured test-result protocol.
