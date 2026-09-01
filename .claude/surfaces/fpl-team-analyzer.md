# FPL Team Analyzer — MVP Surface Brief

## Surface Name
FPL Team Analyzer (web app, mobile-first PWA)

## Mode
**Operate** — Users complete a specific task: "What should I transfer?"

## Entry Points

### Primary (80% of traffic)
1. Homepage → "Analyze your team"
2. Screenshot import → instant analysis
3. FPL manager ID → auto-fetch and analyze

### Secondary
- Shared team URL → view previous analysis
- Manual squad builder → specify 15 players

---

## Default Flow (Mobile-First)

```
┌─────────────────────────────────┐
│  FPL TEAM ANALYZER              │
│                                 │
│  📸 Upload screenshot           │ ← Primary CTA
│                                 │
│  ─────────────────────────────  │
│                                 │
│  Analyze by FPL ID              │
│  [Input field] [Analyze]        │
│                                 │
│  ─────────────────────────────  │
│                                 │
│  Build team manually            │
│                                 │
└─────────────────────────────────┘
        ↓ (user selects input method)
        
┌─────────────────────────────────┐
│  YOUR TEAM                      │
│                                 │
│  Rating: 82/100                 │
│  💪 Strong                      │
│                                 │
│  ─────────────────────────────  │
│                                 │
│  ⚠️ BIGGEST PROBLEM             │
│  Defence projected to lose      │
│  8.4 pts over next 4 GWs        │
│                                 │
└─────────────────────────────────┘
        ↓
        
┌─────────────────────────────────┐
│  YOUR BEST MOVE                 │
│  ═════════════════════════════  │
│                                 │
│  🔄 Calafiori → Player X        │
│                                 │
│  ✨ +7.8 projected points       │
│  📊 Confidence: 87%             │
│                                 │
│  ✓ Better fixtures              │
│  ✓ 92% start probability        │
│  ✓ Higher xGI                   │
│  ✓ £0.3m cheaper                │
│                                 │
│  ⚠️ RISK: Low ownership (7.2%)   │
│                                 │
│  [✓ MAKE THIS MOVE]             │
│  [? WHY THIS?]                  │
│  [⚙️ OPTIONS]                    │
│                                 │
└─────────────────────────────────┘
        ↓
        
┌─────────────────────────────────┐
│  OTHER OPTIONS                  │
│                                 │
│  1️⃣  Player Y    +5.9 pts       │
│  2️⃣  Player Z    +4.7 pts       │
│                                 │
│  [🔄 USE ALTERNATIVE]           │
│                                 │
└─────────────────────────────────┘
        ↓
        
┌─────────────────────────────────┐
│  KEEP YOUR TEAM?                │
│                                 │
│  This recommendation is strong, │
│  but holding is also valid if   │
│  you prefer to bank the         │
│  transfer.                      │
│                                 │
│  [✓ KEEP AS-IS]                 │
│                                 │
└─────────────────────────────────┘
```

---

## Key Screens

### 1. Homepage
**Purpose**: Zero-friction entry point

Content:
- Hero: "Know your next FPL move"
- 3 input methods (screenshot, ID, manual)
- Trust signals (e.g., "87% avg confidence")
- No login required

Design:
- Mobile: Single column, full-width CTAs
- Desktop: Side-by-side options
- Screenshot upload prominent (lowest friction)

### 2. Analysis Loading
**Purpose**: Show work in progress

Content:
- Fetching team...
- Calculating projections...
- Generating recommendation...

Design:
- Progress indicator
- Estimated time to completion
- Reassuring copy

### 3. Team Rating Card
**Purpose**: Give user confidence score before showing recommendation

Content:
- Overall score (0–100)
- Health summary (Good / Concerning / Critical)
- One-line biggest problem

Design:
- Large, colorful score circle
- Traffic-light indicators (red/yellow/green)
- Tappable to see position breakdown

### 4. Recommendation Card (Most Important)
**Purpose**: Single, clear, actionable decision

Content:
- Visual: Player A → Player B
- Headline: +X pts (6-week horizon)
- Confidence: X%
- Why (4 bullets, verified as true)
- Risk (key downside)
- CTAs: Accept / Explore alternatives / Keep team

Design:
- Largest section of the screen
- Bold typography
- Color-coded confidence (green 80%+, yellow 60-80%, red <60%)
- Clear button hierarchy

### 5. Alternatives Panel
**Purpose**: Show #2 and #3 options for comparison

Content:
- Option 1: +5.9 pts, 72% confidence
- Option 2: +4.7 pts, 68% confidence
- Each tappable to compare with primary

Design:
- Smaller cards below main recommendation
- Horizontal swipe on mobile
- Shows differential upside clearly

### 6. Keep Team Option
**Purpose**: Permission to "do nothing" (trust-building)

Content:
- "Keeping your team is fine because..."
- Explains why holding is valid
- Maybe: confidence is only 60%, fixture run is mixed

Design:
- Prominent but secondary
- Use cautious language ("also valid", "reasonable if")

### 7. Expanded Explanation (Tap to Reveal)
**Purpose**: Drill into "why" without cluttering default view

Content:
- Full fixture analysis (4 fixtures, FDR for each)
- xGI calculation (both players, explanation)
- Minutes risk (injury flags, rotation history)
- Ownership implications
- Set-piece roles (if relevant)

