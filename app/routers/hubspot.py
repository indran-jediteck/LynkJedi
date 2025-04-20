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
from fastapi.security.api_key import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN
import requests

access_token = os.getenv("HUBSPOT_TOKEN")
client = HubSpot(access_token=access_token)
email_service = EmailService()

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

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hubspot_webhook")

async def send_welcome_email(email, first_name=None, company_name=None, mongo_service=None):
    """
    Send a welcome email to a new contact.
    """
    try:
        # Prepare template data with more parameters
        print(f"Sending welcome email to {email} with first_name: {first_name}, company_name: {company_name}")

        # add the email checker to check if the email is valid
        abstract_api_key = os.getenv("ABSTRACT_API_KEY")
        response = requests.get(f"https://emailvalidation.abstractapi.com/v1/?api_key={abstract_api_key}&email={email}")
        print(response.status_code)
        print(response.content)
        if response.status_code == 200:
            data = response.json()
            if data.get("is_valid_format"):
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
                # check of if the email already exist in marketing collection
                if mongo_service:
                    existing_contact = await mongo_service.marketing_collection.find_one({"email": email})
                    if existing_contact and existing_contact.get("source") == "newsletter":
                        logger.info(f"Contact {email} already exists in marketing collection as a newsletter signup")
                        template_name="welcome_email_newsletter"
                    else:   
                        if first_name :
                            template_name="welcome_email"
                        else:
                            template_name="welcome_email_noname"
                else:
                    # Default template if mongo_service is not available
                    template_name = "welcome_email" if first_name else "welcome_email_noname"

                print(f"Using template: {template_name}")
                # Send welcome email using  template
                success = await email_service.send_email(
                    recipient=email,
                    cc=settings.SMTP_CC,
                    subject=f"Welcome to {settings.APP_NAME}",
                    template_name=template_name,
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
                        "sentSuccessfully": True,
                        "template_name": template_name
                    }
                else:
                    logger.error(f"Failed to send welcome email to {email}")
                    return {"success": False, "message": "Failed to send welcome email"}
            else:
                logger.error(f"Invalid email: {email}")
                return {"success": False, "message": "Invalid email"}

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
        success = await send_welcome_email(
            email=contact_details["email"], 
            first_name=contact_details.get("firstname"), 
            company_name=contact_details.get("company"),
            mongo_service=mongo_service
        )
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

@router.get("/contacts", response_model=Dict[str, Any])
async def get_hubspot_contacts(
    mongo_service: MongoService = Depends(get_mongo_service),
    api_key: str = Depends(get_api_key)
):
    """
    Get all contacts from the marketing collection.
    
    This endpoint is protected with API key authentication.
    """
    try:
        # Initialize marketing collection if not already done
        if not hasattr(mongo_service, 'marketing_collection'):
            mongo_service.marketing_collection = mongo_service.db.marketing
            
        # Find all contacts in the marketing collection
        contacts = await mongo_service.marketing_collection.find().to_list(1000)
        
        # Convert ObjectId to string for JSON serialization
        for contact in contacts:
            contact["_id"] = str(contact["_id"])
        
        return {
            "status": "success",
            "count": len(contacts),
            "contacts": contacts
        }
    except Exception as e:
        logger.error(f"Error fetching contacts: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching contacts: {str(e)}"
        )

@router.post("/sync-contacts", response_model=Dict[str, Any])
async def sync_hubspot_contacts(
    mongo_service: MongoService = Depends(get_mongo_service),
    limit: Optional[int] = None,
    api_key: str = Depends(get_api_key)
):
    """
    Synchronize HubSpot contacts with the marketing collection.
    
    This endpoint fetches contacts from HubSpot and adds them to the marketing collection.
    It's designed for one-time synchronization of existing contacts.
    Only contacts that don't already exist in the marketing collection will be added.
    
    Args:
        limit: Maximum number of contacts to sync (default: None, which means all contacts)
    
    Returns:
        Summary of the synchronization process
    """
    try:
        # Initialize marketing collection if not already done
        if not hasattr(mongo_service, 'marketing_collection'):
            mongo_service.marketing_collection = mongo_service.db.marketing
            
        logger.info(f"Starting HubSpot contact synchronization (limit: {'all' if limit is None else limit})")
        
        # Initialize counters
        total_contacts = 0
        synced_contacts = 0
        skipped_contacts = 0
        already_exists = 0
        
        # Get all contacts from HubSpot with pagination
        after = None
        has_more = True
        
        while has_more and (limit is None or total_contacts < limit):
            # Fetch contacts from HubSpot
            contacts_page = client.crm.contacts.basic_api.get_page(
                limit=100,  # HubSpot API page size
                after=after,
                properties=["email", "firstname", "lastname", "company", "createdate"]
            )
            
            # Process each contact
            for contact in contacts_page.results:
                total_contacts += 1
                
                # Skip if we've reached the limit
                if limit is not None and total_contacts > limit:
                    break
                
                # Get contact properties
                properties = contact.properties
                
                # Skip contacts without email
                if "email" not in properties or not properties["email"]:
                    skipped_contacts += 1
                    continue
                
                # Check if contact already exists in marketing collection
                email = properties["email"]
                existing_contact = await mongo_service.marketing_collection.find_one({"email": email})
                
                if existing_contact:
                    already_exists += 1
                    logger.info(f"Contact with email {email} already exists in marketing collection, skipping")
                    continue
                
                # Create contact data structure
                contact_data = {
                    "email": email,
                    "name": f"{properties.get('firstname', '')} {properties.get('lastname', '')}".strip(),
                    "company": properties.get("company", ""),
                    "source": "hubspot_sync",
                    "createdAt": datetime.now(),
                    "timestamp": datetime.now().isoformat(),
                    "hubspot_id": contact.id,
                    "hubspot_data": {
                        "id": contact.id,
                        "properties": properties
                    },
                    "communications": []  # Initialize empty communications array
                }
                
                # Insert new contact directly (not update)
                result = await mongo_service.marketing_collection.insert_one(contact_data)
                
                synced_contacts += 1
                
                # Log progress every 10 contacts
                if synced_contacts % 10 == 0:
                    logger.info(f"Synced {synced_contacts} contacts so far...")
            
            # Check if there are more contacts to fetch
            has_more = contacts_page.paging is not None and contacts_page.paging.next is not None
            
            # Update the "after" cursor for the next page
            if has_more:
                after = contacts_page.paging.next.after
        
        # Log completion
        logger.info(f"HubSpot contact synchronization completed: {synced_contacts} synced, {skipped_contacts} skipped, {already_exists} already existed")
        
        # Return summary
        return {
            "status": "success",
            "total_processed": total_contacts,
            "synced": synced_contacts,
            "skipped": skipped_contacts,
            "already_exists": already_exists,
            "message": f"Successfully synchronized {synced_contacts} contacts from HubSpot ({already_exists} already existed)"
        }
        
    except Exception as e:
        logger.error(f"Error synchronizing HubSpot contacts: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error synchronizing contacts: {str(e)}"
        )
