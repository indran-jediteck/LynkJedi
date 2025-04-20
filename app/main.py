from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import events, cron, email, hubspot
from .config import settings
import uvicorn
import os

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="A simple FastAPI backend application that handles MongoDB CRUD operations and email functionality",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(events.router)
app.include_router(cron.router)
app.include_router(email.router)
app.include_router(hubspot.router)

@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": "0.1.0",
        "endpoints": {
            "events": "/events",
            "cron": "/cron",
            "email": "/email",
            "hubspot": "/hubspot"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
