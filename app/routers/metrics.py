from fastapi import APIRouter, HTTPException, Depends, Header
from ..services.mongo_service import MongoService
from typing import Dict, Optional
import os
from starlette.status import HTTP_403_FORBIDDEN

router = APIRouter(
    prefix="/api/v1/metrics",
    tags=["metrics"],
    responses={
        404: {"description": "Not found"},
        403: {"description": "Invalid API key"}
    }
)

async def get_mongo_service():
    return MongoService()

async def verify_api_key(x_api_key: Optional[str] = Header(None, alias="X-API-Key")):
    """
    Verify that the API key in the header matches the internal API key.
    """
    internal_key = os.getenv("INTERNAL_API_KEY")
    if not x_api_key or x_api_key != internal_key:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Invalid API key"
        )
    return x_api_key

@router.post("/increment-agent-count", response_model=Dict[str, int])
async def increment_agent_count(
    mongo_service: MongoService = Depends(get_mongo_service),
    api_key: str = Depends(verify_api_key)
):
    """
    Increment the agent_count field in the system_metrics collection.
    Creates the field if it doesn't exist.
    Requires a valid API key in the X-API-Key header.
    """
    try:
        # Update the document and return the new value
        result = await mongo_service.db.system_metrics.find_one_and_update(
            {},  # empty filter to match the first document
            {"$inc": {"agent_count": 1}},  # increment by 1
            upsert=True,  # create if doesn't exist
            return_document=True  # return the updated document
        )
        
        if result:
            return {"agent_count": result.get("agent_count", 1)}
        else:
            raise HTTPException(status_code=500, detail="Failed to update agent count")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating agent count: {str(e)}")
