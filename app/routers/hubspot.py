from fastapi import APIRouter, HTTPException, Request, Depends, Header
from typing import Dict, Any, Optional
from ..services.mongo_service import MongoService
from ..models.models import EventModel
from datetime import datetime
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hubspot_webhook")

router = APIRouter(
    prefix="/hubspot",
    tags=["hubspot"],
    responses={404: {"description": "Not found"}}
)

async def get_mongo_service():
    return MongoService()

@router.post("/webhook", response_model=Dict[str, str])
async def hubspot_webhook(
    request: Request,
    mongo_service: MongoService = Depends(get_mongo_service),
    x_hubspot_signature: Optional[str] = Header(None)
):
    """
    Webhook endpoint for HubSpot events.
    
    This endpoint receives webhook notifications from HubSpot when events occur
    in your HubSpot account. The events are stored in the database for processing.
    
    In a production environment, you should validate the x-hubspot-signature header
    to ensure the request is coming from HubSpot.
    """
    try:
        # Get the raw payload
        payload = await request.json()
        logger.info(f"Received HubSpot webhook: {json.dumps(payload, indent=2)}")
        
        # TODO: In production, validate the HubSpot signature
        # if x_hubspot_signature:
        #     # Implement signature validation logic here
        #     pass
        
        # Create an event for each webhook notification
        event = EventModel(
            name="hubspot_webhook",
            description="HubSpot webhook notification",
            data=payload,
            processed=False,
            timestamp=datetime.now()
        )
        
        # Store the event in MongoDB
        stored_event = await mongo_service.create_event(event)
        
        return {
            "status": "success",
            "message": "Webhook received and processed",
            "event_id": str(stored_event.id)
        }
        
    except Exception as e:
        logger.error(f"Error processing HubSpot webhook: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing webhook: {str(e)}"
        )
