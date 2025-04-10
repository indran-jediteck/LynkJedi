from motor.motor_asyncio import AsyncIOMotorClient
from ..config import settings
from ..models.models import EventModel, CronJobModel
from bson import ObjectId
from typing import List, Optional, Dict, Any

class MongoService:
    def __init__(self):
        self.client = AsyncIOMotorClient(settings.MONGO_URI)
        self.db = self.client[settings.MONGO_DB]
        self.events_collection = self.db.events
        self.cron_collection = self.db.cron_jobs

    # Event operations
    async def get_all_events(self, limit: int = 100, skip: int = 0) -> List[EventModel]:
        events = []
        cursor = self.events_collection.find().skip(skip).limit(limit)
        async for document in cursor:
            events.append(EventModel(**document))
        return events

    async def get_event(self, event_id: str) -> Optional[EventModel]:
        event = await self.events_collection.find_one({"_id": ObjectId(event_id)})
        if event:
            return EventModel(**event)
        return None

    async def create_event(self, event: EventModel) -> EventModel:
        event_dict = event.dict(by_alias=True, exclude={"id"})
        if event.id is None:
            event_dict.pop("_id", None)
        result = await self.events_collection.insert_one(event_dict)
        event_dict["_id"] = result.inserted_id
        return EventModel(**event_dict)

    async def update_event(self, event_id: str, event_data: Dict[str, Any]) -> Optional[EventModel]:
        event = await self.events_collection.find_one({"_id": ObjectId(event_id)})
        if not event:
            return None
            
        await self.events_collection.update_one(
            {"_id": ObjectId(event_id)}, {"$set": event_data}
        )
        
        updated_event = await self.events_collection.find_one({"_id": ObjectId(event_id)})
        return EventModel(**updated_event)

    async def delete_event(self, event_id: str) -> bool:
        result = await self.events_collection.delete_one({"_id": ObjectId(event_id)})
        return result.deleted_count > 0

    # Cron job operations
    async def get_all_cron_jobs(self, limit: int = 100, skip: int = 0) -> List[CronJobModel]:
        jobs = []
        cursor = self.cron_collection.find().skip(skip).limit(limit)
        async for document in cursor:
            jobs.append(CronJobModel(**document))
        return jobs

    async def get_cron_job(self, job_id: str) -> Optional[CronJobModel]:
        job = await self.cron_collection.find_one({"_id": ObjectId(job_id)})
        if job:
            return CronJobModel(**job)
        return None

    async def create_cron_job(self, job: CronJobModel) -> CronJobModel:
        job_dict = job.dict(by_alias=True, exclude={"id"})
        if job.id is None:
            job_dict.pop("_id", None)
        result = await self.cron_collection.insert_one(job_dict)
        job_dict["_id"] = result.inserted_id
        return CronJobModel(**job_dict)

    async def update_cron_job(self, job_id: str, job_data: Dict[str, Any]) -> Optional[CronJobModel]:
        job = await self.cron_collection.find_one({"_id": ObjectId(job_id)})
        if not job:
            return None
            
        await self.cron_collection.update_one(
            {"_id": ObjectId(job_id)}, {"$set": job_data}
        )
        
        updated_job = await self.cron_collection.find_one({"_id": ObjectId(job_id)})
        return CronJobModel(**updated_job)

    async def delete_cron_job(self, job_id: str) -> bool:
        result = await self.cron_collection.delete_one({"_id": ObjectId(job_id)})
        return result.deleted_count > 0
