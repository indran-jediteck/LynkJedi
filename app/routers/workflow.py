# app/routers/workflow.py
from fastapi import APIRouter
from pydantic import BaseModel
from app.services.workflow_engine import load_workflow
from app.services.email_service import EmailService

router = APIRouter()

class EmailWorkflowInput(BaseModel):
    name: str
    email: str
    premium: bool

@router.post("/workflow/email")
async def run_email_workflow(payload: EmailWorkflowInput):
    wf = load_workflow("app/workflows/email_logic.bpmn", {"customer": payload.dict()})

    while True:
        tasks = wf.get_ready_tasks()
        if not tasks:
            break

        for task in tasks:
            if task.task_spec.name == "Send Premium Email":
                await EmailService().send_email(payload.email, "email/welcome_email.html", {"name": payload.name, "premium": True})
            elif task.task_spec.name == "Send Basic Email":
                await EmailService().send_email(payload.email, "email/welcome_email.html", {"name": payload.name, "premium": False})
            wf.complete_task_from_id(task.id)

    return {"message": f"Workflow completed for {payload.email}"}
