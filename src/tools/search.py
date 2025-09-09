import requests
import os
from typing import List
from ..state import PlaceDetails


def search_places(query: str, limit: int = 10) -> List[PlaceDetails]:
    """Search for places using a mock API"""
    # In a real implementation, this would call Google Places API or similar
    mock_places = [
        PlaceDetails(
            name="Eiffel Tower",
            type="Landmark",
            rating=4.7,
            address="Champ de Mars, 5 Avenue Anatole France, 75007 Paris",
            description="Iconic wrought-iron tower offering city views",
        ),
        PlaceDetails(
            name="Louvre Museum",
            type="Museum",
            rating=4.8,
            address="Rue de Rivoli, 75001 Paris",
            description="Historic art museum housing the Mona Lisa",
        ),
    ]
    return mock_places[:limit]
