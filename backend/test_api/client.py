import requests

BASE_URL = "http://127.0.0.1:8000/api/users/"

def register(username, email, password, password2, location , bio="",):
    if password2 is None:
        password2 = password
    payload = {
        "username": username,
        "email": email,
        "password": password,
        "password2": password2,
        "location":location,
        "bio": bio,

    }
    response = requests.post(BASE_URL + "register/", json=payload)
    print("REGISTER:", response.status_code, response.json())


def login(username, password):
    payload = {"username": username, "password": password}
    response = requests.post(BASE_URL + "login/", json=payload)
    print("LOGIN:", response.status_code, response.json())
    return response.json()


def get_user_profile(access_token):
    url = BASE_URL + "me/"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        print("✅ User profile data:")
        print(response.json())
    else:
        print(f"❌ Error {response.status_code}: {response.text}")


if __name__ == "__main__":
    # test register
    register(
        username="testuser4",
        email="test4@example.com",
        password="SuperStrongPass123",
        password2="SuperStrongPass123",
        location="Mumbai",
        bio="This is my bio"
    )

    # test login
    tokens = login("testuser4", "SuperStrongPass123")
    access_token = tokens.get("access")
    print("Access token:", access_token)

    # test user profile
    if access_token:
        get_user_profile(access_token)

