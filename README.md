# Travel Concierge Multi-Agent System

A production-style multi-agent workflow using LangGraph that plans travel itineraries with multiple agents, security guardrails, fallbacks, and observability.

## Features

- **Multi-Agent Collaboration**: Four specialized agents for user input processing, research, planning, and writing
- **Security Guardrails**: Prompt hardening, schema validation, content moderation, and PII detection
- **Fallbacks & Timeouts**: Retry mechanisms, circuit breakers, and fallback implementations
- **Tracing & Observability**: LangSmith integration for comprehensive tracing and metrics
- **MCP Integration**: Optional Model Context Protocol integration for enhanced tooling

## Architecture

The system consists of:

1. **UserInputAgent**: Extracts travel information from user queries
2. **ResearchAgent**: Gathers information about destinations, places, and weather
3. **PlannerAgent**: Creates day-by-day itineraries based on researched information
4. **WriterAgent**: Generates the final structured output
5. **ReviewerAgent**: Validates itineraries for quality and safety

## Guardrails Implemented

1. **Prompt Hardening**: System prompts explicitly forbid misuse and include safety reminders
2. **Schema Validation**: All outputs validate against Pydantic schemas with violation tracking
3. **Content Moderation**: Lightweight post-generation checks for safety and policy compliance
4. **PII Detection**: Identifies and redacts personally identifiable information

## Fallbacks & Circuit Breakers

- **Per-Tool Retries**: Exponential backoff for failed tool calls
- **Fallback Implementations**: Stubbed responses when external services fail
- **Circuit Breaker**: Prevents cascading failures after multiple consecutive errors
- **Conditional Routing**: Routes to reviewer or human intervention based on validation results

## Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and add your API keys
3. Run the demo: `python -m notebooks.demo`

## Usage

```python
from src.graph import TravelGraph

travel_graph = TravelGraph()
result = travel_graph.invoke("Plan a 5-day trip to Tokyo for 3 people")
print(result.final_output)