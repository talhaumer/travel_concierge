import time
from functools import wraps
from typing import Callable, Any, List, Dict
from .state import TravelState, StateStatus

def with_retry(max_retries: int = 2, delay: float = 1.0):
    """Decorator for retrying function calls with exponential backoff"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        sleep_time = delay * (2 ** attempt)  # Exponential backoff
                        time.sleep(sleep_time)
                        continue
                    else:
                        raise last_exception
            return wrapper
        return decorator

def circuit_breaker(max_failures: int = 3):
    """Circuit breaker pattern to prevent cascading failures - for agent methods"""
    def decorator(func: Callable):
        failures = 0
        
        @wraps(func)
        def wrapper(state: TravelState, *args, **kwargs):
            nonlocal failures
            if failures >= max_failures:
                state.circuit_breaker_count += 1
                state.status = StateStatus.FAILED
                state.error = "Circuit breaker triggered - too many failures"
                return state
                
            try:
                result = func(state, *args, **kwargs)
                failures = 0  # Reset on success
                return result
            except Exception as e:
                failures += 1
                state.circuit_breaker_count += 1
                raise e
        return wrapper
    return decorator

def with_fallback(fallback_func: Callable):
    """Decorator to provide fallback behavior"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print(f"Primary function failed: {e}. Using fallback.")
                return fallback_func(*args, **kwargs)
        return wrapper
    return decorator

# Fallback implementations
def fallback_search_places(query: str, limit: int = 5) -> List[Any]:
    """Fallback for place search"""
    return [{"name": "General sightseeing", "type": "fallback", "rating": 4.0}]

def fallback_get_weather(location: str) -> Dict[str, Any]:
    """Fallback for weather data"""
    return {
        "location": location,
        "forecast": "Weather data unavailable",
        "recommendation": "Check local weather forecast"
    }