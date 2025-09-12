import requests

BASE_URL = "http://127.0.0.1:8000/api/users/"

def register(username, email, password, password2=None, bio=""):
    if password2 is None:
        password2 = password
    payload = {
        "username": username,
        "email": email,
        "password": password,
        "password2": password2,
        "bio": bio,
    }
    response = requests.post(BASE_URL + "register/", json=payload)
    print("REGISTER:", response.status_code, response.json())


def login(username, password):
    payload = {"username": username, "password": password}
    response = requests.post(BASE_URL + "login/", json=payload)
    print("LOGIN:", response.status_code, response.json())
    return response.json()


if __name__ == "__main__":
    # test register
    #register("testuser", "test@example.com", "SuperStrongPass123")

    # test login
    tokens = login("testuser", "SuperStrongPass123")
    print("Access token:", tokens.get("access"))
