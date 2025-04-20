from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Header
from ..models.models import EmailRequest
from ..services.email_service import EmailService
from ..services.mongo_service import MongoService
from typing import Dict, Any

import os
from fastapi.security.api_key import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN


router = APIRouter(
    prefix="/email",
    tags=["email"],
    responses={404: {"description": "Not found"}}
)
# Configure OpenAI with API key from environment

# Set up API key authentication
API_KEY = os.getenv("INTERNAL_API_KEY")
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key_header: str = Depends(api_key_header)):
    if api_key_header == API_KEY:
        return api_key_header
    raise HTTPException(
        status_code=HTTP_403_FORBIDDEN, detail="Could not validate API key"
    )

async def get_email_service():
    return EmailService()

@router.post("/send", response_model=Dict[str, str])
async def send_email(
    email_request: EmailRequest,
    background_tasks: BackgroundTasks,
    email_service: EmailService = Depends(get_email_service)
):
    """
    Send an email using a template.
    
    The email will be sent in the background to avoid blocking the API response.
    """
    # Add the email sending task to background tasks
    background_tasks.add_task(
        email_service.send_email,
        recipient=email_request.recipient,
        subject=email_request.subject,
        template_name=email_request.template_name,
        template_data=email_request.template_data
    )
    
    return {"message": f"Email to {email_request.recipient} has been queued"}


@router.post("/marketing_email", response_model=Dict[str, str])
async def generate_marketing_email(
    user_context: Dict[str, Any],
    api_key: str = Depends(get_api_key)
):

    mongo_service = MongoService()
    system_metrics_doc = await mongo_service.db.system_metrics.find_one()
    #print(f"System metrics: {system_metrics_doc}")

    if system_metrics_doc and "marketing_email_gen_prompt" in system_metrics_doc:
        marketing_email_gen_prompt = system_metrics_doc["marketing_email_gen_prompt"]
    else:
        return {"message": "No marketing email gen prompt found"}   

    marketing_collection = mongo_service.db.marketing
    docs = []
    #find one for test
    doc = await marketing_collection.find()
    async for document in doc:
        docs.append(document)
    print(f"Marketing contact: {docs}")
    print("\n---------------------------------\n")
    email = await generate_email_from_llm(docs, marketing_email_gen_prompt)
    print(email)
    print("\n---------------------------------\n")

    async for doc in marketing_collection.find({"active": True}).limit(1).batch_size(1):
        print(f"Marketing contact: {doc}")
        print("\n---------------------------------\n")
        email = await generate_email_from_llm(doc, marketing_email_gen_prompt)
        print(email)
        print("\n---------------------------------\n")

    return {"message": "Email generated successfully"}
    
    # print(f"Number of marketing contacts: {len(docs)}")
    # #add test email, first name, last name, previous emails, engagement, available assets to the dict to test it 
    # user_context["email"] = "havilal@jediteck.com"
    # user_context["first_name"] = "Havilal"
    # user_context["last_name"] = "Gunasekar"
    # user_context["previous_emails"] = []
    # user_context["engagement"] = {"opened_last_email": False, "clicked": False, "trial_status": "trial"}
    # user_context["available_assets"] = [
    #     {"type": "image", "title": "Image 1", "url": "https://example.com/image1.jpg"}, 
    #     {"type": "video", "title": "Video 1", "url": "https://example.com/video1.mp4"}
    # ]
    
    
