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

# Data for sending the email
email_data = {
    "subject": "Test Email",
    "message": "This is a test email sent from Django.",
    "recipient_list": ["shubhamsinghcmr@gmaail.com","shubhamsinghcmr@gmail.com","itzzshubh@gmail.com"]
}

# AI Input
ai_data = {
        "description": "New Year Sale"
    }

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

# Send Test Mail
def test_send_email():
    response = requests.post(f"{BASE_URL}send-email/", json=email_data)

    if response.status_code == 200:
        print("Email sending started.")
        print("Sent to valid emails:", response.json().get('sent_to'))
        print("Not sent to invalid emails:", response.json().get('not_sent_to'))
    else:
        print("Error sending email:", response.status_code, response.json())

# Function for AI suggestions
def ai_suggestion_email(data):
    response = requests.post(f"{BASE_URL}ai-suggestions/", json=data, headers={'Authorization': f'Bearer {access}'})

    if response.status_code == 200:
        print("Generated Subject:", response.json()['subject'])
        print("Generated Body:", response.json()['body'])
    else:
        print("Error in AI Suggestion:", response.status_code, response.json())


if __name__ == "__main__":
    print("Testing Registration:")
    test_register()
    
    print("\nTesting Login:")
    refresh, access = test_login()

    print("\nTesting CSV Upload:")
    test_csv_upload()

    print("\nTesting Template Creation:")
    test_template_creation()

    print("\nTesting Email Send:")
    test_send_email()

    print("\nTesting AI Email Suggestions:")
    ai_suggestion_email(ai_data)

    print("\nTesting Logout:")
    if refresh:
        test_logout(refresh)
