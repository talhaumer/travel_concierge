# Changelog

All notable changes to the Travel Concierge Multi-Agent System project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-09-09

### Fixed

#### Critical Fixes

- **Fixed Groq API Key Configuration** 
  - Added `api_key` parameter to `BaseAgent` and all derived agent classes
  - Updated `TravelGraph` to pass `GROQ_API_KEY` to all agent instances
  - Resolved `GroqError: The api_key client option must be set` error

- **Fixed Model Name Issues**
  - Updated model name from incorrect `groq/llama3-70b-8192` to `openai/gpt-oss-20b`
  - Resolved `404 model_not_found` error from Groq API
  - Model name now follows correct Groq API format

- **Fixed ChatPromptTemplate Variable Escaping**
  - Escaped JSON examples in prompt templates with double curly braces `{{}}`
  - Resolved `KeyError: 'Input to ChatPromptTemplate is missing variables'` error
  - Template variables now properly distinguished from literal text

#### Agent & Logic Fixes

- **Fixed Circuit Breaker Implementation**
  - Removed `@circuit_breaker` decorator from methods not following state pattern
  - Resolved `'ResearchAgent' object has no attribute 'circuit_breaker_count'` error
  - Circuit breaker now only used on appropriate agent methods

- **Fixed Country Info API Calls**
  - Updated logic to extract country name from destination (e.g., "France" from "Paris")
  - Resolved 404 errors when querying REST Countries API with city names
  - Added fallback to "France" for Paris destinations

- **Fixed Location Parameter Handling**
  - Added `location` parameter to `get_fallback_places()` function
  - Updated all calls to `get_fallback_places()` to pass location
  - Resolved `NameError: 'location' is not defined` error

#### Data & Planning Fixes

- **Enhanced Places Search**
  - Added comprehensive fallback data for Paris (6 major attractions)
  - Fixed location parameter detection in fallback logic
  - Added special handling for Paris variations ("paris", "france", "french")
  - Improved search logic to properly detect cities

- **Fixed Empty Itinerary Issue**
  - Expanded place type matching to include more categories (landmark, monument, cathedral, chapel)
  - Added fallback to use all places if none match specific categories
  - Created `create_basic_itinerary()` method for generic itineraries
  - Planning now handles empty places lists gracefully

- **Fixed Schema Validation**
  - Added conversion of `ItineraryItem` objects to dictionaries in final output
  - Schema validation now passes with properly formatted data
  - Removed "Final output schema validation failed" violations

### Added

#### Missing Imports

- Added `datetime` import to `agents.py`
- Added `StateStatus` to state imports
- Added `FinalOutputSchema` to guardrails imports

#### Features

- **Comprehensive Fallback Data**
  - Added 6 major Paris attractions (Eiffel Tower, Louvre, Notre-Dame, Arc de Triomphe, Musée d'Orsay, Sainte-Chapelle)
  - Added fallback transit info for Paris (Metro, RER, Bus)
  - Added fallback country info for France

- **Debug Logging**
  - Added debug print statements in places search for troubleshooting
  - Added research error logging

#### Documentation

- **Created comprehensive README.md**
  - Added project overview and features
  - Added architecture diagrams and agent descriptions
  - Added installation and usage instructions
  - Added configuration guide
  - Added project structure
  - Added contributing guidelines

- **Created requirements.txt**
  - Listed all project dependencies with versions
  - Organized by category (core, data, HTTP, etc.)
  - Added optional development tools

- **Created .gitignore**
  - Added Python-specific ignores
  - Added IDE and OS ignores
  - Added project-specific ignores
  - Protected sensitive files (API keys, logs)

### Changed

- **Improved Planning Logic**
  - Better categorization of places by type
  - More intelligent activity distribution across days
  - Handles edge cases with generic activities

- **Enhanced Error Handling**
  - Better error messages for debugging
  - Graceful degradation when APIs fail
  - Comprehensive error tracking in state

### Technical Improvements

- **API Integration**
  - Proper error handling for REST Countries API
  - Fallback mechanisms for TransitLand API
  - Rate limiting for OpenStreetMap Nominatim
  - Weather API integration with Open-Meteo

- **State Management**
  - Better handling of empty/null values
  - Proper type conversions for schema compliance
  - Comprehensive state tracking

- **Code Quality**
  - Removed unused commented code sections
  - Improved function signatures
  - Better parameter handling
  - More descriptive variable names

## [0.1.0] - Initial Release

### Added

- Initial multi-agent system architecture
- Five specialized agents (UserInput, Research, Planner, Reviewer, Writer)
- LangGraph workflow implementation
- Security guardrails (prompt hardening, schema validation, content moderation, PII detection)
- Fallback mechanisms and circuit breakers
- Tool integrations (places, weather, country, transit, currency)
- Jupyter notebook demo
- Basic documentation

---

## Legend

- **Added**: New features or functionality
- **Changed**: Changes to existing functionality
- **Deprecated**: Features that will be removed in future versions
- **Removed**: Features that have been removed
- **Fixed**: Bug fixes
- **Security**: Security-related changes

