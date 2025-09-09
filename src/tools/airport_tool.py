import requests

import sys, os

sys.path.append(os.path.abspath(".."))
from src.state import Airport
from src.constants import RAPID_API_KEY, RAPI_API_HOST


class AirportTool:
    def __init__(self):
        self.api_key = RAPID_API_KEY
        self.host = RAPI_API_HOST

    def search_airport(self, query: str, locale: str = "en-US") -> Airport:
        url = f"https://{self.host}/api/v1/flights/searchAirport"
        querystring = {"query": query, "locale": locale}
        headers = {"x-rapidapi-key": self.api_key, "x-Rapidapi-host": self.host}

        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()
        data = response.json().get("data", [])

        if not data:
            raise ValueError(f"No airport found for query: {query}")

        airport_info = data[0]
        return Airport(
            name=airport_info.get("presentation", {}).get("title"),
            code=airport_info.get("navigation", {})
            .get("relevantFlightParams", {})
            .get("skyId"),
            city=airport_info.get("presentation", {}).get("subtitle"),
            country=airport_info.get("presentation", {}).get("country", None),
            lat=airport_info.get("coordinates", {}).get("latitude"),
            lng=airport_info.get("coordinates", {}).get("longitude"),
            source="Sky-Scrapper API",
        )
