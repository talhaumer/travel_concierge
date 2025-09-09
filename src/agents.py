from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_community.chat_models import ChatOpenAI
from langchain.schema import BaseOutputParser
from src.tools.country import get_country_info
from src.tools.transit import get_public_transit
from src.tools.flight_tool import FlightTool
from src.state import TravelState, PlaceDetails, ItineraryItem, FlightOption, StateStatus
from src.tools import search_places, get_weather
from .guardrails import validate_schema, moderate_content, FinalOutputSchema
import json
from typing import List, Dict, Any
import re
from dateutil.parser import parse
from datetime import datetime
from .fallbacks import circuit_breaker, with_retry, with_fallback


class BaseAgent:
    def __init__(self, model_name="openai/gpt-oss-20b", api_key=None):
        self.llm = ChatGroq(model=model_name, temperature=0.1, api_key=api_key)

    def validate_output(self, output: Any, schema: Any) -> bool:
        return validate_schema(output, schema)


class UserInputAgent(BaseAgent):
    def extract_travel_info(self, user_input: str) -> Dict[str, Any]:
        system_prompt = """
        Extract travel information from the user's input. Return valid JSON with:
        - origin: string or null
        - destination: string or null  
        - date_of_travel: YYYY-MM-DD or null
        - num_days: integer or null
        - trip_type: "one-way", "round-trip" or null
        - num_passengers: integer or null
        - budget: float or null
        
        Example: "I want to go to Paris from Dubai for 5 days in October with 2 people"
        Output: {{"origin": "Dubai", "destination": "Paris", "date_of_travel": null, 
                 "num_days": 5, "trip_type": null, "num_passengers": 2, "budget": null}}
        """

        prompt = ChatPromptTemplate.from_messages(
            [("system", system_prompt), ("human", "{input}")]
        )

        chain = prompt | self.llm
        response = chain.invoke({"input": user_input})

        # Extract JSON from response
        try:
            json_str = re.search(r"\{.*\}", response.content, re.DOTALL).group()
            return json.loads(json_str)
        except (json.JSONDecodeError, AttributeError):
            return {}

    def process(self, state: TravelState) -> TravelState:
        if not state.user_input:
            state.error = "No user input provided"
            return state

        extracted = self.extract_travel_info(state.user_input)

        # Update state with extracted values
        if extracted:
            state.origin = extracted.get("origin", state.origin)
            state.destination = extracted.get("destination", state.destination)

            date_str = extracted.get("date_of_travel")
            if date_str:
                try:
                    state.date_of_travel = parse(date_str).date()
                except:
                    pass

            state.num_days = extracted.get("num_days", state.num_days)
            state.trip_type = extracted.get("trip_type", state.trip_type)
            state.num_passengers = extracted.get("num_passengers", state.num_passengers)
            state.budget = extracted.get("budget", state.budget)

        # Check if we have minimum required info
        if state.origin and state.destination:
            state.is_complete = True

        return state


# In src/agents.py - Update the ResearchAgent class
class ResearchAgent(BaseAgent):
    def __init__(self, model_name="openai/gpt-oss-20b", api_key=None):
        super().__init__(model_name, api_key)

    def research_destination(self, destination: str, num_days: int) -> Dict[str, Any]:
        """Comprehensive destination research"""
        # Extract city and country from destination
        city_name = destination.split(",")[0].strip() if "," in destination else destination
        country_name = destination.split(",")[-1].strip() if "," in destination else "France"  # Default to France for Paris
        
        research_data = {
            "places": search_places("tourist attractions", city_name, num_days * 2),
            "weather": get_weather(destination),
            "country_info": get_country_info(country_name),
            "transit_info": get_public_transit(city_name),
        }

        return research_data
    
    def process(self, state: TravelState) -> TravelState:
        if not state.destination or not state.num_days:
            state.error = "Missing destination or number of days"
            return state

        try:
            research_data = self.research_destination(state.destination, state.num_days)

            # Store research data in state
            state.retrieved_places = research_data["places"]
            # Add research_data field to state if needed, or store individually
            state.weather_info = research_data["weather"]
            state.country_info = research_data["country_info"]
            state.transit_info = research_data["transit_info"]

            state.tools_used.extend(
                [
                    "search_places",
                    "get_weather",
                    "get_country_info",
                    "get_public_transit",
                ]
            )

        except Exception as e:
            state.error = f"Research failed: {str(e)}"
            state.needs_fallback = True
            print(f"Research error: {e}")  # Debug print

        return state


