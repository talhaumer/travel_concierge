import requests
from typing import Dict, Any
from ratelimit import limits, sleep_and_retry


@sleep_and_retry
@limits(calls=5, period=60)  # 5 calls per minute
def get_weather(location: str, date: str = None) -> Dict[str, Any]:
    """Get weather forecast using Open-Meteo API"""
    try:
        # First get coordinates from OpenStreetMap
        geocode_url = "https://nominatim.openstreetmap.org/search"
        geocode_params = {"q": location, "format": "json", "limit": 1}

        geocode_response = requests.get(
            geocode_url,
            params=geocode_params,
            headers={"User-Agent": "TravelConciergeApp/1.0"},
        )
        geocode_response.raise_for_status()

        location_data = geocode_response.json()
        if not location_data:
            return get_fallback_weather(location)

        lat = location_data[0]["lat"]
        lon = location_data[0]["lon"]

        # Get weather data
        weather_url = "https://api.open-meteo.com/v1/forecast"
        weather_params = {
            "latitude": lat,
            "longitude": lon,
            "daily": ["temperature_2m_max", "temperature_2m_min", "weathercode"],
            "timezone": "auto",
            "forecast_days": 7,
        }

        weather_response = requests.get(weather_url, params=weather_params)
        weather_response.raise_for_status()

        weather_data = weather_response.json()
        daily = weather_data["daily"]

        # Map weather codes to descriptions
        weather_codes = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Fog",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            80: "Slight rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",
        }

        return {
            "location": location,
            "forecast": weather_codes.get(daily["weathercode"][0], "Unknown"),
            "temperature": {
                "high": daily["temperature_2m_max"][0],
                "low": daily["temperature_2m_min"][0],
            },
            "recommendation": get_weather_recommendation(daily["weathercode"][0]),
        }

    except Exception as e:
        print(f"Error getting weather: {e}")
        return get_fallback_weather(location)


def get_weather_recommendation(weather_code: int) -> str:
    """Generate recommendation based on weather code"""
    if weather_code in [0, 1, 2]:  # Clear to partly cloudy
        return "Perfect weather for outdoor activities and sightseeing"
    elif weather_code in [3]:  # Overcast
        return "Good day for indoor activities and museums"
    elif weather_code in [45, 48]:  # Fog
        return "Be cautious when driving, good for photography"
    elif weather_code in [51, 53, 55, 61, 63, 65, 80, 81, 82]:  # Rain
        return "Bring an umbrella, good day for indoor attractions"
    else:
        return "Check local weather conditions"


def get_fallback_weather(location: str) -> Dict[str, Any]:
    """Fallback weather data"""
    return {
        "location": location,
        "forecast": "Generally pleasant",
        "temperature": {"high": 22, "low": 15},
        "recommendation": "Good weather for travel and sightseeing",
    }
