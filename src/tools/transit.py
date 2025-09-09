import requests
from typing import Dict, List, Any
from ratelimit import limits, sleep_and_retry


@sleep_and_retry
@limits(calls=5, period=60)  # 5 calls per minute
def get_public_transit(city: str) -> Dict[str, Any]:
    """Get public transit information for a city"""
    try:
        # Using TransitLand API (free tier)
        url = f"https://transit.land/api/v2/rest/feeds"
        params = {"served_by": city.lower()}

        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        feeds = data.get("feeds", [])

        transit_info = {"city": city, "available_systems": [], "recommendations": []}

        for feed in feeds[:3]:  # Limit to top 3
            transit_info["available_systems"].append(
                {
                    "name": feed.get("name", "Unknown"),
                    "type": feed.get("type", "transit"),
                }
            )

        # Add general recommendations
        transit_info["recommendations"] = [
            "Download local transit app",
            "Purchase day passes for savings",
            "Check operating hours",
            "Validate tickets when required",
        ]

        return transit_info

    except Exception as e:
        print(f"Error getting transit info: {e}")
        return get_fallback_transit_info(city)


def get_fallback_transit_info(city: str) -> Dict[str, Any]:
    """Fallback transit information"""
    common_cities = {
        "paris": {
            "city": "Paris",
            "available_systems": [
                {"name": "Metro", "type": "subway"},
                {"name": "RER", "type": "regional_rail"},
                {"name": "Bus", "type": "bus"},
            ],
            "recommendations": [
                "Get a Navigo card for unlimited travel",
                "Metro runs until 2am on weekends",
                "Validate tickets before boarding",
            ],
        },
        "london": {
            "city": "London",
            "available_systems": [
                {"name": "Tube", "type": "subway"},
                {"name": "Bus", "type": "bus"},
                {"name": "DLR", "type": "light_rail"},
            ],
            "recommendations": [
                "Use Oyster card or contactless payment",
                "Avoid peak hours (7-9:30am, 4-7pm)",
                "Download Tube Map app",
            ],
        },
    }

    return common_cities.get(
        city.lower(),
        {
            "city": city,
            "available_systems": [{"name": "Local Transit", "type": "unknown"}],
            "recommendations": [
                "Research local transit options",
                "Check for tourist passes",
                "Ask locals for best routes",
            ],
        },
    )
