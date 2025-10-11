# 🌍 Travel Concierge Multi-Agent System

A production-ready multi-agent workflow built with LangGraph that intelligently plans travel itineraries using specialized AI agents, comprehensive security guardrails, robust fallbacks, and full observability.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![LangGraph](https://img.shields.io/badge/LangGraph-latest-green.svg)](https://langchain-ai.github.io/langgraph/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Features

- **🤖 Multi-Agent Collaboration**: Five specialized agents working together for comprehensive travel planning
- **🔒 Security Guardrails**: Prompt hardening, schema validation, content moderation, and PII detection
- **🛡️ Fallbacks & Resilience**: Retry mechanisms, circuit breakers, and graceful degradation
- **📊 Tracing & Observability**: LangSmith integration for comprehensive monitoring and debugging
- **🌐 External APIs**: Integration with weather, places, country info, and transit APIs
- **🎯 Smart Routing**: Conditional edges for quality review and error handling

## 🏗️ Architecture

### Agent Pipeline

```
User Input → UserInputAgent → ResearchAgent → PlannerAgent → ReviewerAgent → WriterAgent → Final Output
                    ↓              ↓              ↓              ↓              ↓
                [Extract]      [Research]     [Create]       [Review]      [Generate]
                [Info]         [Places]       [Itinerary]    [Quality]     [Output]
```

### Agent Responsibilities

1. **UserInputAgent** 🎤
   - Extracts travel information from natural language queries
   - Parses origin, destination, dates, budget, passengers
   - Uses LLM for intelligent information extraction

2. **ResearchAgent** 🔍
   - Gathers comprehensive destination information
   - Fetches tourist attractions, weather forecasts, country info
   - Retrieves public transit information
   - Implements fallback data for reliable operation

3. **PlannerAgent** 📅
   - Creates detailed day-by-day itineraries
   - Categorizes places by type (cultural, outdoor, entertainment)
   - Distributes activities across days intelligently
   - Handles edge cases with generic itineraries

4. **ReviewerAgent** ✅
   - Validates itinerary completeness and quality
   - Checks for activity diversity
   - Identifies potential issues
   - Routes to fallback if quality thresholds not met

5. **WriterAgent** ✍️
   - Generates final structured output
   - Applies content moderation
   - Validates against schema
   - Includes metadata and tool usage tracking

## 🛡️ Security & Guardrails

### Implemented Guardrails

1. **Prompt Hardening**
   - System prompts explicitly forbid misuse
   - Safety reminders in critical operations
   - Input sanitization

2. **Schema Validation**
   - All outputs validate against Pydantic schemas
   - Type checking and constraint enforcement
   - Violation tracking and reporting

3. **Content Moderation**
   - Post-generation safety checks
   - Policy compliance verification
   - Automated flagging of inappropriate content

4. **PII Detection**
   - Identifies personally identifiable information
   - Automatic redaction capabilities
   - Privacy protection built-in

## 🔄 Fallbacks & Resilience

- **Per-Tool Retries**: Exponential backoff for failed API calls
- **Fallback Data**: Curated fallback responses for common destinations
- **Circuit Breaker**: Prevents cascading failures after consecutive errors
- **Graceful Degradation**: System continues with reduced functionality
- **Error Tracking**: Comprehensive error logging and state management

## 📦 Installation

### Prerequisites

- Python 3.11 or higher
- pip package manager
- API keys (Groq, optional: LangSmith)

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/travel_concierge.git
   cd travel_concierge
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API keys**
   - Update `src/graph.py` with your Groq API key
   - (Optional) Set up LangSmith for tracing

4. **Run the demo**
   ```bash
   jupyter notebook notebooks/demo.ipynb
   ```

## 🚀 Usage

### Basic Usage

```python
from travel_concierge.src.graph import TravelGraph

# Initialize the travel planning system
travel_graph = TravelGraph()

# Plan a trip
user_query = """
Plan a 3-day trip to Paris from New York, focusing on art and culture 
with a budget of $2000 for two people. Include must-see attractions, 
local dining options, and a mix of guided tours and free exploration.
"""

result = travel_graph.invoke(user_query)

# Access the results
print(f"Origin: {result['origin']}")
print(f"Destination: {result['destination']}")
print(f"Duration: {result['num_days']} days")
print(f"\nItinerary:")
for day, activities in result['day_plan'].items():
    print(f"\n{day.upper()}:")
    for activity in activities:
        print(f"  {activity.time} - {activity.activity}")
```

### Advanced Usage

```python
# Access detailed information
weather = result.get('weather_info')
country = result.get('country_info')
transit = result.get('transit_info')
places = result.get('retrieved_places')

# Check for violations or errors
if result.get('violations'):
    print("Quality issues detected:", result['violations'])

if result.get('error'):
    print("Errors encountered:", result['error'])

# View tool usage
print("Tools used:", result.get('tools_used'))
```

## 📊 Project Structure

```
travel_concierge/
├── src/
│   ├── agents.py           # Agent implementations
│   ├── graph.py            # LangGraph workflow definition
│   ├── state.py            # State management and schemas
│   ├── fallbacks.py        # Retry and circuit breaker logic
│   ├── observability.py    # Tracing and monitoring
│   ├── constants.py        # Configuration constants
│   ├── guardrails/
│   │   ├── moderation.py   # Content moderation
│   │   ├── pii.py          # PII detection
│   │   └── schemas.py      # Validation schemas
│   └── tools/
│       ├── places.py       # Tourist attraction search
│       ├── weather.py      # Weather forecasting
│       ├── country.py      # Country information
│       ├── transit.py      # Public transit info
│       ├── currency.py     # Currency conversion
│       └── flight_tool.py  # Flight search
├── notebooks/
│   └── demo.ipynb          # Interactive demo
├── artifacts/
│   └── sample_trace.json   # Example trace output
├── README.md
├── requirements.txt
└── CHANGELOG.md

```

## 🔧 Configuration

### API Keys

The system requires:
- **Groq API Key**: For LLM operations (configured in `src/graph.py`)
- **LangSmith API Key** (Optional): For tracing and observability

### Model Configuration

Default model: `openai/gpt-oss-20b` via Groq

To change the model, update the `BaseAgent` class in `src/agents.py`:

```python
class BaseAgent:
    def __init__(self, model_name="llama-3.1-70b-8192", api_key=None):
        self.llm = ChatGroq(model=model_name, temperature=0.1, api_key=api_key)
```

## 📈 Observability

### Tracing

Enable tracing with LangSmith:

```python
from src.observability import setup_observability, export_trace

# Setup tracing
tracer = setup_observability()

# After execution
trace_data = export_trace("run_id")
```

### Metrics

Access execution metrics:

```python
from src.observability import get_metrics

metrics = get_metrics()
print(f"Total runs: {metrics['total_runs']}")
print(f"Success rate: {metrics['success_rate']}")
```

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🐛 Known Issues & Limitations

- **Rate Limits**: External APIs may have rate limits
- **API Availability**: Some fallback data is used when APIs are unavailable
- **Model Limitations**: LLM outputs may vary in quality
- **Geographic Coverage**: Best results for major tourist destinations

## 📝 Changelog

See [CHANGELOG.md](CHANGELOG.md) for a detailed history of changes and improvements.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with [LangGraph](https://langchain-ai.github.io/langgraph/)
- Powered by [Groq](https://groq.com/)
- Weather data from [Open-Meteo](https://open-meteo.com/)
- Place data from [OpenStreetMap Nominatim](https://nominatim.org/)
- Country data from [REST Countries](https://restcountries.com/)

## 📧 Contact

For questions, issues, or suggestions, please open an issue on GitHub.

---

**Built with ❤️ for intelligent travel planning**
