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


def get_real_sample_image() -> tuple[str, str]:
    os.makedirs(SAMPLE_IMG_DIR, exist_ok=True)
    candidates = []
    for fname in os.listdir(SAMPLE_IMG_DIR):
        fpath = os.path.join(SAMPLE_IMG_DIR, fname)
        if os.path.isfile(fpath) and fname != ".gitkeep":
            size = os.path.getsize(fpath)
            if size > 1000:  # real photo, not tiny stub
                candidates.append((fpath, fname, size))

    if candidates:
        # Pick the largest image file or first real photo
        candidates.sort(key=lambda x: x[2], reverse=True)
        chosen_path, chosen_name, chosen_size = candidates[0]
        print(f"Using real sample image: {chosen_name} ({chosen_size / 1024:.1f} KB) at {chosen_path}")
        return chosen_path, chosen_name

    # Fallback if no real photo exists
    ensure_sample_image()
    return SAMPLE_IMG_PATH, "test_sample.jpg"


def main():
    image_path, filename = get_real_sample_image()
    content_type = "image/png" if filename.lower().endswith(".png") else "image/jpeg"

    url = "http://localhost:8000/api/scan"
    print(f"Sending POST request to {url} with image file '{filename}'...")

    with open(image_path, "rb") as img_file:
        files = {"image": (filename, img_file, content_type)}
        with httpx.Client(timeout=120.0) as client:
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
