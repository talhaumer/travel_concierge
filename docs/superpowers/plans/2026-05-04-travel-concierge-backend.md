# Travel Concierge — Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the existing synchronous LangGraph pipeline into a production-ready async FastAPI backend with SSE streaming, real free-tier API integrations, a 6th CostEstimatorAgent, and a full test suite.

**Architecture:** Async FastAPI exposes two endpoints (`POST /api/plan`, `GET /api/stream/{session_id}`). Each plan request starts a background LangGraph run; agents emit progress events into a per-session `asyncio.Queue`; the SSE endpoint drains that queue to the browser. All external HTTP calls use `httpx.AsyncClient` with async retry/circuit-breaker decorators.

**Tech Stack:** Python 3.11+, FastAPI 0.115, uvicorn, httpx 0.27, LangGraph 0.2, langchain-groq, Pydantic v2, pytest 8, pytest-asyncio, pytest-respx

---

## File Map

### New Files
- `backend/__init__.py`
- `backend/main.py` — FastAPI app, routes, startup
- `backend/session.py` — in-memory session store with `asyncio.Queue`
- `backend/stream.py` — SSE event helpers
- `backend/schemas.py` — Pydantic request/response models
- `src/tools/hotels.py` — Nominatim hotel search + price tiers
- `src/tools/flights.py` — Amadeus free-tier flight search + fallback
- `tests/__init__.py`
- `tests/conftest.py` — shared fixtures
- `tests/unit/__init__.py`
- `tests/unit/test_state.py`
- `tests/unit/test_distance.py`
- `tests/unit/test_tools/test_places.py`
- `tests/unit/test_tools/test_weather.py`
- `tests/unit/test_tools/test_hotels.py`
- `tests/unit/test_tools/test_flights.py`
- `tests/unit/test_tools/test_currency.py`
- `tests/unit/test_guardrails.py`
- `tests/unit/test_fallbacks.py`
- `tests/unit/test_agents.py`
- `tests/integration/__init__.py`
- `tests/integration/test_api.py`

### Modified Files
- `requirements.txt` — add fastapi, uvicorn, httpx, pytest-asyncio, pytest-respx
- `src/state.py` — add HotelOption, CostEstimate, MapPoint; extend TravelState
- `src/fallbacks.py` — add async retry + async circuit-breaker decorators
- `src/tools/distance_calc.py` — full haversine implementation
- `src/tools/places.py` — async httpx, 6-city fallback
- `src/tools/weather.py` — async httpx
- `src/tools/country.py` — async httpx
- `src/tools/transit.py` — async httpx
- `src/tools/currency.py` — async httpx + exchangerate.host
- `src/tools/__init__.py` — export new tools
- `src/agents.py` — all 6 agents rewritten as async
- `src/graph.py` — async LangGraph, astream-based SSE emission

### Deleted Files
- `src/tools/mcp_client.py`
- `src/tools/search.py`
- `src/tools/flight_tool.py`
- `src/tools/airport_tool.py`

---

## Task 1: Update requirements.txt

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Replace requirements.txt**

```
# Core
langchain==0.3.0
langchain-core==0.3.0
langchain-groq==0.2.0
langchain-community==0.3.0
langgraph==0.2.0
groq==0.11.0

# API server
fastapi==0.115.0
uvicorn[standard]==0.30.0

# Async HTTP
httpx==0.27.0

# Data
pydantic==2.9.0
python-dateutil==2.9.0
python-dotenv==1.0.1

# Observability
langsmith==0.1.0

# Dev / test
pytest==8.3.2
pytest-asyncio==0.24.0
pytest-respx==0.21.0
pytest-cov==5.0.0

# Notebook
jupyter==1.1.1
ipykernel==6.29.5
```

- [ ] **Step 2: Install**

```bash
pip install -r requirements.txt
```

Expected: no errors. `fastapi`, `httpx`, `pytest-asyncio` appear in `pip list`.

- [ ] **Step 3: Commit**

```bash
git add requirements.txt
git commit -m "feat: add fastapi, httpx, pytest-asyncio to dependencies"
```

---

## Task 2: Extend src/state.py

**Files:**
- Modify: `src/state.py`

- [ ] **Step 1: Write failing test**

Create `tests/unit/test_state.py`:

```python
from src.state import (
    TravelState, HotelOption, CostEstimate, MapPoint, StateStatus
)

def test_hotel_option_defaults():
    h = HotelOption(name="Hotel du Louvre", estimated_price_per_night=150.0, address="Paris")
    assert h.rating is None
    assert h.lat is None

def test_cost_estimate_fields():
    c = CostEstimate(
        flights_total=400.0, hotels_total=300.0,
        daily_spend_budget=100.0, grand_total=700.0, over_budget=False
    )
    assert c.savings_suggestion is None

def test_map_point_fields():
    p = MapPoint(lat=48.8566, lng=2.3522, label="Eiffel Tower", type="place")
    assert p.type == "place"

def test_travel_state_new_fields():
    s = TravelState()
    assert s.hotels == []
    assert s.cost_estimate is None
    assert s.map_points == []
    assert s.replan_count == 0
    assert s.replan_instructions is None

def test_place_details_has_coords():
    from src.state import PlaceDetails
    p = PlaceDetails(name="Louvre", type="museum", rating=4.8,
                     address="Paris", description="Art museum")
    assert p.lat is None
```

- [ ] **Step 2: Run test — expect failures**

```bash
pytest tests/unit/test_state.py -v
```

Expected: `AttributeError` or `ImportError` — HotelOption, CostEstimate, MapPoint not defined yet.

- [ ] **Step 3: Replace src/state.py**

```python
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel


class StateStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_HUMAN = "needs_human"


class ItineraryItem(BaseModel):
    time: str
    activity: str
    notes: Optional[str] = None


class PlaceDetails(BaseModel):
    name: str
    type: str
    rating: float
    address: str
    description: str
    lat: Optional[float] = None
    lng: Optional[float] = None


class HotelOption(BaseModel):
    name: str
    estimated_price_per_night: float
    address: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    rating: Optional[float] = None  # Nominatim does not provide ratings


class FlightOption(BaseModel):
    origin_airport: str
    destination_airport: str
    departure: str
    arrival: str
    price: str
    airline: str
    duration_minutes: Optional[int] = None
    is_estimated: bool = False  # True when Amadeus quota exceeded


class CostEstimate(BaseModel):
    flights_total: float
    hotels_total: float
    daily_spend_budget: float  # budget / num_days — user's per-day food + activities allowance
    grand_total: float
    over_budget: bool
    savings_suggestion: Optional[str] = None


class MapPoint(BaseModel):
    lat: float
    lng: float
    label: str
    type: str  # "place" | "hotel" | "airport"


class Airport(BaseModel):
    name: str
    code: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    source: str


class TravelState(BaseModel):
    user_input: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    date_of_travel: Optional[date] = None
    num_days: Optional[int] = None
    trip_type: Optional[str] = None  # "honeymoon"|"family"|"solo"|"business"
    num_passengers: Optional[int] = None
    budget: Optional[float] = None

    is_complete: bool = False
    status: StateStatus = StateStatus.RUNNING
    error: Optional[str] = None
    needs_fallback: bool = False
    circuit_breaker_count: int = 0
    replan_count: int = 0
    replan_instructions: Optional[str] = None

    retrieved_places: List[PlaceDetails] = []
    hotels: List[HotelOption] = []
    flights: List[FlightOption] = []
    day_plan: Dict[str, List[ItineraryItem]] = {}
    final_output: Optional[Dict[str, Any]] = None
    cost_estimate: Optional[CostEstimate] = None
    map_points: List[MapPoint] = []

    weather_info: Optional[Dict[str, Any]] = None
    country_info: Optional[Dict[str, Any]] = None
    transit_info: Optional[Dict[str, Any]] = None

    tools_used: List[str] = []
    violations: List[str] = []
    tool_errors: Dict[str, List[str]] = {}
```

- [ ] **Step 4: Run tests — expect pass**

```bash
pytest tests/unit/test_state.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add src/state.py tests/unit/test_state.py tests/unit/__init__.py tests/__init__.py
git commit -m "feat: extend TravelState with HotelOption, CostEstimate, MapPoint"
```

---

## Task 3: Implement src/tools/distance_calc.py

**Files:**
- Modify: `src/tools/distance_calc.py`
- Test: `tests/unit/test_distance.py`

- [ ] **Step 1: Write failing test**

Create `tests/unit/test_distance.py`:

```python
from src.tools.distance_calc import haversine

def test_same_point_is_zero():
    assert haversine(48.8566, 2.3522, 48.8566, 2.3522) == 0.0

def test_paris_to_london_approx():
    # Paris → London ≈ 340 km
    d = haversine(48.8566, 2.3522, 51.5074, -0.1278)
    assert 330 < d < 350

def test_new_york_to_london_approx():
    # NYC → London ≈ 5570 km
    d = haversine(40.7128, -74.0060, 51.5074, -0.1278)
    assert 5500 < d < 5650
```

