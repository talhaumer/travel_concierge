import requests
from typing import Dict, Any, List
from ratelimit import limits, sleep_and_retry


@sleep_and_retry
@limits(calls=10, period=60)  # 10 calls per minute
def get_country_info(country_name: str) -> Dict[str, Any]:
    """Get country information using REST Countries API"""
    try:
        url = f"https://restcountries.com/v3.1/name/{country_name}"
        response = requests.get(url)
        response.raise_for_status()

        country_data = response.json()[0]

        return {
            "name": country_data.get("name", {}).get("common", country_name),
            "capital": country_data.get("capital", ["Unknown"])[0],
            "currency": (
                list(country_data.get("currencies", {}).keys())[0]
                if country_data.get("currencies")
                else "Unknown"
            ),
            "languages": list(country_data.get("languages", {}).values()),
            "population": country_data.get("population", 0),
            "timezones": country_data.get("timezones", []),
            "travel_tips": generate_travel_tips(country_data),
        }

    except Exception as e:
        print(f"Error getting country info: {e}")
        return get_fallback_country_info(country_name)


def generate_travel_tips(country_data: Dict[str, Any]) -> List[str]:
    """Generate travel tips based on country data"""
    tips = []

    # Basic tips based on available data
    if country_data.get("currencies"):
        currency = list(country_data["currencies"].keys())[0]
        tips.append(f"Local currency is {currency}")

    if country_data.get("languages"):
        languages = list(country_data["languages"].values())
        tips.append(f"Main languages: {', '.join(languages[:2])}")

    tips.append("Check visa requirements before travel")
    tips.append("Have travel insurance")
    tips.append("Keep emergency contacts handy")

    return tips


def get_fallback_country_info(country_name: str) -> Dict[str, Any]:
    """Fallback country information"""
    common_countries = {
        "france": {
            "name": "France",
            "capital": "Paris",
            "currency": "EUR",
            "languages": ["French"],
            "population": 67390000,
            "travel_tips": [
                "Try local cuisine",
                "Learn basic French phrases",
                "Validate train tickets before boarding",
            ],
        },
        "japan": {
            "name": "Japan",
            "capital": "Tokyo",
            "currency": "JPY",
            "languages": ["Japanese"],
            "population": 125800000,
            "travel_tips": [
                "Carry cash",
                "Learn bowing etiquette",
                "Remove shoes when entering homes",
            ],
        },
    }

    return common_countries.get(
        country_name.lower(),
        {
            "name": country_name,
            "capital": "Unknown",
            "currency": "Unknown",
            "languages": ["Unknown"],
            "population": 0,
            "travel_tips": [
                "Check travel advisories",
                "Research local customs",
                "Stay hydrated",
            ],
        },
    )
