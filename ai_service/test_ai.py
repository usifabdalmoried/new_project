"""
Quick test script for the AI Flask Service.
Run: python test_ai.py
"""
import urllib.request
import json

BASE_URL = "http://127.0.0.1:5000"

# ── 1. Health Check ────────────────────────────────────────────────────────────
print("=" * 50)
print("TEST 1: AI Health Check")
try:
    req = urllib.request.urlopen(f"{BASE_URL}/health", timeout=5)
    data = json.loads(req.read())
    print(f"  Status : 200 OK")
    print(f"  Response: {data}")
    print("  PASSED")
except Exception as e:
    print(f"  FAILED: {e}")

# ── 2. Predict with test image ─────────────────────────────────────────────────
print()
print("=" * 50)
print("TEST 2: AI Predict (sign language image)")
try:
    boundary = b"TestBoundary7MA4X"
    with open("test_sign.jpg", "rb") as f:
        img_data = f.read()

    body = (
        b"--" + boundary + b"\r\n"
        b'Content-Disposition: form-data; name="file"; filename="test_sign.jpg"\r\n'
        b"Content-Type: image/jpeg\r\n\r\n"
        + img_data
        + b"\r\n--" + boundary + b"--\r\n"
    )

    request = urllib.request.Request(
        f"{BASE_URL}/predict",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary=TestBoundary7MA4X"},
        method="POST"
    )
    res = urllib.request.urlopen(request, timeout=15)
    result = json.loads(res.read())
    print(f"  Status   : 200 OK")
    print(f"  Translation : {result.get('translation')}")
    print(f"  Confidence  : {result.get('confidence')}")
    print(f"  Full Response: {result}")
    print("  PASSED")
except Exception as e:
    print(f"  FAILED: {e}")

print()
print("=" * 50)
print("All tests done!")
