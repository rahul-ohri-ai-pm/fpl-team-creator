# Agent Patterns for This Project

A playbook for which agent type fits which FPL-analysis task — to avoid both under-using agents
(re-deriving context by hand every time) and over-using them (spawning one for a question that's
faster to just answer).

## Explore — read-only code search

**Use for**: "Where is X?" questions about this codebase.
- "Where is the scoring formula?"
- "Which files call `recommend_transfers`?"
- "Does `optimize.py` already handle chip logic?"

Breadth: "quick" for a single lookup, "medium" for a few files. Never for FPL *data* questions
(player stats, injury status) — those go through `engine/fetch.py` or the `fpl` MCP directly, not
a codebase search.

## Plan — architectural design

**Use for**: designing an implementation before writing code, when there's a real design choice to
make.
- "How should we add a new weight scheme to the scoring model?"
- "Should the backtest framework snapshot pre-gameweek data automatically?"

Use once per design question, not repeatedly — if a Plan agent's output needs another round, that
usually means the question wasn't scoped tightly enough going in.

## General-purpose — multi-step execution

**Use for**: a scheduled or repetitive task that's well-specified enough to run without further
judgment calls mid-stream.
- Running `/gw-backtest` across all 4 weight schemes and logging the result
- A full `/fpl-weekly-review` pass end-to-end

Point it at the specific skill and docs it needs (e.g., `.claude/docs/SCORING.md` +
`records/gameweek_reviews.md` for a backtest) rather than the whole project — see the token-budget
note per skill in each `SKILL.md`.

## Policy

- **Don't spawn an agent for a one-off answer.** "What's the current ownership_weight for `safe`?"
  is a direct read of `.claude/docs/SCORING.md`, not a task for any agent.
- **Don't duplicate work.** If a skill's SKILL.md already specifies the steps, delegate to
  execution of that skill rather than re-deriving the same fetch→score→optimize sequence by hand.
- **Ad-hoc FPL questions** (injury status, fixture difficulty, "should I captain X") don't need an
  agent at all — call `engine/fetch.py` or the relevant `fpl` MCP tool directly and answer inline.
