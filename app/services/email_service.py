import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from ..config import settings
import os

class EmailService:
    def __init__(self):
        templates_dir = Path(__file__).parent.parent / "templates"
        self.env = Environment(loader=FileSystemLoader(templates_dir))
        
    async def send_email(self, recipient: str, cc: str, subject: str, template_name: str, template_data: dict) -> bool:
        """
        Send an email with both HTML and text versions using templates.
        
        Args:
            recipient: Email address of the recipient
            subject: Email subject
            template_name: Name of the template (without extension)
            template_data: Dictionary of data to be passed to the template
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            # Create message container
           
            print(f"Template data: {template_data}")
            msg = MIMEMultipart('alternative')
            msg['From'] = settings.SMTP_FROM
            msg['To'] = recipient
            msg['CC'] = cc
            msg['Subject'] = subject

            # Render text and HTML templates
            text_template = self.env.get_template(f"email/{template_name}.txt")
            html_template = self.env.get_template(f"email/{template_name}.html")
            
            text_content = text_template.render(**template_data)
            html_content = html_template.render(**template_data)
            
            # Attach parts to message
            part1 = MIMEText(text_content, 'plain')
            part2 = MIMEText(html_content, 'html')
            msg.attach(part1)
            msg.attach(part2)
            
            # Send email
            await aiosmtplib.send(
                msg,
                hostname=settings.SMTP_SERVER,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USERNAME,
                password=settings.SMTP_PASSWORD,
                start_tls=True,
                use_tls=False
            )
            
            return True
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return False
