import requests

BASE_URL = "http://127.0.0.1:8000/api/users/"


def register(username, email, password, password2, location, bio=""):
    if password2 is None:
        password2 = password
    payload = {
        "username": username,
        "email": email,
        "password": password,
        "password2": password2,
        "location": location,
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
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        print("✅ User profile data:")
        print(response.json())
    else:
        print(f"❌ Error {response.status_code}: {response.text}")


def post_ribbit(access_token, text="this is a test ribbit"):
    url = "http://127.0.0.1:8000/api/ribbit/post/"
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"text": text}

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code in (200, 201):
        print("✅ Ribbit posted:")
        data = response.json()
        print(data)
        return data
    else:
        print(f"❌ Error {response.status_code}: {response.text}")
        return None


def update_ribbit(access_token, ribbit_id, new_text="updated ribbit text"):
    # ⚠️ Change this endpoint if your backend uses a different route for update
    url = f"http://127.0.0.1:8000/api/ribbit/update/{ribbit_id}/"
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"text": new_text}

    response = requests.patch(url, headers=headers, json=payload)

    if response.status_code in (200, 202):
        print("✅ Ribbit updated:")
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
        bio="This is my bio",
    )

    # test login
    tokens = login("testuser4", "SuperStrongPass123")
    access_token = tokens.get("access")
    print("Access token:", access_token)

    # test user profile + ribbit flow
    if access_token:
        get_user_profile(access_token)

        # create ribbit
        ribbit = post_ribbit(access_token, "first ribbit via API test")
        if ribbit:
            ribbit_id = ribbit.get("id")
            # update ribbit
            update_ribbit(access_token, ribbit_id, "ribbit has been updated via API ✅")