Design:
- Modal or slide-up drawer
- Same color/type as card, expandable
- Links to player details

### 8. Player Details Page
**Purpose**: Deep dive on player (optional drill-down)

Content:
- Last 3 season stats
- Current season form
- Injury status + FPL flag
- Fixture run (next 6 GWs)
- Ownership (live from FPL API)
- Comparison to alternatives

Design:
- Full-screen modal or new route
- Table layout for mobile (stack vertically)
- Tap to close

### 9. Share Screen
**Purpose**: Generate shareable team URL

Content:
- "Your team scored 84/100"
- "Best move: Smith → Jones (+7.8 pts)"
- QR code + URL
- Share buttons (WhatsApp, Reddit, X, copy link)

Design:
- Highlight card
- Generate after recommendation viewed
- Deep link: `fpl.teamcreator.app/team/abc123?gw=1&ts=1629...`

### 10. Team Builder (Manual Entry)
**Purpose**: Let users construct a custom squad

Content:
- Position slots (2 GK, 5 DEF, 5 MID, 3 FWD)
- Player search by name or team
- Price calculator
- Formation visualizer
- Validate legality (club limit, budget)

Design:
- Card-based (one position at a time on mobile)
- Auto-fill most likely players
- Show remaining budget in real-time
- Formation toggle (3-4-3, 3-5-2, 4-3-3, etc.)

---

## Navigation Structure

```
/                           (homepage)
  ├── /analyze              (input methods)
  ├── /team/[id]            (analysis result, shareable)
  ├── /team/[id]/expand     (drill-down explanation)
  ├── /player/[pid]         (player details)
  ├── /build                (manual team builder)
  └── /about                (methodology + trust)
```

---

## Desktop Responsiveness

| Breakpoint | Changes |
|-----------|---------|
| 375px+ (mobile) | Single column, full-width buttons, card layout |
| 768px+ (tablet) | 2-column grid for alternatives, side panels |
| 1024px+ (desktop) | 3-column: team summary, recommendation, alternatives side-by-side |

---

## Color & Typography

### Mode: Operate (Task-focused)
- Palette: Neutral + accent (action color)
- Typography: Readable, high contrast
- Buttons: Clear, obvious affordance
- Status: Color-coded confidence (red/yellow/green)

### Specific Colors
- **Confidence 80%+**: Green (#10b981)
- **Confidence 60-80%**: Yellow (#f59e0b)
- **Confidence <60%**: Red (#ef4444)
- **Accent**: Brand blue (action)
- **Risk**: Red/orange highlight
- **Recommendation**: Bold, high contrast background

---

## Microcopy

**Homepage**
- "Know your next FPL move"
- "See what to transfer. Understand why. Decide."

**Recommendation Headline**
- "Your best move"
- "This transfer could help"
- Avoid: "AI recommends", "Algorithm says"

**Confidence**
- "87% confident"
- Avoid: "High confidence", "Our AI thinks"

**Risk Section**
- "Main downside: Low ownership"
- "Key uncertainty: European rotation"
- "Be aware: Price could change"

**Keep Team**
- "Keeping your team is also valid"
- "Holding is reasonable if you prefer to preserve transfers"

---

## Interaction Patterns

### Primary CTA
- **Button state**: Active (high contrast)
- **Hover**: Slight color shift, no animation
- **Tap feedback**: Visual feedback (0.2s)
- **Copy**: Action-oriented ("Make this move", not "Submit")

### Secondary CTAs
- **Drill-down**: "Why this?" → expand card
- **Alternative**: Tap card to swap with primary
- **Share**: "Share team" → modal

### Loading
- Skeleton screens (don't show loading spinners)
- Progressive disclosure (show rating, then recommendation, then alternatives)

---

## Accessibility

- **Color**: Not sole indicator (use icons + text)
- **Contrast**: WCAG AA minimum (4.5:1)
- **Touch targets**: 48px minimum on mobile
- **Keyboard**: Full navigation without mouse
- **Screen reader**: Semantic HTML, alt text on all icons

---

## Performance Targets

- **First paint**: <2s on 4G
- **Recommendation visible**: <3s on 4G
- **Share URL load**: <1s (cached analysis)
- **No JavaScript errors** on first load

---

## Error States

| Scenario | Message |
|----------|---------|
| Invalid FPL ID | "Manager not found. Check the ID and try again." |
| Screenshot fails to parse | "Couldn't read the screenshot. Try uploading a clearer image or enter manually." |
| Illegal squad (user-entered) | "This squad breaks FPL rules: 4 from [Club]. Max is 3." |
| Network error | "Couldn't reach FPL data. Check your connection and retry." |
| Gameweek locked | "Recommendations locked 30 min before deadline. Check back after GW closes." |

---

## Next Phase (Season Pass Features)

- 🔒 Unlock multi-GW optimizer
- 🔒 Chip planner (wildcard, bench boost strategy)
- 🔒 Scenario simulator ("What if Haaland injured?")
- 🔒 Mini-league analysis ("Chase" vs "Protect" mode)
- 🔒 Historical recommendation tracking

---

## Success Criteria (Phase 1)

✓ User sees recommendation within 60 seconds
✓ Recommendation acceptance rate >60%
✓ Share URL clicks >30% of analyzed teams
✓ Screenshot import success rate >85%
✓ No critical errors on first load
✓ Mobile test (375px width) fully functional

