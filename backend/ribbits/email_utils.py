import os
import requests

def send_resend_email(to, subject, html):
    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {os.getenv('RESEND_API_KEY')}",
        "Content-Type": "application/json",
    }
    data = {
        "from": "Your App <no-reply@resend.dev>",
        "to": [to],
        "subject": subject,
        "html": html,
    }
    res = requests.post(url, headers=headers, json=data)
    print("📨 Email status:", res.status_code, res.text)
    return res.json()
