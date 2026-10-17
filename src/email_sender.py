"""Email sender for Daily Brief epub delivery to Kindle."""

import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from email import encoders
from pathlib import Path
from typing import Optional


class EmailSender:
    """Sends epub via email to Kindle."""

    def __init__(self, config: dict):
        self.sender_email = config.sender_email
        self.sender_password = self._load_password()
        self.smtp_server = config.smtp_server
        self.smtp_port = config.smtp_port
        self.kindle_email = config.kindle_email

    def _load_password(self) -> str:
        """Load the app password from .env file."""
        import os
        env_path = Path(__file__).parent.parent / ".env"
        password = os.environ.get("GMAIL_APP_PASSWORD", "")
        if not password and env_path.exists():
            with open(env_path) as f:
                for line in f:
                    if line.startswith("GMAIL_APP_PASSWORD="):
                        password = line.split("=", 1)[1].strip()
                        break
        return password

    def send(self, epub_path: str, recipient: Optional[str] = None) -> bool:
        """Send the epub file to Kindle via email."""
        to_email = recipient or self.kindle_email
        if not to_email:
            raise ValueError("No recipient email specified")
        if not self.sender_email or not self.sender_password:
            raise ValueError("Gmail credentials not configured")

        # Create message
        msg = MIMEMultipart()
        msg["From"] = self.sender_email
        msg["To"] = to_email
        msg["Subject"] = "Daily Brief — " + datetime.now().strftime("%Y-%m-%d")

        # Add text body
        body = "Your Daily Brief has arrived. Attach this .epub to your Kindle device or app."
        msg.attach(MIMEText(body, "plain"))

        # Attach epub file
        epub_file = Path(epub_path)
        if not epub_file.exists():
            raise FileNotFoundError(f"Epub file not found: {epub_path}")

        with open(epub_file, "rb") as f:
            part = MIMEApplication(f.read(), Name=epub_file.name)
        part["Content-Disposition"] = f'attachment; filename="{epub_file.name}"'
        msg.attach(part)

        # Send email
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(self.sender_email, self.sender_password)
            server.sendmail(self.sender_email, [to_email], msg.as_string())
            server.quit()
            return True
        except Exception as e:
            raise ConnectionError(f"Failed to send email: {e}")