- [ ] **Step 2: Run test — expect failures**

```bash
pytest tests/unit/test_distance.py -v
```

Expected: ImportError or AssertionError.

- [ ] **Step 3: Implement distance_calc.py**

```python
import math


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return great-circle distance in kilometres between two lat/lon points."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))
```

- [ ] **Step 4: Run tests — expect pass**

```bash
pytest tests/unit/test_distance.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add src/tools/distance_calc.py tests/unit/test_distance.py
git commit -m "feat: implement haversine distance calculator"
```

---

## Task 4: Rewrite src/fallbacks.py with async decorators

**Files:**
- Modify: `src/fallbacks.py`
- Test: `tests/unit/test_fallbacks.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/test_fallbacks.py`:

```python
import pytest
import asyncio
from src.fallbacks import async_retry, async_with_fallback

@pytest.mark.asyncio
async def test_async_retry_succeeds_on_first_try():
    calls = []
    @async_retry(max_retries=3, delay=0.01)
    async def fn():
        calls.append(1)
        return "ok"
    result = await fn()
    assert result == "ok"
    assert len(calls) == 1

@pytest.mark.asyncio
async def test_async_retry_retries_on_failure():
    calls = []
    @async_retry(max_retries=2, delay=0.01)
    async def fn():
        calls.append(1)
        if len(calls) < 3:
            raise ValueError("fail")
        return "ok"
    result = await fn()
    assert result == "ok"
    assert len(calls) == 3

@pytest.mark.asyncio
async def test_async_retry_raises_after_exhaustion():
    @async_retry(max_retries=2, delay=0.01)
    async def fn():
        raise RuntimeError("always fails")
    with pytest.raises(RuntimeError):
        await fn()

@pytest.mark.asyncio
async def test_async_with_fallback_uses_primary():
    @async_with_fallback(lambda: "fallback")
    async def fn():
        return "primary"
    assert await fn() == "primary"

@pytest.mark.asyncio
async def test_async_with_fallback_uses_fallback_on_error():
    @async_with_fallback(lambda: "fallback")
    async def fn():
        raise ValueError("fail")
    assert await fn() == "fallback"
```

- [ ] **Step 2: Run — expect failures**

```bash
pytest tests/unit/test_fallbacks.py -v
```

Expected: ImportError — `async_retry`, `async_with_fallback` not defined.

- [ ] **Step 3: Rewrite src/fallbacks.py**

```python
import asyncio
import time
from functools import wraps
from typing import Callable, Any, List, Dict
from .state import TravelState, StateStatus


def async_retry(max_retries: int = 3, delay: float = 2.0):
    """Async exponential-backoff retry decorator."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception:
                    if attempt == max_retries - 1:
                        raise
                    await asyncio.sleep(delay * (2 ** attempt))
        return wrapper
    return decorator


def async_with_fallback(fallback_func: Callable):
    """Async decorator — calls fallback_func() (sync or async) if primary raises."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                result = fallback_func(*args, **kwargs)
                if asyncio.iscoroutine(result):
                    return await result
                return result
        return wrapper
    return decorator


# ── Sync versions kept for backwards compatibility ──────────────────────────

def with_retry(max_retries: int = 2, delay: float = 1.0):
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exc = e
                    if attempt < max_retries:
                        time.sleep(delay * (2 ** attempt))
            raise last_exc
        return wrapper
    return decorator


def circuit_breaker(max_failures: int = 3):
    def decorator(func: Callable):
        failures = 0
        @wraps(func)
        def wrapper(state: TravelState, *args, **kwargs):
            nonlocal failures
            if failures >= max_failures:
                state.circuit_breaker_count += 1
                state.status = StateStatus.FAILED
                state.error = "Circuit breaker triggered"
                return state
            try:
                result = func(state, *args, **kwargs)
                failures = 0
                return result
            except Exception as e:
                failures += 1
                state.circuit_breaker_count += 1
                raise e
        return wrapper
    return decorator


def with_fallback(fallback_func: Callable):
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                return fallback_func(*args, **kwargs)
        return wrapper
    return decorator


def fallback_search_places(query: str, limit: int = 5) -> List[Any]:
    return [{"name": "General sightseeing", "type": "fallback", "rating": 4.0}]


def fallback_get_weather(location: str) -> Dict[str, Any]:
    return {"location": location, "forecast": "Weather data unavailable",
            "recommendation": "Check local weather forecast"}
```

- [ ] **Step 4: Run tests — expect pass**

```bash
pytest tests/unit/test_fallbacks.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add src/fallbacks.py tests/unit/test_fallbacks.py
git commit -m "feat: add async retry and fallback decorators"
```

---

## Task 5: Rewrite src/tools/places.py as async (6-city fallback)

**Files:**
- Modify: `src/tools/places.py`
- Test: `tests/unit/test_tools/test_places.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/test_tools/__init__.py` (empty).

Create `tests/unit/test_tools/test_places.py`:

```python
import pytest
import respx
import httpx
from src.tools.places import search_places, get_fallback_places

@pytest.mark.asyncio
async def test_fallback_returned_for_paris():
    places = await search_places("attractions", "paris", limit=3)
    assert len(places) >= 1
    assert any("Eiffel" in p.name or "Louvre" in p.name for p in places)

@pytest.mark.asyncio
@respx.mock
async def test_nominatim_parsed_correctly():
    respx.get("https://nominatim.openstreetmap.org/search").mock(
        return_value=httpx.Response(200, json=[
            {"display_name": "Colosseum, Rome, Italy", "type": "historic",
             "lat": "41.8902", "lon": "12.4922"}
        ])
    )
    places = await search_places("attractions", "rome", limit=1)
    assert len(places) == 1
    assert places[0].lat == 41.8902

@pytest.mark.asyncio
@respx.mock
async def test_fallback_on_api_error():
    respx.get("https://nominatim.openstreetmap.org/search").mock(
        return_value=httpx.Response(500)
    )
    places = await search_places("attractions", "unknown_city_xyz", limit=3)
    assert isinstance(places, list)
```

- [ ] **Step 2: Run — expect failures**

```bash
pytest tests/unit/test_tools/test_places.py -v
```

- [ ] **Step 3: Rewrite src/tools/places.py**

