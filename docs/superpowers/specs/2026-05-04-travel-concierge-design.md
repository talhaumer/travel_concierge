# Travel Concierge — State-of-the-Art Design Spec

**Date:** 2026-05-04
**Status:** Approved
**Purpose:** Real product — local deployment first, browser-based web app

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Next.js Frontend                      │
│  Search Form → Live Agent Stream → Itinerary Display    │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP + SSE (Server-Sent Events)
┌──────────────────────▼──────────────────────────────────┐
│                 FastAPI Backend (async)                   │
│  POST /api/plan  →  GET /api/stream/{session_id}         │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│            Async LangGraph Agent Pipeline                 │
│  UserInput → Research → Planner → Reviewer → Writer      │
│                                        → CostEstimator   │
└──┬──────────┬────────┬────────┬─────────────────────────┘
   │          │        │        │
Nominatim  Open-    REST     TransitLand   Amadeus(free)
(places +  Meteo   Countries  (transit)   (flights)
 hotels)  (weather)
```

### Key Architectural Decisions

- **SSE streaming** — as each agent completes, a push event reaches the browser in real time. Users see live progress ("Researching Paris...", "Found weather data...", "Building Day 1...") instead of a spinner.
- **Session-based** — each trip plan gets a UUID. `POST /api/plan` starts a background task and returns `session_id`. The frontend subscribes to `GET /api/stream/{id}` for live events.
- **Async throughout** — all HTTP tool calls use `httpx.AsyncClient`, all agents are async, FastAPI runs on `uvicorn`. No blocking calls on the event loop.
- **Free APIs only** — Nominatim (places + hotels), Open-Meteo (weather), REST Countries, TransitLand, Amadeus free tier (2,000 flight searches/month), exchangerate.host (currency).

---

## 2. Backend — FastAPI + Async LangGraph

### Project Structure

```
travel_concierge/
├── backend/
│   ├── main.py              # FastAPI app, routes
│   ├── session.py           # In-memory session store (dict + asyncio.Queue)
│   ├── stream.py            # SSE event builder & generator
│   └── schemas.py           # Request/response Pydantic models
├── src/
│   ├── agents.py            # All 6 agents rewritten as async
│   ├── graph.py             # Async LangGraph graph, emits SSE progress events
│   ├── state.py             # Extended TravelState (adds hotels, flights, cost)
│   ├── constants.py         # Unchanged
│   ├── fallbacks.py         # Async retry/circuit-breaker decorators
│   ├── observability.py     # Unchanged
│   ├── guardrails/          # Unchanged
│   └── tools/
│       ├── places.py        # Async httpx, extended fallback data (20+ cities)
│       ├── weather.py       # Async httpx
│       ├── country.py       # Async httpx
│       ├── transit.py       # Async httpx
│       ├── currency.py      # Async httpx, exchangerate.host
│       ├── hotels.py        # NEW — Nominatim amenity=hotel search
│       ├── flights.py       # NEW — Amadeus free tier (replaces stub)
│       └── distance_calc.py # NEW — haversine distance between coordinates
├── frontend/                # Next.js app
├── tests/                   # Full test suite
├── requirements.txt         # Add: fastapi, uvicorn, httpx, pytest-asyncio, pytest-respx
└── CLAUDE.md
```

### API Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/plan` | POST | Accept trip query, start background agent run, return `session_id` |
| `/api/stream/{session_id}` | GET | SSE stream — one event per agent step, then final JSON |
| `/api/health` | GET | Liveness check |

### SSE Event Schema

```
event: agent_start    data: {"agent": "research",  "message": "Searching Paris..."}
event: agent_done     data: {"agent": "research",  "message": "Found 8 attractions"}
event: agent_start    data: {"agent": "planner",   "message": "Building itinerary..."}
event: complete       data: { ...full itinerary JSON... }
event: error          data: {"message": "...", "code": "...", "retry": bool}
```

### TravelState Additions

