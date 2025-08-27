# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
This is a Restaurant AI Service that provides intelligent customer service automation for restaurants using LangChain with Google Gemini and FastAPI. The system handles reservations, orders, menu inquiries, and review responses through various messaging channels.

## Architecture
- **FastAPI application** (`main.py`) - Main API server with endpoints for message processing
- **LLM Services** (`llm_services/`) - Core AI components:
  - `restaurant_agent.py` - Main conversational agent with restaurant-specific tools
  - `intent_classifier.py` - Classifies customer messages into intents
  - `response_generator.py` - Generates contextual responses with templates
- **Database schema** (`knowledge/db.md`) - PostgreSQL schema for restaurants, customers, conversations, reservations, orders, reviews, and analytics
- **N8N workflows** (`n8n_workflow/`) - Pre-built automation workflows for different restaurant operations

## Key Technologies
- **LangChain** - AI agent framework with Google Gemini
- **Google Gemini** - AI models (gemini-2.5-flash for all components)
- **FastAPI** - API framework with async support
- **PostgreSQL** - Primary database with UUID primary keys
- **Redis** - Caching layer for responses
- **AsyncPG** - Async PostgreSQL driver

## Development Commands

### Environment Setup
```bash
pip install -r requirements.txt
```

### Running the Application
```bash
# Development server
python main.py
# Or with uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Required Environment Variables
- `REDIS_URL` - Redis connection string
- `DATABASE_URL` - PostgreSQL connection string  
- `GOOGLE_API_KEY` - Google Gemini API key

## Database Setup
The database schema is defined in `knowledge/db.md`. Key tables:
- `restaurants` - Restaurant configurations and settings
- `customers` - Customer profiles with preferences and history
- `conversations` - Message logs with JSONB message arrays
- `reservations` - Table bookings with status tracking
- `orders` - Order processing with items as JSONB
- `reviews` - Multi-platform review management

## Agent System
The `RestaurantAIAgent` uses LangChain's function calling with these tools:
- `check_availability` - Table availability checking
- `make_reservation` - Reservation creation
- `get_menu_info` - Menu item queries
- `process_order` - Order handling
- `check_hours` - Hours inquiry
- `get_wait_time` - Wait time estimates

## API Endpoints
- `POST /process` - Main message processing endpoint
- `POST /analyze-sentiment` - Text sentiment analysis (placeholder)
- `POST /generate-response` - Template-based response generation (placeholder)
- `GET /health` - Health check

## Response Caching
Responses are cached in Redis with 1-hour TTL using message hash as cache key.

## Testing
No specific test framework is currently configured. When adding tests, determine the appropriate testing approach for this FastAPI + LangChain application.