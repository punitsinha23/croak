from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import smtplib
import ssl
from email.message import EmailMessage
import os
from dotenv import load_dotenv
import logging

# ---------------------- CONFIG ----------------------
load_dotenv()  # Loads .env file if present

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
SENDER_EMAIL = 'sinhapunit323@gmail.com'
SENDER_PASSWORD = 'ybyx vuhd vaer svze'

# ---------------------- APP SETUP ----------------------
app = FastAPI(
    title="Email Notification API",
    description="A microservice to send emails to users.",
    version="1.0.0"
)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ---------------------- MODELS ----------------------
class EmailRequest(BaseModel):
    recipient: EmailStr
    subject: str
    body: str

# ---------------------- UTIL FUNCTION ----------------------
def send_email(recipient: str, subject: str, body: str) -> bool:
    try:
        if not SENDER_EMAIL or not SENDER_PASSWORD:
            raise ValueError("Missing email credentials. Set SENDER_EMAIL and SENDER_PASSWORD in .env")

        msg = EmailMessage()
        msg["From"] = SENDER_EMAIL
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.set_content(body)

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)

        logging.info(f"✅ Email sent to {recipient} | Subject: {subject}")
        return True

    except Exception as e:
        logging.error(f"❌ Failed to send email to {recipient}: {e}")
        return False

# ---------------------- ROUTES ----------------------
@app.get("/")
def root():
    return {"message": "FastAPI Email Service is running 🚀"}

@app.post("/api/send-email")
def send_email_api(request: EmailRequest):
    success = send_email(request.recipient, request.subject, request.body)
    if success:
        return {"status": "success", "message": f"Email sent to {request.recipient}"}
    raise HTTPException(status_code=500, detail="Failed to send email. Check logs for details.")

# ---------------------- ENTRY POINT ----------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