```python
import asyncio
import httpx
from typing import List, Optional
from ..state import PlaceDetails

_NOM_SEM = asyncio.Semaphore(1)  # Nominatim: 1 req/sec

FALLBACK_PLACES: dict[str, list[PlaceDetails]] = {
    "paris": [
        PlaceDetails(name="Eiffel Tower", type="landmark", rating=4.7,
                     address="Champ de Mars, 75007 Paris",
                     description="Iconic wrought-iron tower with city views",
                     lat=48.8584, lng=2.2945),
        PlaceDetails(name="Louvre Museum", type="museum", rating=4.8,
                     address="Rue de Rivoli, 75001 Paris",
                     description="World's largest art museum, home of the Mona Lisa",
                     lat=48.8606, lng=2.3376),
        PlaceDetails(name="Notre-Dame Cathedral", type="cathedral", rating=4.6,
                     address="6 Parvis Notre-Dame, 75004 Paris",
                     description="Gothic cathedral masterpiece on the Île de la Cité",
                     lat=48.8530, lng=2.3499),
        PlaceDetails(name="Musée d'Orsay", type="museum", rating=4.7,
                     address="1 Rue de la Légion d'Honneur, 75007 Paris",
                     description="Impressionist masterworks in a converted railway station",
                     lat=48.8600, lng=2.3266),
        PlaceDetails(name="Arc de Triomphe", type="monument", rating=4.5,
                     address="Place Charles de Gaulle, 75008 Paris",
                     description="Historic arch atop the Champs-Élysées",
                     lat=48.8738, lng=2.2950),
        PlaceDetails(name="Sainte-Chapelle", type="chapel", rating=4.6,
                     address="10 Bd du Palais, 75001 Paris",
                     description="Gothic chapel famed for its stunning stained glass",
                     lat=48.8554, lng=2.3450),
    ],
    "london": [
        PlaceDetails(name="Buckingham Palace", type="palace", rating=4.6,
                     address="London SW1A 1AA", description="Official royal residence",
                     lat=51.5014, lng=-0.1419),
        PlaceDetails(name="British Museum", type="museum", rating=4.7,
                     address="Great Russell St, London WC1B 3DG",
                     description="World history and culture across two million years",
                     lat=51.5194, lng=-0.1270),
        PlaceDetails(name="Tower of London", type="castle", rating=4.5,
                     address="Tower Hill, London EC3N 4AB",
                     description="Historic castle and home of the Crown Jewels",
                     lat=51.5081, lng=-0.0759),
        PlaceDetails(name="Tate Modern", type="museum", rating=4.5,
                     address="Bankside, London SE1 9TG",
                     description="Contemporary art in a former power station",
                     lat=51.5076, lng=-0.0994),
    ],
    "tokyo": [
        PlaceDetails(name="Senso-ji Temple", type="temple", rating=4.6,
                     address="2-3-1 Asakusa, Taito, Tokyo",
                     description="Tokyo's oldest and most significant Buddhist temple",
                     lat=35.7148, lng=139.7967),
        PlaceDetails(name="Shibuya Crossing", type="landmark", rating=4.5,
                     address="Shibuya, Tokyo",
                     description="World's busiest pedestrian crossing",
                     lat=35.6595, lng=139.7004),
        PlaceDetails(name="Meiji Shrine", type="shrine", rating=4.6,
                     address="1-1 Yoyogikamizonocho, Shibuya, Tokyo",
                     description="Forested Shinto shrine dedicated to Emperor Meiji",
                     lat=35.6763, lng=139.6993),
        PlaceDetails(name="teamLab Planets", type="museum", rating=4.7,
                     address="6-1-16 Toyosu, Koto, Tokyo",
                     description="Immersive digital art museum",
                     lat=35.6522, lng=139.7936),
    ],
    "rome": [
        PlaceDetails(name="Colosseum", type="historic", rating=4.7,
                     address="Piazza del Colosseo, 00184 Rome",
                     description="Ancient amphitheatre and icon of Imperial Rome",
                     lat=41.8902, lng=12.4922),
        PlaceDetails(name="Vatican Museums", type="museum", rating=4.8,
                     address="Viale Vaticano, 00165 Rome",
                     description="Papal collection including the Sistine Chapel",
                     lat=41.9065, lng=12.4536),
        PlaceDetails(name="Trevi Fountain", type="fountain", rating=4.7,
                     address="Piazza di Trevi, 00187 Rome",
                     description="Baroque fountain — toss a coin to return to Rome",
                     lat=41.9009, lng=12.4833),
        PlaceDetails(name="Pantheon", type="historic", rating=4.7,
                     address="Piazza della Rotonda, 00186 Rome",
                     description="Best-preserved ancient Roman building",
                     lat=41.8986, lng=12.4769),
    ],
    "barcelona": [
        PlaceDetails(name="Sagrada Família", type="church", rating=4.8,
                     address="C/ de Mallorca, 401, Barcelona",
                     description="Gaudí's unfinished masterpiece basilica",
                     lat=41.4036, lng=2.1744),
        PlaceDetails(name="Park Güell", type="park", rating=4.5,
                     address="08024 Barcelona",
                     description="Gaudí-designed public park with city panoramas",
                     lat=41.4145, lng=2.1527),
        PlaceDetails(name="Las Ramblas", type="street", rating=4.3,
                     address="La Rambla, Barcelona",
                     description="Barcelona's famous tree-lined pedestrian boulevard",
                     lat=41.3797, lng=2.1740),
    ],
    "new york": [
        PlaceDetails(name="Central Park", type="park", rating=4.8,
                     address="Central Park, New York, NY",
                     description="843-acre urban park in the heart of Manhattan",
                     lat=40.7851, lng=-73.9683),
        PlaceDetails(name="Metropolitan Museum of Art", type="museum", rating=4.8,
                     address="1000 Fifth Ave, New York, NY 10028",
                     description="One of the world's greatest art collections",
                     lat=40.7794, lng=-73.9632),
        PlaceDetails(name="Statue of Liberty", type="monument", rating=4.7,
                     address="Liberty Island, New York, NY",
                     description="Symbol of freedom gifted by France in 1886",
                     lat=40.6892, lng=-74.0445),
    ],
}


async def search_places(query: str, location: str = None, limit: int = 10) -> List[PlaceDetails]:
    loc = (location or "").lower()
    for city in FALLBACK_PLACES:
        if city in loc or city in query.lower():
            return FALLBACK_PLACES[city][:limit]

    async with _NOM_SEM:
        await asyncio.sleep(1.05)  # enforce 1 req/sec
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://nominatim.openstreetmap.org/search",
                    params={"q": f"{query} {location or ''}", "format": "json",
                            "limit": limit, "addressdetails": 1},
                    headers={"User-Agent": "TravelConciergeApp/2.0"},
                )
                resp.raise_for_status()
                data = resp.json()
                places = []
                for item in data[:limit]:
                    places.append(PlaceDetails(
                        name=item.get("display_name", "Unknown").split(",")[0],
                        type=item.get("type", "place"),
                        rating=4.0,
                        address=item.get("display_name", ""),
                        description=f"{item.get('type', 'place').title()} in {location or ''}",
                        lat=float(item["lat"]) if "lat" in item else None,
                        lng=float(item["lon"]) if "lon" in item else None,
                    ))
                return places if places else get_fallback_places(query, limit, location)
        except Exception:
            return get_fallback_places(query, limit, location)


def get_fallback_places(query: str, limit: int = 5, location: str = None) -> List[PlaceDetails]:
    loc = (location or "").lower()
    for city, places in FALLBACK_PLACES.items():
        if city in loc or city in query.lower():
            return places[:limit]
    return [PlaceDetails(name=f"{(location or query).title()} Attraction",
                         type="attraction", rating=4.0,
                         address=f"Central {location or query}",
                         description="Popular local attraction")]
```

- [ ] **Step 4: Run tests — expect pass**

```bash
pytest tests/unit/test_tools/test_places.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add src/tools/places.py tests/unit/test_tools/
git commit -m "feat: async places tool with 6-city fallback and lat/lng"
```

---

## Task 6: Rewrite remaining tools as async (weather, country, transit, currency)

**Files:**
- Modify: `src/tools/weather.py`, `src/tools/country.py`, `src/tools/transit.py`, `src/tools/currency.py`
- Test: `tests/unit/test_tools/test_weather.py`, `tests/unit/test_tools/test_currency.py`

- [ ] **Step 1: Write weather test**

Create `tests/unit/test_tools/test_weather.py`:

```python
import pytest
import respx
import httpx
from src.tools.weather import get_weather

@pytest.mark.asyncio
@respx.mock
async def test_weather_parsed():
    respx.get("https://nominatim.openstreetmap.org/search").mock(
        return_value=httpx.Response(200, json=[{"lat": "48.8566", "lon": "2.3522"}])
    )
    respx.get("https://api.open-meteo.com/v1/forecast").mock(
        return_value=httpx.Response(200, json={
            "daily": {
                "temperature_2m_max": [22.5],
                "temperature_2m_min": [14.0],
                "weathercode": [3]
            }
        })
    )
    result = await get_weather("Paris")
    assert result["temp_high"] == 22.5
    assert "recommendation" in result

@pytest.mark.asyncio
@respx.mock
async def test_weather_fallback_on_error():
    respx.get("https://nominatim.openstreetmap.org/search").mock(
        return_value=httpx.Response(500)
    )
    result = await get_weather("SomeCity")
    assert "forecast" in result
```

- [ ] **Step 2: Rewrite src/tools/weather.py**

```python
import httpx
from typing import Dict, Any

_WEATHER_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Foggy", 51: "Light drizzle", 61: "Light rain", 71: "Light snow",
    80: "Rain showers", 95: "Thunderstorm",
}


async def get_weather(location: str) -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            geo = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": location, "format": "json", "limit": 1},
                headers={"User-Agent": "TravelConciergeApp/2.0"},
            )
            geo.raise_for_status()
            geo_data = geo.json()
            if not geo_data:
                return _weather_fallback(location)
            lat, lon = geo_data[0]["lat"], geo_data[0]["lon"]

            wx = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={"latitude": lat, "longitude": lon,
                        "daily": "temperature_2m_max,temperature_2m_min,weathercode",
                        "forecast_days": 7, "timezone": "auto"},
            )
            wx.raise_for_status()
            data = wx.json()["daily"]
            code = data["weathercode"][0]
            high = data["temperature_2m_max"][0]
            low = data["temperature_2m_min"][0]
            desc = _WEATHER_CODES.get(code, "Variable conditions")
            rec = "Light layers recommended" if low < 15 else "Comfortable weather expected"
            return {"location": location, "forecast": desc,
                    "temp_high": high, "temp_low": low, "recommendation": rec}
    except Exception:
        return _weather_fallback(location)


def _weather_fallback(location: str) -> Dict[str, Any]:
    return {"location": location, "forecast": "Weather data unavailable",
            "temp_high": None, "temp_low": None,
            "recommendation": "Check local weather forecast before travelling"}
```

- [ ] **Step 3: Rewrite src/tools/country.py**

