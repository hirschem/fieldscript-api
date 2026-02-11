import base64
import json
import urllib.request
import urllib.error

# Hardcoded URL for OCR endpoint
url = "http://127.0.0.1:8000/v1/projects/test/ocr"

# 2MB raw image, base64-encoded
raw_size = 2 * 1024 * 1024  # 2MB decoded
raw_img = bytes([0] * raw_size)
b64_img = base64.b64encode(raw_img).decode()
# Each base64 image is ~2.67MB encoded

# 10 images: 20MB decoded, ~26.7MB base64
images = [b64_img] * 10

payload = {
    "images": images
}

headers = {"Content-Type": "application/json"}
data = json.dumps(payload).encode()

print(f"Total decoded bytes: {raw_size * 10 / (1024*1024):.2f} MB")
print(f"Total base64 bytes: {len(b64_img) * 10 / (1024*1024):.2f} MB")
print(f"Total JSON payload size: {len(data) / (1024*1024):.2f} MB")

req = urllib.request.Request(url, data=data, headers=headers, method="POST")
try:
    with urllib.request.urlopen(req, timeout=30) as resp:
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
