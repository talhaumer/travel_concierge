from typing import List
from src.state import FlightOption, Airport


class FlightTool:
    """Dummy flight tool to return top 3 flights from origin to destination."""

    def fetch_flights(
        self, origin_airport: Airport, destination_airport: Airport
    ) -> List[FlightOption]:
        # Dummy flight data
        flights = [
            FlightOption(
                origin_airport=origin_airport.code or origin_airport.name,
                destination_airport=destination_airport.code
                or destination_airport.name,
                departure="2025-09-10T08:00",
                arrival="2025-09-10T11:00",
                price="$200",
                airline="AirDemo",
            ),
            FlightOption(
                origin_airport=origin_airport.code or origin_airport.name,
                destination_airport=destination_airport.code
                or destination_airport.name,
                departure="2025-09-10T12:00",
                arrival="2025-09-10T15:00",
                price="$220",
                airline="FlyTest",
            ),
            FlightOption(
                origin_airport=origin_airport.code or origin_airport.name,
                destination_airport=destination_airport.code
                or destination_airport.name,
                departure="2025-09-10T16:00",
                arrival="2025-09-10T19:00",
                price="$250",
                airline="DemoAir",
            ),
        ]
        return flights
