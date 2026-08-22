# FPL Team Analyzer — Frontend Setup

## Architecture

**Tech Stack:**
- React 19 + Vite (bundler)
- React Router 7 (routing)
- Tailwind CSS 4 (styling)
- Lucide React (icons)
- Axios (HTTP client)

**File Structure:**
```
src/
├── main.jsx              # Vite entry point
├── App.jsx               # Router setup
├── index.css             # Tailwind + component library
├── pages/
│   ├── HomePage.jsx      # Landing with 3 input methods
│   ├── AnalysisPage.jsx  # Recommendation display
│   └── TeamPage.jsx      # Shareable team results
└── components/
    ├── ScreenshotUpload.jsx    # Image OCR input
    ├── FPLIdInput.jsx          # Manager ID input
    ├── ManualTeamBuilder.jsx   # 15-player selector
    ├── TeamRatingCard.jsx      # 0-100 score display
    ├── RecommendationCard.jsx  # Primary recommendation
    ├── AlternativesPanel.jsx   # #2 and #3 options
    ├── KeepTeamOption.jsx      # Permission to hold
    ├── LoadingScreen.jsx       # Analysis progress
    └── ErrorScreen.jsx         # Error handling
```

## Development

### Install dependencies
```bash
npm install
```

### Run dev server (with HMR)
```bash
npm run dev
# Frontend: http://localhost:5173
# Proxies API calls to http://localhost:8000
```

### Build for production
```bash
npm run build
# Output: dist/
```

### Preview production build
```bash
npm run preview
```

## Backend Integration

Frontend calls `/api/*` endpoints. Vite proxies these to `http://localhost:8000` (configured in `vite.config.js`).

**Required API endpoints:**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/analyze` | POST | Score squad + get recommendations |
| `/api/fetch-team` | POST | Fetch FPL squad by manager ID |
| `/api/players` | GET | List all players (for manual builder) |
| `/api/ocr-screenshot` | POST | Parse screenshot (TODO) |

**Example request (POST /api/analyze):**
```json
{
  "squad": {
    "GK": [{"id": 1, "name": "Raya", "team": "ARS", "price": 45}],
    "DEF": [{"id": 2, "name": "Gabriel", ...}],
    "MID": [...],
    "FWD": [...]
  },
  "bank": 2.5,
  "free_transfers": 1
}
```

**Example response (POST /api/analyze):**
```json
{
  "team_id": "generated_1692806400",
  "team_rating": 82,
  "position_breakdown": {"GK": 75, "DEF": 80, "MID": 85, "FWD": 70},
  "biggest_problem": "Defence projected to lose 8.4 pts over next 4 GWs",
  "recommendation": {
    "player_out": {"id": 1, "name": "Calafiori", "team": "ARS"},
    "player_in": {"id": 2, "name": "Player X", "team": "CHE"},
    "projected_points": 7.8,
    "confidence": 87,
    "why_bullets": ["Better fixtures", "92% start probability", ...],
    "risk": "Low ownership (7.2%)",
    "fixture_analysis": "...",
    "xgi_explanation": "...",
    "minutes_analysis": "...",
    "ownership_note": "..."
  },
  "alternatives": [...],
  "keep_reasoning": "Your squad is well-balanced...",
  "timestamp": "1692806400"
}
```

## Frontend Flows

### 1. Homepage (/)
Three input methods, no login:
- **Screenshot upload** → OCR parsing → direct analysis
- **FPL manager ID** → API fetch → analysis
- **Manual 15-player builder** → squad validation → analysis

### 2. Analysis Page (/analyze)
Shows:
- Team Rating Card (0-100 score + position breakdown)
- Recommendation Card (primary transfer + why + risk)
- Alternatives Panel (#2 and #3 options)
- Keep Team Option (permission to hold)
- Share button

### 3. Share Page (/team/:teamId)
Displays:
- Cached analysis result (from localStorage or URL)
- Pre-filled share message
- Social share buttons (WhatsApp, Reddit, X, copy link)

## Performance Targets

- **First paint:** <2s on 4G
- **Recommendation visible:** <3s on 4G
- **No JavaScript errors** on first load
- **Lighthouse score:** 85+ on desktop, 70+ on mobile

## Responsive Design

| Breakpoint | Changes |
|-----------|---------|
| 375px+ | Single column, full-width buttons |
| 768px+ | 2-column grid for alternatives |
| 1024px+ | 3-column: team, recommendation, alternatives side-by-side |

## Next Steps

1. ✅ Core component structure
2. ⏳ Backend API implementation (web_api.py)
3. ⏳ Screenshot OCR integration (Tesseract.js)
4. ⏳ Shareable URL + localStorage system
5. ⏳ Responsive testing (375px → 1024px+)
6. ⏳ Analytics tracking (activation, engagement, conversion)
7. ⏳ Share flow implementation

## Development Notes

- **No build errors:** All components use standard React patterns
- **Mobile-first:** All layouts start at 375px
- **Accessibility:** WCAG AA contrast, 48px touch targets, semantic HTML
- **Icon library:** Lucide React (21 icons currently used, all included)