class PlannerAgent(BaseAgent):
    def create_itinerary(
        self, places: List[PlaceDetails], num_days: int
    ) -> Dict[str, List[ItineraryItem]]:
        itinerary = {}

        # Group places by type for better planning
        cultural_sites = [
            p
            for p in places
            if any(term in p.type.lower() for term in ["museum", "historical", "cathedral", "chapel", "landmark", "monument"])
        ]
        outdoor_activities = [
            p for p in places if any(term in p.type.lower() for term in ["park", "garden", "outdoor"])
        ]
        entertainment = [
            p
            for p in places
            if any(term in p.type.lower() for term in ["restaurant", "shopping", "entertainment"])
        ]
        
        # If no places match the categories, use all places
        if not cultural_sites and not outdoor_activities and not entertainment:
            cultural_sites = places[:3]  # Use first 3 places as cultural sites

        for day in range(1, num_days + 1):
            day_plan = []

            # Morning activity (cultural)
            if cultural_sites:
                site = cultural_sites.pop(0)
                day_plan.append(
                    ItineraryItem(
                        time="09:00",
                        activity=f"Visit {site.name}",
                        notes=f"{site.type}, Rating: {site.rating}",
                    )
                )

            # Afternoon activity (outdoor)
            if outdoor_activities:
                activity = outdoor_activities.pop(0)
                day_plan.append(
                    ItineraryItem(
                        time="13:00",
                        activity=f"Visit {activity.name}",
                        notes=f"{activity.type}, Rating: {activity.rating}",
                    )
                )

            # Evening activity (entertainment)
            if entertainment:
                venue = entertainment.pop(0)
                day_plan.append(
                    ItineraryItem(
                        time="18:00",
                        activity=f"Visit {venue.name}",
                        notes=f"{venue.type}, Rating: {venue.rating}",
                    )
                )

            itinerary[f"day_{day}"] = day_plan

        return itinerary

    def create_basic_itinerary(self, num_days: int, destination: str) -> Dict[str, List[ItineraryItem]]:
        """Create a basic itinerary when no specific places are available"""
        itinerary = {}
        
        # Basic activities for any destination
        basic_activities = [
            ("09:00", "City walking tour", "Explore the historic city center"),
            ("11:00", "Visit local museum", "Discover local history and culture"),
            ("13:00", "Lunch at local restaurant", "Try authentic local cuisine"),
            ("15:00", "Visit main landmark", "See the city's most famous attraction"),
            ("17:00", "Shopping district", "Browse local shops and markets"),
            ("19:00", "Dinner at recommended restaurant", "Enjoy a memorable dining experience"),
        ]
        
        for day in range(1, num_days + 1):
            day_plan = []
            for time, activity, notes in basic_activities:
                day_plan.append(
                    ItineraryItem(
                        time=time,
                        activity=activity,
                        notes=notes
                    )
                )
            itinerary[f"day_{day}"] = day_plan

        return itinerary

    def process(self, state: TravelState) -> TravelState:
        if not state.num_days:
            state.error = "Missing number of days for planning"
            return state

        # If no places retrieved, create a basic itinerary with generic activities
        if not state.retrieved_places:
            state.day_plan = self.create_basic_itinerary(state.num_days, state.destination)
        else:
            try:
                state.day_plan = self.create_itinerary(
                    state.retrieved_places, state.num_days
                )
            except Exception as e:
                state.error = f"Planning failed: {str(e)}"
                state.needs_fallback = True

        return state


class WriterAgent(BaseAgent):
    def generate_final_output(self, state: TravelState) -> Dict[str, Any]:
        # Moderate content before final output
        moderation_result = moderate_content(str(state.day_plan))
        if not moderation_result["is_safe"]:
            state.violations.append(
                f"Content moderation failed: {moderation_result['issues']}"
            )

        # Convert ItineraryItem objects to dictionaries for schema compliance
        itinerary_dict = {}
        for day, activities in state.day_plan.items():
            itinerary_dict[day] = [activity.dict() for activity in activities]
        
        output = {
            "origin": state.origin,
            "destination": state.destination,
            "travel_date": str(state.date_of_travel) if state.date_of_travel else None,
            "duration_days": state.num_days,
            "passengers": state.num_passengers,
            "budget": state.budget,
            "itinerary": itinerary_dict,
            "recommended_places": [place.dict() for place in state.retrieved_places],
            "tools_used": state.tools_used,
            "generated_at": datetime.now().isoformat(),
        }

        # Validate against schema
        if not self.validate_output(output, FinalOutputSchema):
            state.violations.append("Final output schema validation failed")

        return output

    def process(self, state: TravelState) -> TravelState:
        try:
            state.final_output = self.generate_final_output(state)
            state.status = StateStatus.COMPLETED
        except Exception as e:
            state.error = f"Writing failed: {str(e)}"
            state.needs_fallback = True

        return state


class ReviewerAgent(BaseAgent):
    def review_itinerary(self, itinerary: Dict[str, Any]) -> Dict[str, Any]:
        # Check for completeness, safety, and quality
        issues = []

        # Check if each day has activities
        for day, activities in itinerary.items():
            if not activities:
                issues.append(f"{day} has no activities planned")

        # Check for diversity of activities
        activity_types = set()
        for day_activities in itinerary.values():
            for activity in day_activities:
                if "visit" in activity.activity.lower():
                    activity_types.add("sightseeing")
                elif (
                    "eat" in activity.activity.lower()
                    or "restaurant" in activity.activity.lower()
                ):
                    activity_types.add("dining")
                elif "shop" in activity.activity.lower():
                    activity_types.add("shopping")

        if len(activity_types) < 2 and len(itinerary) > 1:
            issues.append("Itinerary lacks activity diversity")

        return {
            "approved": len(issues) == 0,
            "issues": issues,
            "recommendations": ["Add more activity types"] if issues else [],
        }

    def process(self, state: TravelState) -> TravelState:
        if not state.day_plan:
            state.error = "No itinerary to review"
            return state

        review_result = self.review_itinerary(state.day_plan)

        if not review_result["approved"]:
            state.violations.extend(review_result["issues"])
            state.needs_fallback = True

        return state

