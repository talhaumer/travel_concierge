from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date


class FinalOutputSchema(BaseModel):
    origin: str
    destination: str
    travel_date: Optional[str]
    duration_days: int
    passengers: Optional[int]
    budget: Optional[float]
    itinerary: Dict[str, List[Dict[str, Any]]]
    recommended_places: List[Dict[str, Any]]
    tools_used: List[str]
    generated_at: str


def validate_schema(data: Any, schema: BaseModel) -> bool:
    try:
        schema.model_validate(data)
        return True
    except:
        return False
