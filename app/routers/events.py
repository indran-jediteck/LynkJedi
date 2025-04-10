from fastapi import APIRouter, HTTPException, Depends
from ..models.models import EventModel
from ..services.mongo_service import MongoService
from typing import List, Dict, Any
from bson import ObjectId

router = APIRouter(
    prefix="/events",
    tags=["events"],
    responses={404: {"description": "Not found"}}
)

async def get_mongo_service():
    return MongoService()

@router.get("/", response_model=List[EventModel])
async def get_events(
    skip: int = 0, 
    limit: int = 100,
    mongo_service: MongoService = Depends(get_mongo_service)
):
    """
    Get all events with pagination.
    """
    return await mongo_service.get_all_events(limit=limit, skip=skip)

@router.get("/{event_id}", response_model=EventModel)
async def get_event(
    event_id: str,
    mongo_service: MongoService = Depends(get_mongo_service)
):
    """
    Get a specific event by ID.
    """
    if not ObjectId.is_valid(event_id):
        raise HTTPException(status_code=400, detail="Invalid event ID format")
        
    event = await mongo_service.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@router.post("/", response_model=EventModel)
async def create_event(
    event: EventModel,
    mongo_service: MongoService = Depends(get_mongo_service)
):
    """
    Create a new event.
    """
    return await mongo_service.create_event(event)

@router.put("/{event_id}", response_model=EventModel)
async def update_event(
    event_id: str,
    event_data: Dict[str, Any],
    mongo_service: MongoService = Depends(get_mongo_service)
):
    """
    Update an existing event.
    """
    if not ObjectId.is_valid(event_id):
        raise HTTPException(status_code=400, detail="Invalid event ID format")
        
    updated_event = await mongo_service.update_event(event_id, event_data)
    if not updated_event:
        raise HTTPException(status_code=404, detail="Event not found")
    return updated_event

@router.delete("/{event_id}", response_model=dict)
async def delete_event(
    event_id: str,
    mongo_service: MongoService = Depends(get_mongo_service)
):
    """
    Delete an event.
    """
    if not ObjectId.is_valid(event_id):
        raise HTTPException(status_code=400, detail="Invalid event ID format")
        
    success = await mongo_service.delete_event(event_id)
    if not success:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"message": "Event deleted successfully"}
