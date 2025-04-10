# LynkJedi

A simple FastAPI backend application that handles MongoDB CRUD operations and email functionality with HTML and text templates. The application is designed to respond to events and perform scheduled tasks via cron jobs.

## Features

- FastAPI backend with router structure
- MongoDB integration for data storage and retrieval
- Email service with HTML and text template support
- Event handling system
- Cron job support for scheduled tasks

## Project Structure

```
LynkJedi/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── events.py
│   │   ├── cron.py
│   │   └── email.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── models.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── mongo_service.py
│   │   └── email_service.py
│   └── templates/
│       ├── email/
│       │   ├── notification.html
│       │   └── notification.txt
├── requirements.txt
└── README.md
```

## Setup

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment: 
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Create a `.env` file with your configuration (see `.env.example`)
6. Run the application: `uvicorn app.main:app --reload`

## API Endpoints

- `/events` - CRUD operations for events
- `/cron` - Endpoints for scheduled tasks
- `/email` - Email sending functionality

## Environment Variables

Create a `.env` file with the following variables:

```
MONGO_URI=mongodb://localhost:27017
MONGO_DB=lynkjedi_db
SMTP_SERVER=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=your_username
SMTP_PASSWORD=your_password
EMAIL_FROM=noreply@example.com
```
