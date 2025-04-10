from fastapi import APIRouter, HTTPException, Request, Depends, Header
from typing import Dict, Any, Optional
from ..services.mongo_service import MongoService
from ..models.models import EventModel
from datetime import datetime
import json
import logging
from hubspot import HubSpot
from hubspot.crm.contacts import ApiException
import os
from ..services.email_service import EmailService
from ..config import settings

access_token = os.getenv("HUBSPOT_TOKEN")
client = HubSpot(access_token=access_token)
email_service = EmailService()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hubspot_webhook")

async def send_welcome_email(email, first_name=None, company_name=None):
    """
    Send a welcome email to a new contact.
    """
    try:
        # Prepare template data with more parameters
        print(f"Sending welcome email to {email} with first_name: {first_name}, company_name: {company_name}")
        
        current_time = datetime.now()
        
        template_data = {
            "email": email,
            "name": (first_name or "").capitalize(),  # Default to "there" if first_name is None
            "company": company_name or "",  # Empty string if company_name is None
            "app_name": settings.APP_NAME,
            "contact_email": settings.SMTP_FROM,
            "company_name": "JediTeck",
            "support_email": "support@jediteck.com",
            "website_url": "https://jediteck.com",
            "current_year": "2025"
        }
        
        # Send welcome email using welcome_email template
        success = await email_service.send_email(
            recipient=email,
            cc=settings.SMTP_CC,
            subject=f"Welcome to {settings.APP_NAME}",
            template_name="welcome_email",  # Changed from welcome to welcome_email
            template_data=template_data
        )
        
        if success:
            logger.info(f"Welcome email sent to {email}")
            return {
                "success": True, 
                "subject": f"Welcome to {settings.APP_NAME}", 
                "message": f"Welcome email sent to {email}", 
                "sentAt": current_time.isoformat(), 
                "messageType": "welcome", 
                "status": "sent", 
                "sentSuccessfully": True
            }
        else:
            logger.error(f"Failed to send welcome email to {email}")
            return {"success": False, "message": "Failed to send welcome email"}
    except Exception as e:
        logger.error(f"Error sending welcome email to {email}: {str(e)}")
        return {"success": False, "message": f"Error sending welcome email: {str(e)}"}

def get_contact_details(object_id):
    """
    Retrieve contact details from HubSpot using the contact ID.
    
    Args:
        object_id: The HubSpot contact ID
        
    Returns:
        Contact properties dictionary or None if an error occurs
    """
    try:
        response = client.crm.contacts.basic_api.get_by_id(
            contact_id=object_id,
            properties=["email", "firstname", "lastname", "company"]
        )
        return response.properties
    except ApiException as e:
        logger.error(f"Error fetching contact {object_id}: {e}")
        return None

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
        
        # Handle case where HubSpot sends an array with a single object
        if isinstance(payload, list) and len(payload) > 0:
            payload = payload[0]  # Extract the first item from the array
        
        # TODO: In production, validate the HubSpot signature
        # if x_hubspot_signature:
        #     # Implement signature validation logic here
        #     pass
        
        # Process contact creation events
        if payload.get("subscriptionType") == "contact.creation" and payload.get("objectId"):
            # Get contact details from HubSpot
            contact_id = payload.get("objectId")
            contact_details = get_contact_details(contact_id)
            
            if contact_details and "email" in contact_details:
                # Store contact in marketing_contacts collection
                # Maintain the existing document structure
                contact_data = {
                    "email": contact_details.get("email", ""),
                    "name": f"{contact_details.get('firstname', '')} {contact_details.get('lastname', '')}".strip(),
                    "company": contact_details.get("company", ""),
                    "source": payload.get("changeSource", ""),
                    "createdAt": datetime.now(),
                    "timestamp": datetime.now().isoformat(),
                    "hubspot_id": contact_id,
                    "hubspot_data": payload
                }
                
                # Store in marketing contacts collection
                await mongo_service.create_or_update_marketing_contact(
                    email=contact_details["email"],
                    contact_data=contact_data
                )
                
                logger.info(f"Stored contact {contact_id} in marketing_contacts collection")
        
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
        
        # Send welcome email
        success = await send_welcome_email(contact_details["email"], contact_details.get("firstname"), contact_details.get("company"))
        # {"success": True , "subject": f"Welcome to {settings.APP_NAME}", "message": f"Welcome email sent to {contact_details['email']}", "sentAt": current_time.isoformat(), "messageType": "welcome", "status": "sent", "sentSuccessfully": True}
    
        if "communications" not in contact_data:
            contact_data["communications"] = []
        if success["success"]:
            # Add the welcome email to communications
            contact_data["communications"].append({
                "type": "email",
                "subject": success["subject"],
                "content": success["message"],
                "sentAt": success["sentAt"],
                "messageType": "welcome",
                "status": "sent",
                "sentSuccessfully": True
            })

            # Update the timestamp
            contact_data["lastCommunication"] = success["sentAt"]

            await mongo_service.create_or_update_marketing_contact(
                email=contact_details["email"],
                contact_data=contact_data
            )

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
