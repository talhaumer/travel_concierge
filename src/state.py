from datetime import date, datetime
from typing import Optional, List, Dict, Any, TypedDict
from enum import Enum
from pydantic import BaseModel, Field
import json


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


class FlightOption(BaseModel):
    origin_airport: str
    destination_airport: str
    departure: str
    arrival: str
    price: str
    airline: str

class Airport(BaseModel):
    name: str
    code: Optional[str] = None   # e.g., DXB, MED
    city: Optional[str] = None
    country: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    source: str

class TravelState(BaseModel):
    # Core travel information
    user_input: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    date_of_travel: Optional[date] = None
    num_days: Optional[int] = None
    trip_type: Optional[str] = None
    num_passengers: Optional[int] = None
    budget: Optional[float] = None

    # Processing state
    is_complete: bool = False
    status: StateStatus = StateStatus.RUNNING
    error: Optional[str] = None
    needs_fallback: bool = False
    circuit_breaker_count: int = 0

    # Agent outputs
    retrieved_places: List[PlaceDetails] = []
    flights: List[FlightOption] = []
    day_plan: Dict[str, List[ItineraryItem]] = {}
    final_output: Optional[Dict[str, Any]] = None

    # Research data
    weather_info: Optional[Dict[str, Any]] = None
    country_info: Optional[Dict[str, Any]] = None
    transit_info: Optional[Dict[str, Any]] = None
    research_data: Optional[Dict[str, Any]] = None

    # Guardrails and monitoring
    tools_used: List[str] = []
    violations: List[str] = []
    tool_errors: Dict[str, List[str]] = {}


# from pydantic import BaseModel, Field
# from typing import List, Optional, Dict, Any
# from datetime import date
# from enum import Enum

# class StateStatus(str, Enum):
#     RUNNING = "running"
#     COMPLETE = "complete"

# class BaseRunState(BaseModel):
#     is_complete: bool = Field(default=False, description="Whether the workflow is complete")
#     status: StateStatus = Field(default=StateStatus.RUNNING, description="Current state status")
#     error: Optional[str] = Field(None, description="Error message if any")

# # Tourist place
# class Place(BaseModel):
#     name: str
#     type: str
#     rating: Optional[float] = None
#     open_hours: Optional[str] = None
#     lat: float
#     lng: float
#     distance_from_center: Optional[float] = None
#     website: Optional[str] = None

# # Itinerary item
# class ItineraryItem(BaseModel):
#     time: str
#     activity: str
#     notes: Optional[str] = None

# class Airport(BaseModel):
#     name: str
#     code: Optional[str] = None   # e.g., DXB, MED
#     city: Optional[str] = None
#     country: Optional[str] = None
#     lat: Optional[float] = None
#     lng: Optional[float] = None
#     source: str

# class Flight(BaseModel):
#     origin_airport: str
#     destination_airport: str
#     departure: str
#     arrival: str
#     price: str
#     airline: str

# class TravelState(BaseModel):
#     user_input: Optional[str] = None
#     origin: Optional[str] = None
#     destination: Optional[str] = None
#     date_of_travel: Optional[date] = None
#     num_days: Optional[int] = None
#     trip_type: Optional[str] = None
#     num_passengers: Optional[int] = None
#     is_complete: bool = False

# # Main runtime state (extends BaseRunState)
# class RunState(BaseRunState):

#     # User input and location fields
#     user_input: Optional[str] = Field(None, description="Raw user input")
#     origin: Optional[str] = Field(None, description="Departure city/airport")
#     destination: Optional[str] = Field(None, description="Destination city/airport")

#     # Core travel parameters (make optional!)
#     city: Optional[str] = Field(None, description="Destination city")
#     days: Optional[int] = Field(None, description="Number of days for the trip")
#     preferences: List[str] = Field(default_factory=list, description="User preferences")

#     # Workflow data
#     tools_used: List[str] = Field(default_factory=list, description="List of tools used")
#     violations: List[str] = Field(default_factory=list, description="Validation violations")
#     tool_errors: Dict[str, str] = Field(default_factory=dict, description="Tool error messages")
#     retrieved_places: List[Place] = Field(default_factory=list, description="Retrieved tourist places")
#     airport: Optional[Airport] = Field(None, description="Airport information")
#     flights: List[Flight] = Field(default_factory=list, description="Flight options")
#     day_plan: Dict[str, List[ItineraryItem]] = Field(default_factory=dict, description="Daily itinerary")
#     final_output: Optional[Dict] = Field(None, description="Final output dictionary")
#     needs_fallback: bool = Field(default=False, description="Whether fallback is needed")
#     circuit_breaker_count: int = Field(default=0, description="Circuit breaker counter")
#     destination_airport_code: Optional[str] = Field(None, description="Destination airport code")

#     # Additional travel info
#     date_of_travel: Optional[date] = Field(None, description="Travel date")
#     trip_type: Optional[str] = Field(None, description="One-way or round-trip")
#     num_passengers: Optional[int] = Field(None, description="Number of passengers")
#     num_days: Optional[int] = Field(None, description="Number of days")
#     budget: Optional[str] = Field(None, description="Budget level")
#     # def check_complete(self) -> bool:
#     #     """Check if all required fields are filled in."""
#     #     return all([
#     #         self.city,
#     #         self.days,
#     #         self.origin,
#     #         self.destination_airport_code,
#     #         self.date_of_travel,
#     #         self.trip_type,
#     #         self.num_passengers,
#     #     ])
