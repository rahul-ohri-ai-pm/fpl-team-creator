# AI Product Plan — FPL Team Creator

Status: draft v1 · Owner: Rahul · Purpose: take the project to production and use it as an AI PM portfolio case study.

## 1. Problem and users

**Problem.** FPL managers face ~20 transfer options a week and no way to tell which advice is trustworthy. Existing tools show data or opinions but rarely prove their own accuracy.

**Primary user.** An engaged FPL manager who wants one clear move per gameweek, the reasoning, and evidence that the model's past calls held up.

**Secondary user (the portfolio audience).** A hiring manager scanning for evidence of AI product judgement: evals, guardrails, cost control, iteration on measured error.

## 2. Product thesis

> The most *trustworthy* FPL advisor, not the most feature-rich: every recommendation is grounded in a deterministic engine, explained by an LLM, and scored publicly against real results.

The LLM never invents numbers or squads. It explains and retrieves; the engine decides.

## 3. Principles

1. **Engine decides, LLM explains.** Points, squads and legality come from `engine/`. The LLM only narrates and extracts.
2. **Advisory only.** No transfers are ever executed against a live FPL account.
3. **Measured, not asserted.** Every AI feature ships with a metric and a baseline.
4. **Unknown stays null.** Extraction returns null rather than guessing (same rule as `data/preseason.json`).
5. **Reachable from the real squad.** "Best team" always means from the current squad, bank and free transfers.

## 4. AI features (prioritised)

| # | Feature | What it does | Success metric | Guardrail |
|---|---|---|---|---|
| 1 | Grounded advisor chat | Claude with tool use over `recommend_transfers`, `best_lineup`, fixtures and injuries; answers "why X over Y?" | Groundedness ≥ 95% (every figure traceable to a tool result); task success on a fixed question set | Answers refused or flagged if a number has no tool source |
| 2 | Explainable recommendations | One-line reason per transfer and captain pick | Reason-vs-engine-driver agreement ≥ 90% (LLM-as-judge plus spot checks) | Reasons generated from engine fields only |
| 3 | News and injury extraction | Turns press-conference and news text into `{player, status, return_date, confidence}` | Precision/recall vs the official FPL API status; null rate reported | Null when unsure; never overrides API status without a source link |
| 4 | Public eval dashboard | Predicted vs actual points per gameweek, bias by position, weight-change A/B | MAE trend down over the season; calibration bias near 0 | Built on `records/predictions.jsonl` and `engine/evaluate.py` |
| 5 | Weekly digest agent | Scheduled run: evaluate last week, recommend this week, send a short summary | On-time delivery before deadline; cost per run | Hard token and cost budget per run; failures fall back to the plain engine report |

## 5. Architecture (target)

- **Core:** existing `engine/` (fetch, score, optimize, evaluate), unchanged.
- **API:** wrap in `web_api.py` (FastAPI). Endpoints: `/recommendation`, `/explain`, `/chat`, `/evals`.
- **LLM layer:** Claude API with tool use. Tools are thin read-only wrappers over engine functions.
- **Validators:** deterministic checks (15-man squad shape, £100.0m budget, max 3 per club, free-transfer and hit math) run on every output before display.
- **Frontend:** existing React app (`src/`): decision card, squad table (XI/bench, captain/vice), chat panel, evals page.
- **Storage:** append-only `records/` stays the source of truth; add a small run log (tokens, latency, cost, validator pass/fail).
- **Hosting:** free-tier backend and static frontend; scheduled weekly job.

See `docs/ARCHITECTURE.md` and `docs/EVALUATION.md` for existing detail.

## 6. Evaluation plan

- **Offline eval set:** 30–50 fixed questions (transfers, captains, fixtures, injuries) with expected tool calls and facts.
- **Metrics:** groundedness, tool-call accuracy, answer correctness, refusal correctness, latency p50/p95, cost per answer.
- **Model quality:** prediction MAE and bias per gameweek (already measured). Retune `engine/score.py` only on measured bias, and log the reasoning.
- **Regression gate:** a prompt or model change must not drop groundedness or correctness below baseline.
- **Online:** thumbs up/down per recommendation; 'followed' vs 'ignored' tracked against outcome.

## 7. Risks and mitigations

| Risk | Mitigation |
|---|---|
| LLM hallucinates stats or players | Tool-only numbers, groundedness check, validators |
| Stale data near deadline | Show data timestamp; refuse to recommend if fetch is older than a threshold |
| Cost creep | Per-run and per-user budgets, caching of engine results, smaller model for extraction |
| FPL API change or outage | Cached last-good snapshot; clear degraded-mode banner |
| Overclaiming accuracy | Publish MAE and misses, including bad weeks |
| Scope creep | Roadmap below; one feature per milestone |

## 8. Roadmap

| Milestone | Scope | Exit criteria |
|---|---|---|
| M1 — Serve | API + decision card + squad table live; weekly job | Public URL; weekly run succeeds unattended |
| M2 — Explain | Explainable recommendations + validators | Agreement ≥ 90% on judged sample |
| M3 — Chat | Grounded advisor chat with tool use + eval set | Groundedness ≥ 95%; regression gate in CI |
| M4 — Prove | Public eval dashboard | Full-season predicted vs actual published |
| M5 — Extract | News/injury extraction vs API ground truth | Precision/recall reported with null rate |
| M6 — Digest | Scheduled digest agent with cost budget | Delivered before each deadline for 4 weeks |

## 9. Portfolio framing (case study outline)

1. Problem and user insight
2. Why "engine decides, LLM explains"
3. Eval design: what I measured and why
4. A failure I found and how I fixed it (use a real bad gameweek from `records/gameweek_reviews.md`)
5. Cost and latency trade-offs
6. What I'd do next

## 10. Open questions

- Free vs paid tier, and whether accuracy is the paid hook.
- Which model sizes for chat vs extraction (cost vs quality).
- Whether to open-source the eval set.
