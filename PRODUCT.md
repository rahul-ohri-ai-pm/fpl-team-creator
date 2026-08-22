# FPL Team Creator — Product Context

## Product Definition

**The fastest, simplest and most trustworthy FPL decision engine on the web.**

Every gameweek, tell users the one move that matters most — and prove why.

---

## Core Promise

> **Open the site. See what you should do. Understand why. Decide.**

Not:
- "Here are 50 transfer options."
- "Explore this dashboard."
- "Read this analysis."

Instead:
- "Your best move: Player A → Player B. +7.8 projected points. 87% confidence. Here's why."

---

## Target User

Fantasy Premier League players who:
- Want trustworthy recommendations they can act on immediately
- Don't have time to analyze 20 options
- Care about decision quality over feature count
- Will pay for accuracy they can verify

---

## Competitive Position

**vs. FPL.team** → Simpler, decision-first (not feature-heavy)
**vs. Onside Arena** → Owned decision layer, stronger explainability
**vs. FPLXI** → Add explainability, scenarios, personalization (keep simplicity)
**vs. Fantasy Football Hub** → Product-first, not content-first

---

## MVP Scope (Phase 1)

### Input
- Import by FPL manager ID
- Screenshot import (vision/OCR)
- Manual squad builder
- Auto-detect: bank, free transfers, captain, formation

### Output (per user input)
- Team score (0–100)
- Biggest weakness (one sentence)
- **Primary recommendation** (visually dominant)
  - Player A → Player B
  - +X projected points (6-GW basis)
  - Confidence: X%
  - Why (4–5 bullets: fixtures, xGI, price, ownership, minutes)
  - Risk (key downside)
- 2 alternatives (ranked by upside)
- Starting XI
- Captain + Vice Captain
- Bench order

### Platform
- Mobile-first responsive web app
- No app store (PWA)
- No mandatory signup before first value
- Shareable team URL (`/team/abc123`)

---

## Monetisation (Phase 2)

| Tier | Price | Features |
|------|-------|----------|
| **Free** | £0 | Team analysis + 1 rec/GW + shareable team + screenshot import |
| **Season Pass** | £19.99–£29.99/season | Unlimited recs + 6-GW optimizer + chip planner + scenario simulator + mini-league analysis |
| **Pro** | £39.99–£59.99/season | Season Pass + real-time alerts + advanced model data + rival analysis + API/MCP access |

---

## Key Design Decisions

### Decision-first, not dashboard-first
Default screen shows:
1. **One recommendation** (bold, clear)
2. **Why** (concise evidence)
3. **Confidence** (explicit uncertainty)
4. **Risk** (be honest)
5. **Alternatives** (for exploration)

Not: 40 charts, 12 tables, 8 filters.

### Allowed to recommend "do nothing"
- If current squad is optimal, system says so
- This builds trust more than always suggesting changes

### Explain confidence, not just prediction
Every recommendation includes:
- Confidence % (87%, not 0.87)
- Expected range (+3 to +12 pts)
- Main uncertainty (e.g., "European rotation")
- Key assumption (e.g., "no injury news")

### Mobile-first UX
- Touch-optimized
- Readable on 375px screens
- Single-column layouts
- Tap, not hover

### No hidden complexity
If user wants to see assumptions, drill-down is available:
- What's your xGI model?
- How's minutes confidence calculated?
- Which fixtures matter most?

But default view is: *Here's what to do.*

---

## Acquisition Strategy (Phase 2+)

### Organic / SEO
Pages around:
- "Best FPL team for GW1"
- "Best FPL defenders"
- "Haaland vs Isak"
- "Best FPL captain GW4"

### Shareable results
Every team analysis generates:
> "Your FPL team scored 84/100. Best move: Smith → Jones (+7.8 pts)."

Shareable via WhatsApp, Reddit, Discord, X.

### AI discovery
Authoritative pages AI systems can cite:
- Player profiles
- Club profiles
- Gameweek analysis
- Competitor comparisons

### Public accuracy ledger (Phase 3)
Track every recommendation:
- Predicted: +7.8 pts
- Actual: +6.0 pts
- Confidence: 87%
- Correct: Yes (within range)

This becomes a marketing asset.

---

## Strategic Moat (Long-term)

1. **Historical prediction record** — Verifiable accuracy
2. **Proprietary data** — Preseason minutes, reliability blending
3. **User decision history** — Personalized recommendations
4. **Behavioral model** — Learn user preferences over time
5. **Distribution** — SEO, social, AI referrals
6. **Brand authority** — "The trustworthy FPL engine"

---

## Technical Foundation (Existing)

✅ Backend engine (engine/fetch.py, engine/score.py, engine/optimize.py)
✅ Preseason data integration
✅ Weekly performance tracking
✅ Prediction → actual evaluation framework

❌ Frontend UI
❌ Team import flows
❌ Shareable URLs
❌ Payment/tier system
❌ Public dashboard

---

## Success Metrics (Phase 1)

**Activation**
- User sees recommendation within 60 sec of landing
- Team analysis → recommendation view rate >70%

**Engagement**
- Screenshot import sessions
- Manual builder starts
- Share URL clicks

**Trust**
- Recommendation acceptance rate
- "Useful?" feedback >80%

**Outcome** (Phase 2)
- Predicted vs actual calibration
- Recommendation accuracy tracking

---

## Design Mode

**Mode**: Operate (task completion: "What should I transfer?")

Users come to complete a specific FPL decision, not to explore or learn.

---

## Constraints & Decisions

- **No real-time updates in free tier** (prevents data staleness)
- **Deadline lockdown at T-30m** (recommendations freeze)
- **Screenshot import has no OCR cost** (free for all tiers)
- **Bank/transfers are user-provided** (we don't sync FPL account)
- **No betting, gambling, or money-related claims** (regulatory)

---

## Terminology

| Term | Definition |
|------|-----------|
| **Recommendation** | Primary suggestion to improve team (1 per view) |
| **Alternative** | Secondary/tertiary option (2 shown) |
| **Confidence** | Model's certainty in the recommendation (0–100%) |
| **Horizon** | 6-gameweek lookahead (basis for fixture weighting) |
| **xGI** | Expected goal involvements (used for new players) |
| **Reliability** | Probability player starts (based on minutes history) |

---

## Brand Voice

- Confident but honest
- "87% confident" not "definitely"
- "Main uncertainty: European rotation"
- "This could cost 2 points" (acknowledge downside)
- Avoid hype: "Revolutionary AI" → "Transparent process"

---

## Next Steps

1. Design MVP interface (reference/new-work.md → surface brief)
2. Build team import flows
3. Wire recommendation engine to UI
4. Ship screenshot import + share URLs
5. Measure activation and calibration
6. Iterate before Phase 2 paid tier