On top of existing fields, add:
- `hotels: list[HotelOption]` — name, estimated_price_per_night, address, coordinates, rating (Optional[float] = None — Nominatim returns no ratings)
- `flights: list[FlightOption]` — real Amadeus data (airline, price, departure/arrival, duration)
- `cost_estimate: CostEstimate` — flights_total, hotels_total, daily_spend_budget (user's per-day food + activities allowance = total_budget / num_days), grand_total, over_budget flag
- `map_points: list[MapPoint]` — lat/lng + label for every place, hotel, airport

---

## 3. Frontend — Next.js + Tailwind

### App Structure

```
frontend/
├── app/
│   ├── page.tsx                  # Home — hero + search form
│   ├── plan/[sessionId]/
│   │   └── page.tsx              # Live results page
│   └── layout.tsx                # Root layout, fonts, global styles
├── components/
│   ├── SearchForm.tsx            # Origin, destination, dates, budget, passengers, trip type
│   ├── AgentProgress.tsx         # Live streaming steps with animated indicators
│   ├── ItineraryCard.tsx         # One card per day, morning/afternoon/evening timeline
│   ├── FlightCard.tsx            # Flight options with price badges
│   ├── HotelCard.tsx             # Hotel options with star ratings
│   ├── WeatherBadge.tsx          # Temperature + condition chip
│   ├── CostSummary.tsx           # Breakdown: flights + hotels + daily budget + total
│   ├── MapView.tsx               # Leaflet.js map with all place/hotel pins (free, no key)
│   └── ExportButton.tsx          # Download itinerary as PDF (react-pdf, client-side)
├── lib/
│   ├── stream.ts                 # SSE client hook (useEventSource)
│   └── api.ts                    # fetch wrappers for /api/plan
└── public/
    └── og-image.png
```

### User Journey

1. **Home page** — clean hero with one search form (origin, destination, dates, budget, passengers, trip type)
2. **Submit** → navigates to `/plan/[sessionId]` immediately
3. **Live progress** — agent steps stream in with animated indicators:
   ```
   [✓] Extracting trip details...
   [⟳] Researching Paris weather, attractions, transit...
   [⟳] Searching flights & hotels...
   [⟳] Building your 3-day itinerary...
   ```
4. **Itinerary reveals** section by section as each SSE event arrives (Framer Motion animations)
5. **Final state** — full itinerary with day cards, flights, hotels, map, cost summary, PDF export

### Design System

- Tailwind CSS — warm travel palette: deep blue (`#1E3A5F`), amber (`#F59E0B`), cream (`#FEFCE8`)
- Framer Motion — card reveal animations as sections load
- Lucide icons — consistent iconography
- Leaflet.js + OpenStreetMap tiles — interactive map, zero API key
- react-pdf — client-side PDF generation, no server involvement
- Mobile-first, fully responsive
- No paid component libraries

---

## 4. Agent Upgrades

### UserInputAgent
- Extracts trip type: honeymoon, family, solo, business
- Validates dates are in the future, budget is a positive number
- Returns structured error if query is too vague, prompting user for specifics

### ResearchAgent
- Runs all 6 tool calls concurrently via `asyncio.gather()` (places, hotels, weather, country, transit, flights)
- Emits one SSE `agent_start` event per tool as it begins
- Extended fallback data covering 20+ cities (currently only Paris + London)

### PlannerAgent
- Respects trip type: honeymoon → romantic restaurants + sunset viewpoints; family → kid-friendly; solo → flexible pace
- Groups activities by geography — nearby places scheduled on the same day
- 3 slots per day: morning / afternoon / evening
- Integrates hotel check-in note on Day 1 and check-out on last day

### ReviewerAgent
- Checks activity variety per day (flags all-museum days)
- Checks geographic clustering (flags days with places >50km apart)
- Checks budget alignment — flags if cost estimate exceeds user budget
- Returns specific fix instructions to PlannerAgent; re-plan loop capped at 2 iterations

### WriterAgent
- Produces full `FinalOutput` with all sections: itinerary, flights, hotels, cost estimate, map points, weather, transit tips
- Adds "why visit" context note per activity from country/place data
- PII redaction applied before output (existing, kept)

### CostEstimatorAgent (new — 6th agent, runs after Writer)
- Sums: flight estimate + (hotel_per_night × num_days) + (daily_budget × num_days)
- Flags over-budget with one specific savings suggestion (e.g., "choosing a 3-star hotel saves $180")
- Skipped gracefully if flights or hotels were not retrieved

---

## 5. Free API Integrations

| Tool | API | Free Limit | Data Retrieved |
|---|---|---|---|
| Places | Nominatim (OSM) | Unlimited (1 req/s) | Attractions, coordinates |
| Hotels | Nominatim amenity=hotel | Unlimited (1 req/s) | Name, address, coordinates |
| Weather | Open-Meteo | Unlimited | 7-day forecast, temp, conditions |
| Country | REST Countries | Unlimited | Capital, currency, language, timezone |
| Transit | TransitLand v2 | 1,000 req/day | Transit systems, recommendations |
| Flights | Amadeus free tier | 2,000 req/month | Real airline, price, times |
| Currency | exchangerate.host | Unlimited | Live exchange rates |
| Map | Leaflet.js + OSM tiles | Unlimited | Interactive map |
| Distance | Haversine (local) | Unlimited | Distance between coordinates |
| PDF | react-pdf (client-side) | Unlimited | Browser-generated PDF |

### Environment Variables

```
# Required
GROQ_API_KEY=              # LLM (existing)
AMADEUS_CLIENT_ID=         # Flights — free tier at developers.amadeus.com
AMADEUS_CLIENT_SECRET=     # Flights — free tier

# Optional
LANGCHAIN_API_KEY=         # LangSmith tracing (existing)
```

All other APIs require zero keys.

### Hotel Pricing Strategy
Nominatim returns name/address/coordinates only — no pricing. Prices estimated from destination cost-of-living tier (hardcoded: budget/mid/luxury by city). UI clearly labels these as "estimated price" — no real booking implied.

### Amadeus Fallback
If Amadeus quota is exceeded or credentials missing, pipeline falls back to 3 realistic dummy flights. UI shows an "estimated" badge on flight cards.

---

## 6. Testing

### Structure

```
tests/
├── unit/
│   ├── test_agents.py           # Each agent in isolation, mocked tools
│   ├── test_tools/
│   │   ├── test_places.py       # Nominatim responses + fallback trigger
│   │   ├── test_weather.py      # Open-Meteo parsing + fallback
│   │   ├── test_flights.py      # Amadeus response parsing + fallback
│   │   ├── test_hotels.py       # Nominatim hotel search + price tiers
│   │   ├── test_currency.py     # Rate conversion logic
│   │   └── test_distance.py     # Haversine math assertions
│   ├── test_guardrails.py       # PII redaction, moderation, schema validation
│   ├── test_fallbacks.py        # Retry decorator, circuit breaker behaviour
│   └── test_cost_estimator.py   # Budget math and over-budget flagging
├── integration/
│   ├── test_graph.py            # Full LangGraph pipeline, mocked LLM
│   └── test_api.py              # FastAPI endpoints via httpx.AsyncClient
├── e2e/
│   └── test_paris_trip.py       # Full real run: Paris 3-day trip, asserts output shape
└── conftest.py                  # Shared fixtures: mock state, mock API responses
```

### Principles

- Unit tests mock all external HTTP with `pytest-respx`
- Integration tests mock only the LLM; real tool logic runs
- E2E tests hit real APIs — marked `@pytest.mark.e2e`, skipped unless `--e2e` flag passed
- `pytest-asyncio` for all async tests
- Coverage target: 80% on `src/` and `backend/`
- `pytest tests/unit tests/integration` runs cleanly with zero API keys

---

## 7. Error Handling & Resilience

### Per-Tool
- Async exponential backoff retry (max 3 attempts, 2s base delay)
- Circuit breaker per tool — trips after 3 consecutive failures, resets after 60s
- Every tool has hardcoded fallback — pipeline never fully halts
- Amadeus quota exceeded → dummy flights, UI shows "estimated" badge

### Agent-Level
- Reviewer sends Planner back for re-plan (max 2 iterations, then accept best result)
- Zero places retrieved → PlannerAgent uses extended 20+ city fallback data
- LLM errors (Groq timeout/rate limit) → retry up to 3 times with 2s backoff

### API-Level (FastAPI)
- All error responses: `{"error": "...", "code": "...", "retry": bool}`
- SSE stream always terminates with `event: complete` or `event: error` — no hanging connections
- Session TTL: 30 minutes, background cleanup task
- Request timeout: 60s hard limit per `/api/plan`

### Frontend
- SSE disconnect → auto-reconnect up to 3 times with exponential backoff
- Partial results rendered as each agent completes — user sees content even on partial failure
- Missing data sections (e.g., no flights) → panel hidden gracefully, not crash

### Removals
- `distance_calc.py` empty placeholder → replaced with real haversine implementation
- `mcp_client.py` minimal stub → removed (out of scope)
- `search.py` mock → removed (superseded by real tools)

---

## 8. Out of Scope (This Version)

- User authentication / saved trips
- Real hotel booking or flight booking
- Deployment (Vercel / Railway / Fly.io) — local only
- Multi-language UI
- Mobile app
