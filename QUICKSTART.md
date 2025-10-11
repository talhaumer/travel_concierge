# 🚀 Quick Start Guide

Get up and running with Travel Concierge in under 5 minutes!

## Prerequisites

- Python 3.11 or higher
- Groq API key ([Get one here](https://console.groq.com/))

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/travel_concierge.git
   cd travel_concierge
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your API key**
   
   Open `travel_concierge/src/graph.py` and update line 11 with your Groq API key:
   ```python
   GROQ_API_KEY = "your_api_key_here"
   ```

## Your First Travel Plan

### Option 1: Jupyter Notebook (Recommended)

1. **Launch Jupyter**
   ```bash
   jupyter notebook
   ```

2. **Open the demo**
   - Navigate to `notebooks/demo.ipynb`
   - Run all cells (Cell → Run All)

3. **Customize your query**
   - Modify the `user_query` variable with your travel plans
   - Run the cell again

### Option 2: Python Script

Create a file `test_travel.py`:

```python
from travel_concierge.src.graph import TravelGraph

# Initialize the travel planner
travel_graph = TravelGraph()

# Plan your trip
user_query = """
Plan a 3-day trip to Paris from New York, 
focusing on art and culture with a budget 
of $2000 for two people.
"""

# Get the results
result = travel_graph.invoke(user_query)

# Print the itinerary
print(f"\n🌍 Travel Plan: {result['origin']} → {result['destination']}")
print(f"📅 Duration: {result['num_days']} days")
print(f"💰 Budget: ${result['budget']}")
print(f"👥 Passengers: {result['num_passengers']}")

print("\n📋 Itinerary:")
for day, activities in result['day_plan'].items():
    print(f"\n{day.upper().replace('_', ' ')}:")
    for activity in activities:
        print(f"  ⏰ {activity.time} - {activity.activity}")
        print(f"     📝 {activity.notes}")

print("\n📍 Recommended Places:")
for place in result.get('recommended_places', [])[:5]:
    print(f"  • {place['name']} ({place['type']}) - ⭐ {place['rating']}")
```

Run it:
```bash
python test_travel.py
```

## Example Output

```
🌍 Travel Plan: New York → Paris
📅 Duration: 3 days
💰 Budget: $2000.0
👥 Passengers: 2

📋 Itinerary:

DAY 1:
  ⏰ 09:00 - Visit Eiffel Tower
     📝 landmark, Rating: 4.7
  ⏰ 13:00 - Visit Louvre Museum
     📝 museum, Rating: 4.8
  ⏰ 18:00 - Visit Arc de Triomphe
     📝 monument, Rating: 4.5

DAY 2:
  ⏰ 09:00 - Visit Notre-Dame Cathedral
     📝 cathedral, Rating: 4.6
  ⏰ 13:00 - Visit Musée d'Orsay
     📝 museum, Rating: 4.7

DAY 3:
  ⏰ 09:00 - Visit Sainte-Chapelle
     📝 chapel, Rating: 4.6

📍 Recommended Places:
  • Eiffel Tower (landmark) - ⭐ 4.7
  • Louvre Museum (museum) - ⭐ 4.8
  • Notre-Dame Cathedral (cathedral) - ⭐ 4.6
  • Arc de Triomphe (monument) - ⭐ 4.5
  • Musée d'Orsay (museum) - ⭐ 4.7
```

## Common Query Formats

The system understands natural language. Try:

```python
# Simple query
"Plan a 5-day trip to Tokyo"

# Detailed query
"I want to visit London from Paris for 4 days with my family (3 people)"

# Budget-focused
"Plan a budget trip to Rome for 3 days, under $1500"

# Interest-specific
"Plan a 7-day cultural tour of Kyoto focusing on temples and traditional crafts"

# Multi-destination
"Plan a 10-day trip covering Barcelona, Madrid, and Seville"
```

## Accessing Additional Information

```python
result = travel_graph.invoke(user_query)

# Weather information
weather = result['weather_info']
print(f"Temperature: {weather['temperature']['high']}°C / {weather['temperature']['low']}°C")
print(f"Forecast: {weather['forecast']}")

# Country information
country = result['country_info']
print(f"Currency: {country['currency']}")
print(f"Languages: {', '.join(country['languages'])}")
print(f"Travel Tips: {country['travel_tips']}")

# Transit information
transit = result['transit_info']
for system in transit['available_systems']:
    print(f"- {system['name']} ({system['type']})")
print(f"Recommendations: {transit['recommendations']}")

# Tools used
print(f"Tools Used: {result['tools_used']}")
```

## Troubleshooting

### API Key Issues

**Error**: `GroqError: The api_key client option must be set`

**Solution**: Make sure you've set your API key in `src/graph.py`

### Import Errors

**Error**: `ModuleNotFoundError: No module named 'langchain'`

**Solution**: Install dependencies
```bash
pip install -r requirements.txt
```

### Empty Results

**Issue**: Getting empty itineraries or no places

**Solution**: This usually means API rate limits or connectivity issues. The system uses fallback data automatically, but you can check:
- Internet connection
- API key validity
- Rate limits on external APIs

## Next Steps

- 📖 Read the full [README.md](README.md) for detailed documentation
- 🔧 Customize agents in `src/agents.py`
- 🎨 Add new destinations to fallback data in `src/tools/places.py`
- 📊 Enable tracing with LangSmith (see [README.md](README.md))
- 🤝 Contribute! See [CONTRIBUTING.md](CONTRIBUTING.md)

## Need Help?

- 📚 Check the [README.md](README.md) for detailed docs
- 🐛 Found a bug? [Open an issue](https://github.com/yourusername/travel_concierge/issues)
- 💡 Have questions? [Start a discussion](https://github.com/yourusername/travel_concierge/discussions)

---

**Happy travels! ✈️**

