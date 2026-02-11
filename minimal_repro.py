import base64
import json
import urllib.request
import urllib.error

# Hardcoded URL for OCR endpoint
url = "http://127.0.0.1:8000/v1/projects/test/ocr"

# 1KB raw image, base64-encoded
raw_img = bytes([0] * 1024)
b64_img = base64.b64encode(raw_img).decode()

payload = {
    "images": [b64_img]
}

headers = {"Content-Type": "application/json"}
data = json.dumps(payload).encode()

req = urllib.request.Request(url, data=data, headers=headers, method="POST")
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        status = resp.status
        x_request_id = resp.headers.get('x-request-id')
        body = resp.read().decode()
except urllib.error.HTTPError as e:
    status = e.code
    x_request_id = e.headers.get('x-request-id')
    body = e.read().decode()

print(f"Status: {status}")
print(f"x-request-id: {x_request_id}")
print(f"Body: {body}")