```python
import httpx
from typing import Dict, Any

_FALLBACK = {
    "france": {"capital": "Paris", "currency": "EUR", "language": "French",
               "timezone": "Europe/Paris", "travel_tip": "Greet with 'Bonjour'"},
    "japan": {"capital": "Tokyo", "currency": "JPY", "language": "Japanese",
              "timezone": "Asia/Tokyo", "travel_tip": "Cash is widely preferred"},
    "italy": {"capital": "Rome", "currency": "EUR", "language": "Italian",
              "timezone": "Europe/Rome", "travel_tip": "Validate train tickets before boarding"},
    "spain": {"capital": "Madrid", "currency": "EUR", "language": "Spanish",
              "timezone": "Europe/Madrid", "travel_tip": "Lunch is the main meal, often after 2pm"},
    "united kingdom": {"capital": "London", "currency": "GBP", "language": "English",
                       "timezone": "Europe/London", "travel_tip": "Oyster card for London transport"},
    "united states": {"capital": "Washington D.C.", "currency": "USD", "language": "English",
                      "timezone": "America/New_York", "travel_tip": "Tip 15-20% at restaurants"},
}


async def get_country_info(country: str) -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"https://restcountries.com/v3.1/name/{country}",
                params={"fields": "name,capital,currencies,languages,timezones,population"},
            )
            resp.raise_for_status()
            data = resp.json()[0]
            currencies = list(data.get("currencies", {}).keys())
            languages = list(data.get("languages", {}).values())
            return {
                "country": data["name"]["common"],
                "capital": data.get("capital", ["Unknown"])[0],
                "currency": currencies[0] if currencies else "Unknown",
                "language": languages[0] if languages else "Unknown",
                "timezone": data.get("timezones", ["Unknown"])[0],
                "travel_tip": "Respect local customs and carry local currency",
            }
    except Exception:
        key = country.lower()
        return _FALLBACK.get(key, {
            "country": country, "capital": "Unknown", "currency": "USD",
            "language": "Local", "timezone": "UTC", "travel_tip": "Check travel advisories"
        })
```

- [ ] **Step 4: Rewrite src/tools/transit.py**

```python
import httpx
from typing import Dict, Any

_FALLBACK = {
    "paris": {"systems": ["Métro", "RER", "Bus", "Vélib' bikes"],
              "recommendation": "Use Navigo pass for unlimited travel. Metro runs 5:30am-1:15am."},
    "london": {"systems": ["Underground (Tube)", "Bus", "DLR", "Elizabeth line"],
               "recommendation": "Oyster card or contactless payment. 24-hour service on weekends."},
    "tokyo": {"systems": ["JR lines", "Tokyo Metro", "Toei Subway", "Bus"],
              "recommendation": "IC Card (Suica/Pasmo) accepted everywhere. Trains run on the minute."},
    "rome": {"systems": ["Metro (2 lines)", "Bus", "Tram"],
             "recommendation": "Buy tickets before boarding; validate every journey."},
    "barcelona": {"systems": ["Metro", "FGC", "Bus", "Bicing bikes"],
                  "recommendation": "T-Casual 10-trip card is best value for tourists."},
    "new york": {"systems": ["Subway", "Bus", "PATH train"],
                 "recommendation": "OMNY contactless or MetroCard. Subway runs 24/7."},
}


async def get_public_transit(city: str) -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://transit.land/api/v2/rest/agencies",
                params={"city_name": city, "per_page": 5},
                headers={"apikey": ""},  # TransitLand allows unauthenticated for basic queries
            )
            if resp.status_code == 200:
                agencies = resp.json().get("agencies", [])
                if agencies:
                    systems = [a.get("name", "Local Transit") for a in agencies[:5]]
                    return {"systems": systems,
                            "recommendation": "Use local transit apps for real-time schedules"}
    except Exception:
        pass
    key = city.lower()
    return _FALLBACK.get(key, {
        "systems": ["Local Bus", "Taxi"],
        "recommendation": "Ask your hotel for local transport advice"
    })
```

- [ ] **Step 5: Rewrite src/tools/currency.py**

Create `tests/unit/test_tools/test_currency.py`:

```python
import pytest
import respx
import httpx
from src.tools.currency import convert_currency

@pytest.mark.asyncio
@respx.mock
async def test_convert_uses_api():
    respx.get("https://api.exchangerate.host/convert").mock(
        return_value=httpx.Response(200, json={"result": 920.5, "success": True})
    )
    result = await convert_currency(1000.0, "USD", "EUR")
    assert result["converted"] == 920.5

@pytest.mark.asyncio
@respx.mock
async def test_convert_fallback_on_error():
    respx.get("https://api.exchangerate.host/convert").mock(
        return_value=httpx.Response(500)
    )
    result = await convert_currency(100.0, "USD", "EUR")
    assert "converted" in result
    assert result["converted"] > 0
```

```python
# src/tools/currency.py
import httpx
from typing import Dict, Any

_FALLBACK_RATES: dict[str, dict[str, float]] = {
    "USD": {"EUR": 0.92, "GBP": 0.79, "JPY": 149.5, "USD": 1.0},
    "EUR": {"USD": 1.09, "GBP": 0.86, "JPY": 163.0, "EUR": 1.0},
    "GBP": {"USD": 1.27, "EUR": 1.16, "JPY": 189.0, "GBP": 1.0},
}


async def convert_currency(amount: float, from_currency: str, to_currency: str) -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://api.exchangerate.host/convert",
                params={"from": from_currency, "to": to_currency, "amount": amount},
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("success"):
                return {"from": from_currency, "to": to_currency,
                        "original": amount, "converted": data["result"]}
    except Exception:
        pass
    rate = _FALLBACK_RATES.get(from_currency, {}).get(to_currency, 1.0)
    return {"from": from_currency, "to": to_currency,
            "original": amount, "converted": round(amount * rate, 2),
            "note": "estimated rate"}
```

- [ ] **Step 6: Run all tool tests**

```bash
pytest tests/unit/test_tools/ -v
```

Expected: all pass (weather + currency + distance + places).

- [ ] **Step 7: Commit**

```bash
git add src/tools/weather.py src/tools/country.py src/tools/transit.py src/tools/currency.py tests/unit/test_tools/
git commit -m "feat: rewrite weather/country/transit/currency tools as async"
```

---

## Task 7: Create src/tools/hotels.py

**Files:**
- Create: `src/tools/hotels.py`
- Test: `tests/unit/test_tools/test_hotels.py`

- [ ] **Step 1: Write failing test**

Create `tests/unit/test_tools/test_hotels.py`:

```python
import pytest
import respx
import httpx
from src.tools.hotels import search_hotels

@pytest.mark.asyncio
@respx.mock
async def test_hotels_parsed_from_nominatim():
    respx.get("https://nominatim.openstreetmap.org/search").mock(
        return_value=httpx.Response(200, json=[
            {"display_name": "Hotel Ritz, Paris, France", "type": "hotel",
             "lat": "48.8687", "lon": "2.3312"}
        ])
    )
    hotels = await search_hotels("paris", num_days=3)
    assert len(hotels) >= 1
    assert hotels[0].estimated_price_per_night > 0
    assert hotels[0].lat == 48.8687

@pytest.mark.asyncio
async def test_hotels_fallback_for_known_city():
    hotels = await search_hotels("paris", num_days=2)
    assert len(hotels) >= 1

@pytest.mark.asyncio
@respx.mock
async def test_hotels_price_tier_applied():
    respx.get("https://nominatim.openstreetmap.org/search").mock(
        return_value=httpx.Response(500)
    )
    hotels = await search_hotels("tokyo", num_days=3)
    assert all(h.estimated_price_per_night > 0 for h in hotels)
```

- [ ] **Step 2: Run — expect failures**

```bash
pytest tests/unit/test_tools/test_hotels.py -v
```

- [ ] **Step 3: Create src/tools/hotels.py**

```python
import asyncio
import httpx
from typing import List
from ..state import HotelOption

_NOM_SEM = asyncio.Semaphore(1)

# Estimated nightly rates (mid-tier) in USD by city
_PRICE_TIERS: dict[str, float] = {
    "paris": 180.0, "london": 200.0, "tokyo": 150.0,
    "rome": 140.0, "barcelona": 130.0, "new york": 250.0,
    "dubai": 170.0, "amsterdam": 160.0, "berlin": 120.0,
    "lisbon": 110.0, "prague": 90.0, "vienna": 130.0,
}

_FALLBACK_HOTELS: dict[str, list[HotelOption]] = {
    "paris": [
        HotelOption(name="Hôtel du Louvre", estimated_price_per_night=195.0,
                    address="Place André Malraux, 75001 Paris", lat=48.8637, lng=2.3362),
        HotelOption(name="Hôtel de Crillon", estimated_price_per_night=950.0,
                    address="10 Pl. de la Concorde, 75008 Paris", lat=48.8659, lng=2.3214),
        HotelOption(name="Hôtel Bastille Spéria", estimated_price_per_night=140.0,
                    address="1 Rue de la Bastille, 75004 Paris", lat=48.8533, lng=2.3691),
    ],
    "london": [
        HotelOption(name="The Savoy", estimated_price_per_night=450.0,
                    address="Strand, London WC2R 0EU", lat=51.5100, lng=-0.1207),
        HotelOption(name="Hub by Premier Inn", estimated_price_per_night=120.0,
                    address="Covent Garden, London", lat=51.5134, lng=-0.1225),
    ],
}


async def search_hotels(city: str, num_days: int = 1) -> List[HotelOption]:
    city_key = city.lower()
    if city_key in _FALLBACK_HOTELS:
        return _FALLBACK_HOTELS[city_key]

    async with _NOM_SEM:
        await asyncio.sleep(1.05)
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://nominatim.openstreetmap.org/search",
                    params={"q": f"hotel {city}", "format": "json",
                            "limit": 5, "addressdetails": 1},
                    headers={"User-Agent": "TravelConciergeApp/2.0"},
                )
                resp.raise_for_status()
                items = resp.json()
                base_price = _PRICE_TIERS.get(city_key, 130.0)
                hotels = []
                for item in items[:5]:
                    hotels.append(HotelOption(
                        name=item.get("display_name", "Local Hotel").split(",")[0],
                        estimated_price_per_night=base_price,
                        address=item.get("display_name", city),
                        lat=float(item["lat"]) if "lat" in item else None,
                        lng=float(item["lon"]) if "lon" in item else None,
                    ))
                return hotels if hotels else _generic_fallback(city_key)
        except Exception:
            return _generic_fallback(city_key)


def _generic_fallback(city: str) -> List[HotelOption]:
    price = _PRICE_TIERS.get(city, 130.0)
    return [HotelOption(name=f"Central Hotel {city.title()}",
                        estimated_price_per_night=price,
                        address=f"City Centre, {city.title()}")]
```

