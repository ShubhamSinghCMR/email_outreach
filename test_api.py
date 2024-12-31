import requests

# Base URL for API
BASE_URL = "http://127.0.0.1:8000/api/users/"

# User credentials for registration and login
USER_DATA = {
    "username": "user4",
    "password": "User@pass1"
}

# Template for email
TEMPLATE = "Hello {first_name}, welcome to our platform!"

# Register a New User
def test_register():
    data = {
        "username": USER_DATA["username"],
        "password": USER_DATA["password"]
    }
    response = requests.post(f"{BASE_URL}register/", json=data)
    print("Register Response:", response.status_code, response.json())
    if response.status_code == 201:
        print("Status: Registered")
    else:
        print("Status: Error")

# Login with the Registered User
def test_login():
    data = {
        "username": USER_DATA["username"],
        "password": USER_DATA["password"]
    }
    response = requests.post(f"{BASE_URL}login/", json=data)
    print("Login Response:", response.status_code, response.json())
    if response.status_code == 200:
        print("Status: Logged in")
        return response.json().get('refresh'), response.json().get('access')
    else:
        print("Status: Invalid credentials")
        return None, None

# Logout the User
def test_logout(refresh_token):
    data = {"refresh": refresh_token}
    response = requests.post(f"{BASE_URL}logout/", json=data)
    
    # Check status code first
    if response.status_code == 205:
        print("Logout Response:", response.status_code)
        print("Status: Logged out")
    else:
        print("Logout Response:", response.status_code, response.text)
        print("Status: Error")

# Test CSV Upload
def test_csv_upload():
    with open('testcsv.csv', 'rb') as file:
        response = requests.post(f"{BASE_URL}upload-csv/", files={'file': file})
    print("CSV Upload Response:", response.status_code, response.json())

# Test Template Creation
def test_template_creation():
    data = {
        "template": TEMPLATE
    }
    response = requests.post(f"{BASE_URL}template/", json=data)
    print("Template Response:", response.status_code, response.json())

if __name__ == "__main__":
    print("Testing Registration:")
    test_register()
    
    print("\nTesting Login:")
    refresh, access = test_login()

    print("Testing CSV Upload:")
    test_csv_upload()

    print("\nTesting Template Creation:")
    test_template_creation()

    print("\nTesting Logout:")
    if refresh:
        test_logout(refresh)
