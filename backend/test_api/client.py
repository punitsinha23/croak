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


def like_ribbit(access_token, ribbit_id):
    url = f"http://127.0.0.1:8000/api/ribbit/ribbits/{ribbit_id}/like/"
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.post(url, headers=headers)

    if response.status_code in (200, 201):
        print("✅ Like action success:")
        print(response.json())  # shows {"status": "liked"/"unliked", "likes_count": N}
        return response.json()
    else:
        print(f"❌ Error {response.status_code}: {response.text}")
        return None

def get_liked_ribbits(access_token):
    url = "http://127.0.0.1:8000/api/ribbit/liked/"
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        print("✅ Liked ribbits:")
        for ribbit in data.get("results", data):  # handle pagination or plain list
            print(f"- ID {ribbit['id']}: {ribbit['text']} (likes={ribbit['likes_count']}, is_liked={ribbit['is_liked']})")
        return data
    else:
        print(f"❌ Error {response.status_code}: {response.text}")
        return None

def test_comments(access_token, ribbit_id):
    url = f"http://127.0.0.1:8000/api/ribbit/ribbits/{ribbit_id}/comment/"
    headers = {"Authorization": f"Bearer {access_token}"}

    # 1. Post a new comment
    payload = {"text": "This is a test comment"}
    response = requests.post(url, headers=headers, json=payload)

    if response.status_code in (200, 201):
        print("✅ Comment posted successfully:")
        comment_data = response.json()
        print(comment_data)
    else:
        print(f"❌ Failed to post comment ({response.status_code}): {response.text}")
        return

    # 2. Fetch all comments for that ribbit
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        comments = data.get("results", [])  # <- access paginated results
        print("✅ Comments fetched:")
        for c in comments:
            print(f"- ID {c.get('id', 'N/A')}: {c['text']} (author={c['author']['username']})")
    else:
        print(f"❌ Failed to fetch comments ({response.status_code}): {response.text}")



if __name__ == "__main__":
    # Step 1: Register
    register(
        username="testuser4",
        email="test4@example.com",
        password="SuperStrongPass123",
        password2="SuperStrongPass123",
        location="Mumbai",
        bio="This is my bio",
    )

    # Step 2: Login
    tokens = login("testuser4", "SuperStrongPass123")
    access_token = tokens.get("access")
    print("Access token:", access_token)

    # Step 3: Run flow only if login worked
    if access_token:
        # Fetch profile
        get_user_profile(access_token)

        # Step 4: Post a ribbit
        ribbit = post_ribbit(access_token, "liking another ribbit test")
        if ribbit:
            ribbit_id = ribbit.get("id")

            # Step 5: Like the ribbit
            print("\n--- Liking ribbit ---")
            like_result = like_ribbit(access_token, ribbit_id)

            if like_result and like_result.get("status") == "liked":
                print(f"✅ Ribbit {ribbit_id} liked. Likes count: {like_result.get('likes_count')}")
            else:
                print("❌ Like action did not work as expected.")

            # Step 6: Fetch liked ribbits
            print("\n--- Fetching liked ribbits ---")
            liked_posts = get_liked_ribbits(access_token)

            # Step 7: Test comments
            print("\n--- Testing comments ---")
            test_comments(access_token, ribbit_id)

