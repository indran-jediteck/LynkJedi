from fastapi import APIRouter, HTTPException, Depends
from ..models.models import CronJobModel
from ..services.mongo_service import MongoService
from typing import List, Dict, Any
from bson import ObjectId
from datetime import datetime

router = APIRouter(
    prefix="/cron",
    tags=["cron"],
    responses={404: {"description": "Not found"}}
)

async def get_mongo_service():
    return MongoService()

@router.get("/", response_model=List[CronJobModel])
async def get_cron_jobs(
    skip: int = 0, 
    limit: int = 100,
    mongo_service: MongoService = Depends(get_mongo_service)
):
    """
    Get all cron jobs with pagination.
    """
    return await mongo_service.get_all_cron_jobs(limit=limit, skip=skip)

@router.get("/{job_id}", response_model=CronJobModel)
async def get_cron_job(
    job_id: str,
    mongo_service: MongoService = Depends(get_mongo_service)
):
    """
    Get a specific cron job by ID.
    """
    if not ObjectId.is_valid(job_id):
        raise HTTPException(status_code=400, detail="Invalid job ID format")
        
    job = await mongo_service.get_cron_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Cron job not found")
    return job

@router.post("/", response_model=CronJobModel)
async def create_cron_job(
    job: CronJobModel,
    mongo_service: MongoService = Depends(get_mongo_service)
):
    """
    Create a new cron job.
    """
    return await mongo_service.create_cron_job(job)

@router.put("/{job_id}", response_model=CronJobModel)
async def update_cron_job(
    job_id: str,
    job_data: Dict[str, Any],
    mongo_service: MongoService = Depends(get_mongo_service)
):
    """
    Update an existing cron job.
    """
    if not ObjectId.is_valid(job_id):
        raise HTTPException(status_code=400, detail="Invalid job ID format")
        
    updated_job = await mongo_service.update_cron_job(job_id, job_data)
    if not updated_job:
        raise HTTPException(status_code=404, detail="Cron job not found")
    return updated_job

@router.delete("/{job_id}", response_model=dict)
async def delete_cron_job(
    job_id: str,
    mongo_service: MongoService = Depends(get_mongo_service)
):
    """
    Delete a cron job.
    """
    if not ObjectId.is_valid(job_id):
        raise HTTPException(status_code=400, detail="Invalid job ID format")
        
    success = await mongo_service.delete_cron_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Cron job not found")
    return {"message": "Cron job deleted successfully"}

@router.post("/{job_id}/execute", response_model=dict)
async def execute_cron_job(
    job_id: str,
    mongo_service: MongoService = Depends(get_mongo_service)
):
    """
    Manually execute a cron job.
    """
    if not ObjectId.is_valid(job_id):
        raise HTTPException(status_code=400, detail="Invalid job ID format")
        
    job = await mongo_service.get_cron_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Cron job not found")
    
    # Update last_run timestamp
    await mongo_service.update_cron_job(job_id, {"last_run": datetime.now()})
    
    # In a real application, you would execute the job logic here
    # For now, we'll just return a success message
    return {"message": f"Cron job '{job.name}' executed successfully"}