- [ ] **Step 4: Run tests — expect pass**

```bash
pytest tests/unit/test_tools/test_hotels.py -v
```

- [ ] **Step 5: Commit**

```bash
git add src/tools/hotels.py tests/unit/test_tools/test_hotels.py
git commit -m "feat: hotel search tool via Nominatim with price tiers"
```

---

## Task 8: Create src/tools/flights.py (Amadeus free tier)

**Files:**
- Create: `src/tools/flights.py`
- Test: `tests/unit/test_tools/test_flights.py`

- [ ] **Step 1: Write failing test**

Create `tests/unit/test_tools/test_flights.py`:

```python
import pytest
import respx
import httpx
from unittest.mock import patch
from src.tools.flights import search_flights

@pytest.mark.asyncio
async def test_fallback_when_no_credentials():
    with patch.dict("os.environ", {}, clear=True):
        flights = await search_flights("JFK", "CDG", "2026-06-01", adults=2)
    assert len(flights) == 3
    assert all(f.is_estimated for f in flights)

@pytest.mark.asyncio
@respx.mock
async def test_amadeus_token_and_search():
    respx.post("https://test.api.amadeus.com/v1/security/oauth2/token").mock(
        return_value=httpx.Response(200, json={"access_token": "tok123", "expires_in": 1799})
    )
    respx.get("https://test.api.amadeus.com/v2/shopping/flight-offers").mock(
        return_value=httpx.Response(200, json={
            "data": [{
                "itineraries": [{
                    "segments": [{
                        "departure": {"iataCode": "JFK", "at": "2026-06-01T08:00:00"},
                        "arrival": {"iataCode": "CDG", "at": "2026-06-01T20:00:00"},
                        "carrierCode": "AF",
                        "duration": "PT7H"
                    }]
                }],
                "price": {"grandTotal": "650.00", "currency": "USD"},
                "validatingAirlineCodes": ["AF"]
            }]
        })
    )
    with patch.dict("os.environ", {
        "AMADEUS_CLIENT_ID": "id123", "AMADEUS_CLIENT_SECRET": "sec456"
    }):
        flights = await search_flights("JFK", "CDG", "2026-06-01", adults=1)
    assert len(flights) == 1
    assert flights[0].airline == "AF"
    assert not flights[0].is_estimated
```

- [ ] **Step 2: Run — expect failures**

```bash
pytest tests/unit/test_tools/test_flights.py -v
```

- [ ] **Step 3: Create src/tools/flights.py**

```python
import os
import httpx
from typing import List, Optional
from ..state import FlightOption

_AMADEUS_BASE = "https://test.api.amadeus.com"
_token_cache: dict = {}  # {"token": str, "expires_at": float}


async def _get_token(client: httpx.AsyncClient) -> Optional[str]:
    import time
    client_id = os.getenv("AMADEUS_CLIENT_ID")
    client_secret = os.getenv("AMADEUS_CLIENT_SECRET")
    if not client_id or not client_secret:
        return None
    if _token_cache.get("token") and time.time() < _token_cache.get("expires_at", 0):
        return _token_cache["token"]
    resp = await client.post(
        f"{_AMADEUS_BASE}/v1/security/oauth2/token",
        data={"grant_type": "client_credentials",
              "client_id": client_id, "client_secret": client_secret},
    )
    resp.raise_for_status()
    data = resp.json()
    _token_cache["token"] = data["access_token"]
    _token_cache["expires_at"] = time.time() + data["expires_in"] - 60
    return _token_cache["token"]


async def search_flights(
    origin: str, destination: str, date: str, adults: int = 1
) -> List[FlightOption]:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            token = await _get_token(client)
            if not token:
                return _dummy_flights(origin, destination)
            resp = await client.get(
                f"{_AMADEUS_BASE}/v2/shopping/flight-offers",
                params={"originLocationCode": origin, "destinationLocationCode": destination,
                        "departureDate": date, "adults": adults, "max": 3},
                headers={"Authorization": f"Bearer {token}"},
            )
            resp.raise_for_status()
            offers = resp.json().get("data", [])
            flights = []
            for offer in offers:
                itin = offer["itineraries"][0]
                seg = itin["segments"][0]
                price = offer["price"]["grandTotal"]
                airline = offer.get("validatingAirlineCodes", ["??"])[0]
                flights.append(FlightOption(
                    origin_airport=seg["departure"]["iataCode"],
                    destination_airport=seg["arrival"]["iataCode"],
                    departure=seg["departure"]["at"],
                    arrival=seg["arrival"]["at"],
                    price=f"${price} {offer['price']['currency']}",
                    airline=airline,
                    is_estimated=False,
                ))
            return flights if flights else _dummy_flights(origin, destination)
    except Exception:
        return _dummy_flights(origin, destination)


def _dummy_flights(origin: str, destination: str) -> List[FlightOption]:
    return [
        FlightOption(origin_airport=origin, destination_airport=destination,
                     departure="08:00", arrival="16:00",
                     price="~$650 USD", airline="Major Airline", is_estimated=True),
        FlightOption(origin_airport=origin, destination_airport=destination,
                     departure="13:00", arrival="21:00",
                     price="~$580 USD", airline="Budget Carrier", is_estimated=True),
        FlightOption(origin_airport=origin, destination_airport=destination,
                     departure="20:00", arrival="06:00+1",
                     price="~$720 USD", airline="Premium Airline", is_estimated=True),
    ]
```

- [ ] **Step 4: Run tests — expect pass**

```bash
pytest tests/unit/test_tools/test_flights.py -v
```

- [ ] **Step 5: Update src/tools/__init__.py**

```python
from .places import search_places
from .weather import get_weather
from .country import get_country_info
from .transit import get_public_transit
from .currency import convert_currency
from .hotels import search_hotels
from .flights import search_flights
from .distance_calc import haversine

__all__ = [
    "search_places", "get_weather", "get_country_info",
    "get_public_transit", "convert_currency",
    "search_hotels", "search_flights", "haversine",
]
```

- [ ] **Step 6: Commit**

```bash
git add src/tools/flights.py src/tools/__init__.py tests/unit/test_tools/test_flights.py
git commit -m "feat: Amadeus free-tier flight search with dummy fallback"
```

---

## Task 9: Rewrite src/agents.py (all 6 agents async)

**Files:**
- Modify: `src/agents.py`
- Test: `tests/unit/test_agents.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/test_agents.py`:

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.state import TravelState, PlaceDetails, ItineraryItem
from src.agents import (
    UserInputAgent, ResearchAgent, PlannerAgent,
    ReviewerAgent, WriterAgent, CostEstimatorAgent
)

@pytest.fixture
def base_state():
    return TravelState(
        user_input="3 days in Paris from New York",
        origin="New York", destination="Paris",
        num_days=3, budget=2000.0, num_passengers=2
    )

@pytest.fixture
def state_with_places(base_state):
    base_state.retrieved_places = [
        PlaceDetails(name="Eiffel Tower", type="landmark", rating=4.7,
                     address="Paris", description="Tower", lat=48.8584, lng=2.2945),
        PlaceDetails(name="Louvre", type="museum", rating=4.8,
                     address="Paris", description="Museum", lat=48.8606, lng=2.3376),
        PlaceDetails(name="Notre-Dame", type="cathedral", rating=4.6,
                     address="Paris", description="Church", lat=48.8530, lng=2.3499),
    ]
    return base_state

@pytest.mark.asyncio
async def test_user_input_agent_extracts_fields():
    agent = UserInputAgent(api_key="fake")
    mock_llm = AsyncMock()
    mock_llm.ainvoke = AsyncMock(return_value=MagicMock(
        content='{"origin":"New York","destination":"Paris","num_days":3,"budget":2000,"trip_type":"solo","num_passengers":1,"date_of_travel":null}'
    ))
    agent.llm = mock_llm
    state = TravelState(user_input="3 days in Paris from New York solo $2000")
    result = await agent.process(state)
    assert result.destination == "Paris"
    assert result.num_days == 3

