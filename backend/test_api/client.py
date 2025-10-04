import requests

BASE_URL = "http://127.0.0.1:8000/api/users/"


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


def follow_user(access_token, username_to_follow):
    url = f"{BASE_URL}{username_to_follow}/follow/"
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.post(url, headers=headers)
    if response.status_code in (200, 201):
        print(f"✅ Successfully followed {username_to_follow}")
        print(response.json())
        return response.json()
    else:
        print(f"❌ Failed to follow {username_to_follow}: {response.status_code}, {response.text}")
        return None


if __name__ == "__main__":
    # Step 1: Register with your email
    register(
        username="punit_test_user",
        first_name="Punit",
        email="punitsinha1542004@gmail.com",
        password="SuperStrongPass123",
        password2="SuperStrongPass123",
        location="Mumbai",
        bio="Testing notifications!"
    )

    # Step 2: Login
    tokens = login("punit_test_user", "SuperStrongPass123")
    access_token = tokens.get("access") if tokens else None
    print("Access token:", access_token)

    # Step 3: Follow a real user
    if access_token:
        # Replace 'realusername' with the username of an actual person in your DB
        follow_user(access_token, "NotABot")
