import sys
sys.stdout.reconfigure(encoding="utf-8")

import json
import os
import httpx


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
SAMPLE_IMG_DIR = os.path.join(PROJECT_ROOT, "sample_images")
SAMPLE_IMG_PATH = os.path.join(SAMPLE_IMG_DIR, "test_sample.jpg")

MINIMAL_JPEG_BYTES = (
    b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01"
    b"\x00\x48\x00\x48\x00\x00\xFF\xD9"
)


def ensure_sample_image():
    os.makedirs(SAMPLE_IMG_DIR, exist_ok=True)
    if not os.path.exists(SAMPLE_IMG_PATH):
        try:
            from PIL import Image
            img = Image.new("RGB", (200, 200), color=(73, 109, 137))
            img.save(SAMPLE_IMG_PATH, "JPEG")
            print(f"Created sample image using PIL at: {SAMPLE_IMG_PATH}")
        except Exception:
            with open(SAMPLE_IMG_PATH, "wb") as f:
                f.write(MINIMAL_JPEG_BYTES)
            print(f"Created sample image binary at: {SAMPLE_IMG_PATH}")


def main():
    ensure_sample_image()

    url = "http://localhost:8000/api/scan"
    print(f"Sending POST request to {url} with image file...")

    with open(SAMPLE_IMG_PATH, "rb") as img_file:
        files = {"image": ("test_sample.jpg", img_file, "image/jpeg")}
        with httpx.Client(timeout=10.0) as client:
            response = client.post(url, files=files)

    print("\n--- TEST RESPONSE ---")
    print(f"HTTP Status Code: {response.status_code}")

    try:
        data = response.json()
        print("\nFull JSON Response:")
        print(json.dumps(data, indent=2))

        compliance = data.get("compliance", {})
        status = compliance.get("status", "N/A")
        violations = compliance.get("violations", [])

        print("\n========================================")
        print(f"COMPLIANCE STATUS    : {status}")
        print(f"COMPLIANCE VIOLATIONS: {violations}")
        print("========================================\n")
    except Exception as exc:
        print(f"Failed to parse JSON response: {exc}")
        print(f"Raw response content: {response.text}")


if __name__ == "__main__":
    main()
