from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import asyncio
import uvicorn
from contextlib import asynccontextmanager
import redis.asyncio as redis
import asyncpg
from datetime import datetime
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import our custom modules
from llm_services.restaurant_agent import RestaurantAIAgent
from llm_services.intent_classifier import RestaurantIntentClassifier
from llm_services.response_generator import RestaurantResponseGenerator

# Models
class MessageRequest(BaseModel):
    message: str
    context: Dict[str, Any]
    restaurant_id: str
    customer_id: Optional[str] = None
    channel: str = "web"

class AnalyzeRequest(BaseModel):
    text: str
    type: str  # sentiment, intent, etc.
    metadata: Optional[Dict] = None

class ResponseRequest(BaseModel):
    template: str
    variables: Dict[str, Any]
    personalization: Optional[Dict] = None

# Lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.redis = await redis.from_url(os.environ['REDIS_URL'])
    app.state.db = await asyncpg.create_pool(os.environ['DATABASE_URL'])
    
    # Initialize AI components
    app.state.agents = {}
    app.state.classifier = RestaurantIntentClassifier()
    
    yield
    
    # Shutdown
    await app.state.redis.close()
    await app.state.db.close()

# Create FastAPI app
app = FastAPI(
    title="Restaurant AI Service",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/process")
async def process_message(request: MessageRequest):
    """Process incoming customer message"""
    
    # Get or create agent for restaurant
    if request.restaurant_id not in app.state.agents:
        # Load restaurant config from database
        async with app.state.db.acquire() as conn:
            restaurant = await conn.fetchrow(
                "SELECT * FROM restaurants WHERE id = $1",
                request.restaurant_id
            )
        
        if not restaurant:
            raise HTTPException(status_code=404, detail="Restaurant not found")
        
        app.state.agents[request.restaurant_id] = RestaurantAIAgent(
            dict(restaurant)
        )
    
    agent = app.state.agents[request.restaurant_id]
    
    # Check cache for similar queries
    cache_key = f"response:{request.restaurant_id}:{hash(request.message)}"
    cached = await app.state.redis.get(cache_key)
    
    if cached:
        return json.loads(cached)
    
    # Process with agent
    response = agent.agent.invoke({"input": request.message})
    
    # Cache response
    await app.state.redis.setex(
        cache_key,
        3600,  # 1 hour TTL
        json.dumps(response)
    )
    
    # Log conversation
    await log_conversation(
        app.state.db,
        request.restaurant_id,
        request.customer_id,
        request.message,
        response['output'],
        request.channel
    )
    
    return response

@app.post("/analyze-sentiment")
async def analyze_sentiment(request: AnalyzeRequest):
    """Analyze sentiment of text"""
    # Implementation here
    pass

@app.post("/generate-response")
async def generate_response(request: ResponseRequest):
    """Generate templated response"""
    # Implementation here
    pass

@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "redis": {"status": "unknown", "details": ""},
            "database": {"status": "unknown", "details": ""},
            "llm": {"status": "unknown", "details": ""}
        }
    }
    
    overall_healthy = True
    
    # Test Redis connection
    try:
        redis_start = datetime.utcnow()
        await app.state.redis.ping()
        redis_end = datetime.utcnow()
        response_time = (redis_end - redis_start).total_seconds() * 1000
        
        health_status["services"]["redis"] = {
            "status": "healthy",
            "details": f"Connected successfully",
            "response_time_ms": round(response_time, 2)
        }
    except Exception as e:
        overall_healthy = False
        health_status["services"]["redis"] = {
            "status": "unhealthy",
            "details": f"Connection failed: {str(e)}"
        }
    
    # Test Database connection
    try:
        db_start = datetime.utcnow()
        async with app.state.db.acquire() as conn:
            await conn.fetchval("SELECT 1")
        db_end = datetime.utcnow()
        response_time = (db_end - db_start).total_seconds() * 1000
        
        health_status["services"]["database"] = {
            "status": "healthy",
            "details": "Connected successfully",
            "response_time_ms": round(response_time, 2)
        }
    except Exception as e:
        overall_healthy = False
        health_status["services"]["database"] = {
            "status": "unhealthy",
            "details": f"Connection failed: {str(e)}"
        }
    
    # Test LLM connection
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        llm_start = datetime.utcnow()
        test_llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0
        )
        response = test_llm.predict("Hello")
        llm_end = datetime.utcnow()
        response_time = (llm_end - llm_start).total_seconds() * 1000
        
        health_status["services"]["llm"] = {
            "status": "healthy",
            "details": "API call successful",
            "response_time_ms": round(response_time, 2),
            "model": "gemini-2.5-flash"
        }
    except Exception as e:
        overall_healthy = False
        health_status["services"]["llm"] = {
            "status": "unhealthy",
            "details": f"API call failed: {str(e)}",
            "model": "gemini-2.5-flash"
        }
    
    # Set overall status
    health_status["status"] = "healthy" if overall_healthy else "unhealthy"
    
    return health_status

async def log_conversation(
    db_pool,
    restaurant_id: str,
    customer_id: str,
    message: str,
    response: str,
    channel: str
):
    """Log conversation to database"""
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO conversations 
            (restaurant_id, customer_id, channel, messages)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (restaurant_id, customer_id, channel)
            DO UPDATE SET 
                messages = conversations.messages || $4,
                updated_at = CURRENT_TIMESTAMP
        """, restaurant_id, customer_id, channel, json.dumps([
            {"role": "user", "content": message, "timestamp": datetime.utcnow().isoformat()},
            {"role": "assistant", "content": response, "timestamp": datetime.utcnow().isoformat()}
        ]))

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)