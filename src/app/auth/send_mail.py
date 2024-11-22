import os
from dotenv import load_dotenv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

load_dotenv()


def render_confirmation_email(confirmation_link: str) -> str:
    templates_dir = Path(__file__).parent
    env = Environment(loader=FileSystemLoader(templates_dir))
    template = env.get_template("confirmation_email.html")
    return template.render(confirmation_link=confirmation_link)


def send_email(token, address):
    sender = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD")

    server = smtplib.SMTP("74.125.143.108", 587)
    server.ehlo()
    server.starttls()
    confirmation_link = f"http://localhost:8000/confirm/{token}"
    html_content = render_confirmation_email(confirmation_link)

    try:
        server.login(sender, password)
        msg = MIMEMultipart()
        msg["Subject"] = "Подтверждение Test"
        msg["To"] = address
        msg["From"] = sender
        msg.attach(MIMEText(html_content, "html"))

        server.sendmail(
            sender,
            address,
            msg.as_string(),
        )
        return "the message was send"
    except Exception as e:
        return f"error: {e}"
    finally:
        server.quit()
