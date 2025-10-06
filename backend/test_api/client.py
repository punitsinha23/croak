import requests

BASE_URL = "http://127.0.0.1:8000/api/users/"
RIBBIT_URL = "http://127.0.0.1:8000/api/ribbit/"


def register(username, first_name, email, password, password2=None, location="", bio=""):
    if password2 is None:
        password2 = password
    payload = {
        "username": username,
        "first_name": first_name,
        "email": email,
        "password": password,
        "password2": password2,
        "location": location,
        "bio": bio,
    }
    response = requests.post(BASE_URL + "register/", json=payload)
    print("REGISTER:", response.status_code, response.text)
    return response.json() if response.status_code in (200, 201) else None


def login(username, password):
    payload = {"username": username, "password": password}
    response = requests.post(BASE_URL + "login/", json=payload)
    print("LOGIN:", response.status_code, response.text)
    return response.json() if response.status_code == 200 else None


def create_ribbit(access_token, text="Testing like notifications 🚀"):
    """Create a test ribbit post"""
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"text": text}
    response = requests.post(RIBBIT_URL + "ribbits/", headers=headers, json=payload)
    print("CREATE RIBBIT:", response.status_code, response.text)
    if response.status_code in (200, 201):
        return response.json().get("id")
    return None


def like_ribbit(access_token, ribbit_id):
    """Like a specific ribbit"""
    url = f"{RIBBIT_URL}ribbits/{ribbit_id}/like/"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.post(url, headers=headers)
    print("LIKE RIBBIT:", response.status_code, response.text)
    if response.status_code in (200, 201):
        print("✅ Successfully liked ribbit!")
    else:
        print(f"❌ Failed to like ribbit: {response.status_code}, {response.text}")

def follow(access_token, user_name):
    """Like a specific ribbit"""
    url = f"{BASE_URL}{user_name}/follow/"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.post(url, headers=headers)
    print("LIKE RIBBIT:", response.status_code, response.text)
    if response.status_code in (200, 201):
        print("✅ Successfully liked ribbit!")
    else:
        print(f"❌ Failed to like ribbit: {response.status_code}, {response.text}")  

def comment(access_token, ribbit_id, text="Hey"):
    """Comment on a specific ribbit"""
    url = f"{RIBBIT_URL}ribbits/{ribbit_id}/comment/"
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"text": text}
    response = requests.post(url, headers=headers, json=payload)
    print("COMMENT RIBBIT:", response.status_code, response.text)
    if response.status_code in (200, 201):
        print("✅ Successfully commented on ribbit!")
    else:
        print(f"❌ Failed to comment on ribbit: {response.status_code}, {response.text}")



if __name__ == "__main__":
    # Step 1: Register two users
    register(
        username="like_tester",
        first_name="Like",
        email="like_tester@gmail.com",
        password="StrongPass123",
        password2="StrongPass123",
        location="Delhi",
        bio="Testing like notifications!"
    )

    register(
        username="post_owner",
        first_name="Owner",
        email="post_owner@gmail.com",
        password="StrongPass123",
        password2="StrongPass123",
        location="Pune",
        bio="Will get a like notification!"
    )


    liker_tokens = login("like_tester", "StrongPass123")
    liker_token = liker_tokens.get("access") if liker_tokens else None


    like_ribbit(liker_token, 48)
    follow(liker_token , "NotABot")
    comment(liker_token, 48, "Nice ribbit!")