@pytest.mark.asyncio
async def test_planner_creates_3_slots_per_day(state_with_places):
    agent = PlannerAgent(api_key="fake")
    result = await agent.process(state_with_places)
    assert "day_1" in result.day_plan
    day1 = result.day_plan["day_1"]
    assert len(day1) >= 1

@pytest.mark.asyncio
async def test_reviewer_flags_empty_day():
    agent = ReviewerAgent(api_key="fake")
    state = TravelState(destination="Paris", num_days=2, budget=1000.0)
    state.day_plan = {"day_1": [], "day_2": []}
    result = await agent.process(state)
    assert result.violations

@pytest.mark.asyncio
async def test_cost_estimator_calculates_total():
    from src.state import FlightOption, HotelOption
    agent = CostEstimatorAgent(api_key="fake")
    state = TravelState(num_days=3, budget=2000.0, num_passengers=1)
    state.flights = [FlightOption(origin_airport="JFK", destination_airport="CDG",
                                   departure="08:00", arrival="16:00",
                                   price="$650 USD", airline="AF")]
    state.hotels = [HotelOption(name="Hotel Paris", estimated_price_per_night=180.0,
                                 address="Paris")]
    result = await agent.process(state)
    assert result.cost_estimate is not None
    assert result.cost_estimate.hotels_total == 540.0  # 180 * 3
```

- [ ] **Step 2: Run — expect failures**

```bash
pytest tests/unit/test_agents.py -v
```

- [ ] **Step 3: Rewrite src/agents.py**

```python
import json
import re
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from dateutil.parser import parse
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from .state import (
    TravelState, PlaceDetails, ItineraryItem, FlightOption,
    HotelOption, CostEstimate, MapPoint, StateStatus
)
from .tools import (
    search_places, get_weather, get_country_info,
    get_public_transit, search_hotels, search_flights, haversine
)
from .guardrails import validate_schema, moderate_content, FinalOutputSchema
from .fallbacks import async_retry


class BaseAgent:
    def __init__(self, model_name: str = "llama-3.3-70b-versatile", api_key: str = None):
        self.llm = ChatGroq(model=model_name, temperature=0.1, api_key=api_key)

    def validate_output(self, output: Any, schema: Any) -> bool:
        return validate_schema(output, schema)


