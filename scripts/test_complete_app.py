import urllib.request
import urllib.error
import json
import mimetypes
import uuid
import os

BASE_URL = "http://localhost:3000"
AI_URL = "http://127.0.0.1:5000"

def log_test(name, result, detail=""):
    status = "SUCCESS" if result else "FAILED"
    print(f"[{status}] - {name} {detail}")

def test_ai_health():
    try:
        url = f"{AI_URL}/health"
        req = urllib.request.urlopen(url, timeout=5)
        res_data = json.loads(req.read().decode())
        log_test("AI Service Health Check", True, f"Response: {res_data}")
        return True
    except Exception as e:
        log_test("AI Service Health Check", False, str(e))
        return False

def test_backend_health():
    try:
        url = f"{BASE_URL}/health"
        req = urllib.request.urlopen(url, timeout=5)
        res_data = json.loads(req.read().decode())
        log_test("Backend Server Health Check", True, f"Response: {res_data}")
        return True
    except Exception as e:
        log_test("Backend Server Health Check", False, str(e))
        return False

def test_direct_predict():
    try:
        boundary = "Boundary-" + str(uuid.uuid4())
        image_path = "ai_service/test_sign.jpg"
        if not os.path.exists(image_path):
            image_path = "../ai_service/test_sign.jpg"
        with open(image_path, "rb") as f:
            img_data = f.read()

        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="test_sign.jpg"\r\n'
            f"Content-Type: image/jpeg\r\n\r\n"
        ).encode('utf-8') + img_data + f"\r\n--{boundary}--\r\n".encode('utf-8')

        req = urllib.request.Request(
            f"{AI_URL}/predict",
            data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST"
        )
        res = urllib.request.urlopen(req, timeout=10)
        res_data = json.loads(res.read().decode())
        log_test("AI Direct Predict", True, f"Response: {res_data}")
        return True
    except Exception as e:
        log_test("AI Direct Predict", False, str(e))
        return False

def test_backend_predict_proxy():
    try:
        boundary = "Boundary-" + str(uuid.uuid4())
        image_path = "ai_service/test_sign.jpg"
        if not os.path.exists(image_path):
            image_path = "../ai_service/test_sign.jpg"
        with open(image_path, "rb") as f:
            img_data = f.read()

        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="test_sign.jpg"\r\n'
            f"Content-Type: image/jpeg\r\n\r\n"
        ).encode('utf-8') + img_data + f"\r\n--{boundary}--\r\n".encode('utf-8')

        req = urllib.request.Request(
            f"{BASE_URL}/predict",
            data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST"
        )
        res = urllib.request.urlopen(req, timeout=10)
        res_data = json.loads(res.read().decode())
        log_test("Backend Predict Proxy (No Auth)", True, f"Response: {res_data}")
        return True
    except Exception as e:
        log_test("Backend Predict Proxy (No Auth)", False, str(e))
        return False

def run_auth_and_protected_tests():
    # 1. Register a new random user
    email = f"user-{uuid.uuid4().hex[:6]}@test.com"
    password = "Password123"
    register_body = {
        "name": f"User {uuid.uuid4().hex[:4]}",
        "email": email,
        "password": password,
        "confirmPassword": password
    }
    
    token = None
    try:
        # 1. Register
        req = urllib.request.Request(
            f"{BASE_URL}/api/auth/register",
            data=json.dumps(register_body).encode('utf-8'),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        res = urllib.request.urlopen(req, timeout=10)
        res_data = json.loads(res.read().decode())
        log_test("User Registration", True, f"Registered: {email}")
        
        # 2. Login to get token
        login_body = {
            "email": email,
            "password": password
        }
        req_login = urllib.request.Request(
            f"{BASE_URL}/api/auth/login",
            data=json.dumps(login_body).encode('utf-8'),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        res_login = urllib.request.urlopen(req_login, timeout=10)
        res_login_data = json.loads(res_login.read().decode())
        token = res_login_data.get("data", {}).get("token")
        log_test("User Login", True, f"Logged in: {email}")
    except Exception as e:
        log_test("User Registration/Login", False, str(e))
        return False

    if not token:
        log_test("Token Generation Check", False, "No auth token returned during registration")
        return False

    # 2. Test profile fetching
    try:
        req = urllib.request.Request(
            f"{BASE_URL}/api/users/me",
            headers={"Authorization": f"Bearer {token}"},
            method="GET"
        )
        res = urllib.request.urlopen(req, timeout=10)
        res_data = json.loads(res.read().decode())
        user_name = res_data.get('data', {}).get('user', {}).get('name')
        log_test("Get User Profile (Authenticated)", True, f"User Name: {user_name}")
    except Exception as e:
        log_test("Get User Profile (Authenticated)", False, str(e))
        return False

    # 3. Upload and translate with media record generation and DB storage
    try:
        boundary = "Boundary-" + str(uuid.uuid4())
        image_path = "ai_service/test_sign.jpg"
        if not os.path.exists(image_path):
            image_path = "../ai_service/test_sign.jpg"
        with open(image_path, "rb") as f:
            img_data = f.read()

        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="test_sign.jpg"\r\n'
            f"Content-Type: image/jpeg\r\n\r\n"
        ).encode('utf-8') + img_data + f"\r\n--{boundary}--\r\n".encode('utf-8')

        req = urllib.request.Request(
            f"{BASE_URL}/api/translation/upload",
            data=body,
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "Authorization": f"Bearer {token}"
            },
            method="POST"
        )
        res = urllib.request.urlopen(req, timeout=10)
        res_data = json.loads(res.read().decode())
        log_test("Translation Upload & Save (Authenticated)", True, f"Translation: {res_data.get('data', {}).get('translation')}")
    except Exception as e:
        log_test("Translation Upload & Save (Authenticated)", False, str(e))
        return False

    # 4. Fetch translation history
    try:
        req = urllib.request.Request(
            f"{BASE_URL}/api/translation/history",
            headers={"Authorization": f"Bearer {token}"},
            method="GET"
        )
        res = urllib.request.urlopen(req, timeout=10)
        res_data = json.loads(res.read().decode())
        items = res_data.get('data', {}).get('items', [])
        log_test("Fetch Translation History (Authenticated)", True, f"History items count: {len(items)}")
    except Exception as e:
        log_test("Fetch Translation History (Authenticated)", False, str(e))
        return False

    return True

if __name__ == "__main__":
    print("=" * 60)
    print("STARTING COMPLETE END-TO-END APPLICATION TESTS")
    print("=" * 60)
    
    success = True
    success &= test_ai_health()
    success &= test_backend_health()
    success &= test_direct_predict()
    success &= test_backend_predict_proxy()
    success &= run_auth_and_protected_tests()
    
    print("=" * 60)
    if success:
        print("ALL TESTS PASSED SUCCESSFULLY! [SUCCESS]")
    else:
        print("SOME TESTS FAILED. Please check logs.")
    print("=" * 60)
