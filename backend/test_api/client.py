import requests

BASE_URL = "http://127.0.0.1:8000/api/"
USERS_URL = BASE_URL + "users/"
RIBBIT_URL = BASE_URL + "ribbit/"


# -----------------------------
# AUTH HELPERS
# -----------------------------
def register(username, email, password):
    payload = {
        "username": username,
        "email": email,
        "first_name": "Test",
        "password": password,
        "password2": password
    }
    res = requests.post(USERS_URL + "register/", json=payload)
    print("REGISTER:", res.status_code)
    return res.json() if res.status_code in (200, 201) else None


def login(username, password):
    payload = {"username": username, "password": password}
    res = requests.post(USERS_URL + "login/", json=payload)
    print("LOGIN:", res.status_code)
    return res.json() if res.status_code == 200 else None


# -----------------------------
# REPLY API TEST
# -----------------------------
def create_reply(access_token, comment_id, text="Test reply from script"):
    url = f"{RIBBIT_URL}comments/{comment_id}/replies/"
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"text": text}

    res = requests.post(url, headers=headers, json=payload)
    print("CREATE REPLY:", res.status_code, res.text)

    return res.json() if res.status_code in (200, 201) else None


def list_replies(access_token, comment_id):
    url = f"{RIBBIT_URL}comments/{comment_id}/replies/"
    headers = {"Authorization": f"Bearer {access_token}"}

    res = requests.get(url, headers=headers)
    print("LIST REPLIES:", res.status_code, res.text)
    return res.json() if res.status_code == 200 else None


# -----------------------------
# RUN TEST
# -----------------------------
if __name__ == "__main__":
    # Create a test user

    tokens = login("punitsinha", "@12345678")
    access_token = tokens.get("access")

    # >>> Change comment_id to test
    COMMENT_ID = 64

    create_reply(access_token, COMMENT_ID, text="Hello from reply tester!")
    list_replies(access_token, COMMENT_ID)