class UserInputAgent(BaseAgent):
    @async_retry(max_retries=3, delay=2.0)
    async def _extract(self, user_input: str) -> Dict[str, Any]:
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Extract travel info from user input. Return valid JSON only:
{
  "origin": string or null,
  "destination": string or null,
  "date_of_travel": "YYYY-MM-DD" or null,
  "num_days": integer or null,
  "trip_type": "honeymoon"|"family"|"solo"|"business" or null,
  "num_passengers": integer or null,
  "budget": float or null
}"""),
            ("human", "{input}"),
        ])
        chain = prompt | self.llm
        resp = await chain.ainvoke({"input": user_input})
        match = re.search(r"\{.*\}", resp.content, re.DOTALL)
        if not match:
            return {}
        return json.loads(match.group())

    async def process(self, state: TravelState) -> TravelState:
        if not state.user_input:
            state.error = "No user input provided"
            return state
        try:
            extracted = await self._extract(state.user_input)
            if extracted:
                state.origin = extracted.get("origin") or state.origin
                state.destination = extracted.get("destination") or state.destination
                state.num_days = extracted.get("num_days") or state.num_days
                state.trip_type = extracted.get("trip_type") or state.trip_type
                state.num_passengers = extracted.get("num_passengers") or state.num_passengers
                state.budget = extracted.get("budget") or state.budget
                date_str = extracted.get("date_of_travel")
                if date_str:
                    try:
                        state.date_of_travel = parse(date_str).date()
                    except Exception:
                        pass
        except Exception as e:
            state.error = f"Input extraction failed: {e}"
        return state


class ResearchAgent(BaseAgent):
    async def process(self, state: TravelState) -> TravelState:
        if not state.destination:
            state.error = "Missing destination"
            return state
        num_days = state.num_days or 3
        city = state.destination.split(",")[0].strip()
        country = state.destination.split(",")[-1].strip() if "," in state.destination else city

        try:
            (places, hotels, weather, country_info, transit, flights) = await asyncio.gather(
                search_places("tourist attractions", city, num_days * 3),
                search_hotels(city, num_days),
                get_weather(state.destination),
                get_country_info(country),
                get_public_transit(city),
                search_flights(
                    _city_to_iata(state.origin or ""),
                    _city_to_iata(city),
                    str(state.date_of_travel or datetime.now().date()),
                    state.num_passengers or 1,
                ),
                return_exceptions=True,
            )
            if not isinstance(places, Exception):
                state.retrieved_places = places
            if not isinstance(hotels, Exception):
                state.hotels = hotels
            if not isinstance(weather, Exception):
                state.weather_info = weather
            if not isinstance(country_info, Exception):
                state.country_info = country_info
            if not isinstance(transit, Exception):
                state.transit_info = transit
            if not isinstance(flights, Exception):
                state.flights = flights
            state.tools_used.extend([
                "search_places", "search_hotels", "get_weather",
                "get_country_info", "get_public_transit", "search_flights"
            ])
            # Build map points from places and hotels
            for p in state.retrieved_places:
                if p.lat and p.lng:
                    state.map_points.append(MapPoint(lat=p.lat, lng=p.lng,
                                                     label=p.name, type="place"))
            for h in state.hotels:
                if h.lat and h.lng:
                    state.map_points.append(MapPoint(lat=h.lat, lng=h.lng,
                                                     label=h.name, type="hotel"))
        except Exception as e:
            state.error = f"Research failed: {e}"
            state.needs_fallback = True
        return state


def _city_to_iata(city: str) -> str:
    _MAP = {
        "new york": "JFK", "london": "LHR", "paris": "CDG", "tokyo": "NRT",
        "rome": "FCO", "barcelona": "BCN", "dubai": "DXB", "amsterdam": "AMS",
        "berlin": "BER", "lisbon": "LIS", "sydney": "SYD", "singapore": "SIN",
    }
    return _MAP.get(city.lower(), city.upper()[:3])


class PlannerAgent(BaseAgent):
    async def process(self, state: TravelState) -> TravelState:
        if not state.num_days:
            state.error = "Missing number of days"
            return state
        try:
            state.day_plan = self._build_itinerary(
                state.retrieved_places, state.num_days,
                state.trip_type or "solo", state.destination or ""
            )
        except Exception as e:
            state.error = f"Planning failed: {e}"
            state.needs_fallback = True
        return state

    def _build_itinerary(
        self, places: List[PlaceDetails], num_days: int, trip_type: str, destination: str
    ) -> Dict[str, List[ItineraryItem]]:
        itinerary: Dict[str, List[ItineraryItem]] = {}
        # Sort places by proximity using haversine (group nearby places on same day)
        sorted_places = _geo_sort(places)

        slots = [("09:00", "Morning"), ("13:00", "Afternoon"), ("18:00", "Evening")]
        slot_idx = 0

        for day in range(1, num_days + 1):
            day_key = f"day_{day}"
            items: List[ItineraryItem] = []

            if day == 1:
                items.append(ItineraryItem(
                    time="14:00",
                    activity="Hotel check-in and neighbourhood orientation",
                    notes="Drop luggage, pick up local transport card"
                ))

            for time, period in slots:
                if not sorted_places:
                    items.append(_generic_activity(time, period, trip_type, destination))
                else:
                    place = sorted_places.pop(0)
                    note = _trip_type_note(place, trip_type)
                    items.append(ItineraryItem(
                        time=time,
                        activity=f"Visit {place.name}",
                        notes=f"{place.description}. {note}",
                    ))
                slot_idx += 1

            if day == num_days:
                items.append(ItineraryItem(
                    time="11:00",
                    activity="Hotel check-out",
                    notes="Store luggage at hotel if flight is later"
                ))

            itinerary[day_key] = items
        return itinerary


def _geo_sort(places: List[PlaceDetails]) -> List[PlaceDetails]:
    with_coords = [p for p in places if p.lat and p.lng]
    without = [p for p in places if not p.lat or not p.lng]
    if len(with_coords) < 2:
        return with_coords + without
    # Greedy nearest-neighbour from first place
    result = [with_coords.pop(0)]
    while with_coords:
        last = result[-1]
        nearest = min(with_coords, key=lambda p: haversine(last.lat, last.lng, p.lat, p.lng))
        with_coords.remove(nearest)
        result.append(nearest)
    return result + without


def _trip_type_note(place: PlaceDetails, trip_type: str) -> str:
    if trip_type == "honeymoon":
        return "Perfect for a romantic afternoon"
    if trip_type == "family":
        return "Kid-friendly — great for all ages"
    if trip_type == "business":
        return "Quick visit recommended"
    return "Allow 1-2 hours"


def _generic_activity(time: str, period: str, trip_type: str, destination: str) -> ItineraryItem:
    activities = {
        "Morning": f"Morning walk through {destination} city centre",
        "Afternoon": f"Local market visit and lunch in {destination}",
        "Evening": f"Dinner at a recommended {destination} restaurant",
    }
    return ItineraryItem(time=time, activity=activities.get(period, "Free time"),
                         notes="Ask hotel concierge for personalised recommendations")


class ReviewerAgent(BaseAgent):
    async def process(self, state: TravelState) -> TravelState:
        if not state.day_plan:
            state.error = "No itinerary to review"
            return state

        issues: List[str] = []

        for day, activities in state.day_plan.items():
            if not activities:
                issues.append(f"{day} has no activities")
                continue
            types = {a.activity.lower() for a in activities}
            if len(types) < 2:
                issues.append(f"{day} lacks activity variety")
            # Geo clustering check
            if state.retrieved_places:
                coords = [(p.lat, p.lng) for p in state.retrieved_places if p.lat and p.lng]
                if len(coords) >= 2:
                    max_dist = max(
                        haversine(coords[i][0], coords[i][1], coords[j][0], coords[j][1])
                        for i in range(len(coords)) for j in range(i + 1, len(coords))
                    )
                    if max_dist > 50:
                        issues.append(f"{day} has places more than 50km apart")

        if state.cost_estimate and state.budget and state.cost_estimate.grand_total > state.budget:
            issues.append("Estimated cost exceeds budget")

        if issues:
            state.violations.extend(issues)
            if state.replan_count < 2:
                state.replan_instructions = "; ".join(issues)
                state.replan_count += 1
                state.needs_fallback = True
        return state


class WriterAgent(BaseAgent):
    async def process(self, state: TravelState) -> TravelState:
        try:
            moderation = moderate_content(str(state.day_plan))
            if not moderation["is_safe"]:
                state.violations.append(f"Moderation: {moderation['issues']}")

            itinerary_dict = {
                day: [item.model_dump() for item in items]
                for day, items in state.day_plan.items()
            }
            output = {
                "origin": state.origin,
                "destination": state.destination,
                "travel_date": str(state.date_of_travel) if state.date_of_travel else None,
                "duration_days": state.num_days,
                "passengers": state.num_passengers,
                "budget": state.budget,
                "trip_type": state.trip_type,
                "itinerary": itinerary_dict,
                "flights": [f.model_dump() for f in state.flights],
                "hotels": [h.model_dump() for h in state.hotels],
                "recommended_places": [p.model_dump() for p in state.retrieved_places],
                "weather": state.weather_info,
                "country": state.country_info,
                "transit": state.transit_info,
                "map_points": [m.model_dump() for m in state.map_points],
                "cost_estimate": state.cost_estimate.model_dump() if state.cost_estimate else None,
                "tools_used": state.tools_used,
                "generated_at": datetime.now().isoformat(),
            }
            if not self.validate_output(output, FinalOutputSchema):
                state.violations.append("Schema validation failed")
            state.final_output = output
            state.status = StateStatus.COMPLETED
        except Exception as e:
            state.error = f"Writing failed: {e}"
            state.needs_fallback = True
        return state


class CostEstimatorAgent(BaseAgent):
    async def process(self, state: TravelState) -> TravelState:
        if not state.num_days or not state.budget:
            return state
        try:
            num_days = state.num_days
            budget = state.budget

            flights_total = 0.0
            for f in state.flights:
                if not f.is_estimated:
                    try:
                        flights_total += float(f.price.replace("$", "").split()[0])
                    except Exception:
                        flights_total += 650.0
                else:
                    flights_total += 650.0

            hotels_total = 0.0
            if state.hotels:
                nightly = state.hotels[0].estimated_price_per_night
                hotels_total = nightly * num_days

            daily_spend = budget / num_days
            grand_total = flights_total + hotels_total + (daily_spend * num_days * 0.5)
            over = grand_total > budget
            suggestion = None
            if over and state.hotels:
                cheaper = state.hotels[0].estimated_price_per_night * 0.7
                savings = (state.hotels[0].estimated_price_per_night - cheaper) * num_days
                suggestion = f"A budget hotel could save ${savings:.0f} over {num_days} days"

            state.cost_estimate = CostEstimate(
                flights_total=round(flights_total, 2),
                hotels_total=round(hotels_total, 2),
                daily_spend_budget=round(daily_spend, 2),
                grand_total=round(grand_total, 2),
                over_budget=over,
                savings_suggestion=suggestion,
            )
        except Exception as e:
            state.error = f"Cost estimation failed: {e}"
        return state
```

- [ ] **Step 4: Run tests — expect pass**

```bash
pytest tests/unit/test_agents.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add src/agents.py tests/unit/test_agents.py
git commit -m "feat: rewrite all 6 agents as async with trip-type awareness and cost estimator"
```

---

## Task 10: Rewrite src/graph.py (async + SSE events)

**Files:**
- Modify: `src/graph.py`

- [ ] **Step 1: Rewrite src/graph.py**

```python
import os
import asyncio
from typing import AsyncGenerator, Optional
from langgraph.graph import StateGraph, END
from .state import TravelState, StateStatus
from .agents import (
    UserInputAgent, ResearchAgent, PlannerAgent,
    ReviewerAgent, WriterAgent, CostEstimatorAgent
)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

_AGENT_LABELS = {
    "get_user_input": "Extracting trip details",
    "research_destination": "Researching destination, weather, flights & hotels",
    "plan_itinerary": "Building your day-by-day itinerary",
    "review_itinerary": "Reviewing itinerary quality",
    "estimate_cost": "Calculating cost estimate",
    "generate_output": "Finalising your travel plan",
}


class TravelGraph:
    def __init__(self):
        self._user_input_agent = UserInputAgent(api_key=GROQ_API_KEY)
        self._research_agent = ResearchAgent(api_key=GROQ_API_KEY)
        self._planner_agent = PlannerAgent(api_key=GROQ_API_KEY)
        self._reviewer_agent = ReviewerAgent(api_key=GROQ_API_KEY)
        self._writer_agent = WriterAgent(api_key=GROQ_API_KEY)
        self._cost_agent = CostEstimatorAgent(api_key=GROQ_API_KEY)
        self._compiled = self._build()

    def _build(self):
        g = StateGraph(TravelState)
        g.add_node("get_user_input", self._user_input_agent.process)
        g.add_node("research_destination", self._research_agent.process)
        g.add_node("plan_itinerary", self._planner_agent.process)
        g.add_node("review_itinerary", self._reviewer_agent.process)
        g.add_node("estimate_cost", self._cost_agent.process)
        g.add_node("generate_output", self._writer_agent.process)

        g.set_entry_point("get_user_input")
        g.add_edge("get_user_input", "research_destination")
        g.add_edge("research_destination", "plan_itinerary")
        g.add_conditional_edges(
            "plan_itinerary",
            self._should_review,
            {"review": "review_itinerary", "cost": "estimate_cost"},
        )
        g.add_edge("review_itinerary", "plan_itinerary")  # re-plan loop
        g.add_edge("estimate_cost", "generate_output")
        g.add_edge("generate_output", END)
        return g.compile()

    def _should_review(self, state: TravelState) -> str:
        if state.violations or state.needs_fallback:
            if state.replan_count < 2:
                return "review"
        return "cost"

    async def invoke_streaming(
        self, user_input: str, queue: asyncio.Queue
    ) -> None:
        """Run the graph and push SSE-ready dicts into queue."""
        initial_state = TravelState(user_input=user_input)
        try:
            async for chunk in self._compiled.astream(initial_state):
                node_name = next(iter(chunk))
                label = _AGENT_LABELS.get(node_name, node_name)
                node_state: TravelState = chunk[node_name]
                await queue.put({
                    "event": "agent_done",
                    "data": {"agent": node_name, "message": label,
                             "error": node_state.error},
                })
            # Final state is the last chunk's value
            final_state: TravelState = node_state  # noqa: F821
            if final_state.status == StateStatus.COMPLETED and final_state.final_output:
                await queue.put({"event": "complete", "data": final_state.final_output})
            else:
                await queue.put({"event": "error",
                                 "data": {"message": final_state.error or "Pipeline failed"}})
        except Exception as e:
            await queue.put({"event": "error", "data": {"message": str(e)}})
        finally:
            await queue.put(None)  # sentinel — stream is done

    def invoke(self, user_input: str) -> TravelState:
        """Synchronous invocation (kept for notebook compatibility)."""
        import asyncio as _a
        return _a.run(self._run_sync(user_input))

    async def _run_sync(self, user_input: str) -> TravelState:
        initial = TravelState(user_input=user_input)
        result = await self._compiled.ainvoke(initial)
        return result
```

- [ ] **Step 2: Smoke-test the graph runs without crashing**

```bash
python -c "
import asyncio, os
os.environ.setdefault('GROQ_API_KEY', 'fake')
from src.graph import TravelGraph
g = TravelGraph()
print('Graph compiled OK')
"
```

Expected: `Graph compiled OK`

- [ ] **Step 3: Commit**

```bash
git add src/graph.py
git commit -m "feat: async LangGraph pipeline with SSE event queue and re-plan loop"
```

---

## Task 11: Create backend package (schemas, session, stream, main)

**Files:**
- Create: `backend/__init__.py`, `backend/schemas.py`, `backend/session.py`, `backend/stream.py`, `backend/main.py`

- [ ] **Step 1: Create backend/__init__.py** (empty)

- [ ] **Step 2: Create backend/schemas.py**

```python
from pydantic import BaseModel
from typing import Optional


class PlanRequest(BaseModel):
    query: str
    # Optional structured overrides (frontend may pass these from form fields)
    origin: Optional[str] = None
    destination: Optional[str] = None
    num_days: Optional[int] = None
    budget: Optional[float] = None
    num_passengers: Optional[int] = None
    trip_type: Optional[str] = None


class PlanResponse(BaseModel):
    session_id: str


class HealthResponse(BaseModel):
    status: str = "ok"
```

- [ ] **Step 3: Create backend/session.py**

```python
import asyncio
import time
from typing import Dict, Optional

_SESSION_TTL = 1800  # 30 minutes

class Session:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.queue: asyncio.Queue = asyncio.Queue()
        self.created_at: float = time.time()

    def is_expired(self) -> bool:
        return time.time() - self.created_at > _SESSION_TTL


_store: Dict[str, Session] = {}


def create_session(session_id: str) -> Session:
    s = Session(session_id)
    _store[session_id] = s
    return s


def get_session(session_id: str) -> Optional[Session]:
    return _store.get(session_id)


def cleanup_expired() -> None:
    expired = [sid for sid, s in _store.items() if s.is_expired()]
    for sid in expired:
        del _store[sid]
```

- [ ] **Step 4: Create backend/stream.py**

```python
import json
from typing import AsyncGenerator
from .session import get_session


async def sse_generator(session_id: str) -> AsyncGenerator[str, None]:
    """Yield SSE-formatted strings from the session queue until sentinel."""
    session = get_session(session_id)
    if not session:
        yield _fmt("error", {"message": "Session not found"})
        return

    while True:
        item = await session.queue.get()
        if item is None:  # sentinel
            break
        yield _fmt(item["event"], item["data"])


def _fmt(event: str, data: object) -> str:
    payload = json.dumps(data) if not isinstance(data, str) else data
    return f"event: {event}\ndata: {payload}\n\n"
```

- [ ] **Step 5: Create backend/main.py**

```python
import asyncio
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from .schemas import PlanRequest, PlanResponse, HealthResponse
from .session import create_session, get_session, cleanup_expired
from .stream import sse_generator
from src.graph import TravelGraph

_graph: TravelGraph = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _graph
    _graph = TravelGraph()
    # Background cleanup task
    async def _cleanup():
        while True:
            await asyncio.sleep(300)
            cleanup_expired()
    asyncio.create_task(_cleanup())
    yield


app = FastAPI(title="Travel Concierge API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", response_model=HealthResponse)
async def health():
    return HealthResponse()


@app.post("/api/plan", response_model=PlanResponse)
async def plan(request: PlanRequest):
    session_id = str(uuid.uuid4())
    session = create_session(session_id)
    # Build a richer query string from structured fields if provided
    query = request.query
    if request.origin and request.origin not in query:
        query = f"{query} from {request.origin}"
    asyncio.create_task(_graph.invoke_streaming(query, session.queue))
    return PlanResponse(session_id=session_id)


@app.get("/api/stream/{session_id}")
async def stream(session_id: str):
    if not get_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    return StreamingResponse(
        sse_generator(session_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
```

- [ ] **Step 6: Run the server to verify it starts**

```bash
uvicorn backend.main:app --reload --port 8000
```

Expected: `Application startup complete.` with no errors. Visit `http://localhost:8000/api/health` — returns `{"status":"ok"}`. Stop with Ctrl+C.

- [ ] **Step 7: Commit**

```bash
git add backend/
git commit -m "feat: FastAPI backend with SSE streaming endpoints"
```

---

## Task 12: Integration tests for the API

**Files:**
- Create: `tests/integration/test_api.py`
- Create: `tests/integration/__init__.py`

- [ ] **Step 1: Create tests/integration/test_api.py**

```python
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from backend.main import app


@pytest.fixture
def mock_graph():
    async def fake_streaming(query, queue):
        await queue.put({"event": "agent_done", "data": {"agent": "research", "message": "Done"}})
        await queue.put({"event": "complete", "data": {"destination": "Paris", "itinerary": {}}})
        await queue.put(None)
    with patch("backend.main._graph") as mock:
        mock.invoke_streaming = AsyncMock(side_effect=fake_streaming)
        yield mock


@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_plan_returns_session_id(mock_graph):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/plan", json={"query": "3 days in Paris"})
    assert resp.status_code == 200
    assert "session_id" in resp.json()


@pytest.mark.asyncio
async def test_stream_404_unknown_session():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/stream/nonexistent-session-id")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_stream_delivers_events(mock_graph):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        plan_resp = await client.post("/api/plan", json={"query": "3 days in Paris"})
        session_id = plan_resp.json()["session_id"]
        # Give background task a moment to process
        import asyncio
        await asyncio.sleep(0.1)
        stream_resp = await client.get(f"/api/stream/{session_id}")
    assert stream_resp.status_code == 200
    assert "text/event-stream" in stream_resp.headers["content-type"]
```

- [ ] **Step 2: Run integration tests**

```bash
pytest tests/integration/test_api.py -v
```

Expected: 4 passed.

- [ ] **Step 3: Run full test suite**

```bash
pytest tests/unit tests/integration -v --cov=src --cov=backend --cov-report=term-missing
```

Expected: all pass, coverage ≥ 70%.

- [ ] **Step 4: Commit**

```bash
git add tests/integration/
git commit -m "test: integration tests for FastAPI SSE endpoints"
```

---

## Task 13: Cleanup — delete unused files, update .env.example

**Files:**
- Delete: `src/tools/mcp_client.py`, `src/tools/search.py`, `src/tools/flight_tool.py`, `src/tools/airport_tool.py`
- Modify: `.env.example`

- [ ] **Step 1: Delete obsolete files**

```bash
git rm src/tools/mcp_client.py src/tools/search.py src/tools/flight_tool.py src/tools/airport_tool.py
```

- [ ] **Step 2: Update .env.example**

```
# Required
GROQ_API_KEY=your_groq_api_key_here

# Required for real flight data (free at developers.amadeus.com)
AMADEUS_CLIENT_ID=your_amadeus_client_id
AMADEUS_CLIENT_SECRET=your_amadeus_client_secret

# Optional — enables LangSmith tracing
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=travel-concierge
```

- [ ] **Step 3: Commit**

```bash
git add .env.example
git commit -m "chore: remove unused tool stubs, update .env.example"
```

---

## Task 14: Create conftest.py

**Files:**
- Create: `tests/conftest.py`

- [ ] **Step 1: Create tests/conftest.py**

```python
import pytest
from src.state import TravelState, PlaceDetails, HotelOption, FlightOption


@pytest.fixture
def paris_state():
    return TravelState(
        user_input="3 days in Paris from New York for 2 people, budget $2000",
        origin="New York",
        destination="Paris",
        num_days=3,
        num_passengers=2,
        budget=2000.0,
        trip_type="solo",
    )


@pytest.fixture
def paris_places():
    return [
        PlaceDetails(name="Eiffel Tower", type="landmark", rating=4.7,
                     address="Paris", description="Iconic tower",
                     lat=48.8584, lng=2.2945),
        PlaceDetails(name="Louvre Museum", type="museum", rating=4.8,
                     address="Paris", description="Art museum",
                     lat=48.8606, lng=2.3376),
        PlaceDetails(name="Notre-Dame", type="cathedral", rating=4.6,
                     address="Paris", description="Gothic cathedral",
                     lat=48.8530, lng=2.3499),
    ]


@pytest.fixture
def sample_hotel():
    return HotelOption(name="Hotel du Louvre", estimated_price_per_night=180.0,
                       address="Paris", lat=48.8637, lng=2.3362)


@pytest.fixture
def sample_flight():
    return FlightOption(origin_airport="JFK", destination_airport="CDG",
                        departure="2026-06-01T08:00", arrival="2026-06-01T20:00",
                        price="$650 USD", airline="Air France", is_estimated=False)
```

- [ ] **Step 2: Run full suite with conftest in place**

```bash
pytest tests/unit tests/integration -v
```

Expected: all pass.

- [ ] **Step 3: Commit**

```bash
git add tests/conftest.py
git commit -m "test: add shared fixtures to conftest.py"
```

---

## Completion Check

- [ ] `uvicorn backend.main:app` starts without errors
- [ ] `GET /api/health` returns `{"status":"ok"}`
- [ ] `POST /api/plan` returns a `session_id`
- [ ] `GET /api/stream/{session_id}` streams SSE events
- [ ] `pytest tests/unit tests/integration` — all green
- [ ] Coverage ≥ 70% on `src/` and `backend/`
