import threading

import requests
from django.conf import settings


def post_to_notifications(path, payload, timeout=10):
    return requests.post(
        f"{settings.NOTIFICATIONS_SERVICE_URL}{path}",
        json=payload,
        headers={"X-Notify-Secret": settings.NOTIFICATIONS_SECRET},
        timeout=timeout,
    )


def send_in_background(path, payload):
    def run():
        try:
            post_to_notifications(path, payload)
        except Exception as e:
            print(f"Error calling notifications service {path}: {e}")

    threading.Thread(target=run, daemon=True).start()
