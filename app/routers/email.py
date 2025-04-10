from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from ..models.models import EmailRequest
from ..services.email_service import EmailService
from typing import Dict

router = APIRouter(
    prefix="/email",
    tags=["email"],
    responses={404: {"description": "Not found"}}
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
