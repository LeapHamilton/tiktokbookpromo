import os
import json
import requests
from datetime import date

CLIENT_KEY = os.environ["TIKTOK_CLIENT_KEY"]
CLIENT_SECRET = os.environ["TIKTOK_CLIENT_SECRET"]
REFRESH_TOKEN = os.environ["TIKTOK_REFRESH_TOKEN"]

GITHUB_USER = os.environ["GITHUB_USER"]
GITHUB_REPO = os.environ["GITHUB_REPO"]
GITHUB_BRANCH = os.environ.get("GITHUB_BRANCH", "main")

CAPTION = "Check out my new book! 📖 #BookTok #NewRelease"


def refresh_access_token():
    r = requests.post("https://open.tiktokapis.com/v2/oauth/token/", data={
        "client_key": CLIENT_KEY,
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN,
    })
    r.raise_for_status()
    return r.json()["access_token"]


def get_slideshow_folders():
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/images"
    r = requests.get(url, params={"ref": GITHUB_BRANCH})
    r.raise_for_status()
    folders = [f["name"] for f in r.json() if f["type"] == "dir"]
    return sorted(folders)


def get_next_folder(folders):
    day_number = (date.today() - date(2026, 1, 1)).days
    return folders[day_number % len(folders)]


def download_images(folder):
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/images/{folder}"
    r = requests.get(url, params={"ref": GITHUB_BRANCH})
    r.raise_for_status()
    files = r.json()
    local_paths = []
    for f in sorted(files, key=lambda x: x["name"]):
        if f["name"].lower().endswith((".jpg", ".jpeg", ".png")):
            raw_url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/images/{folder}/{f['name']}"
            img_data = requests.get(raw_url).content
            local_path = f"/tmp/{f['name']}"
            with open(local_path, "wb") as img_file:
                img_file.write(img_data)
            local_paths.append(local_path)
            print(f"Downloaded: {f['name']}")
    return local_paths


def initialize_photo_post(access_token, image_count):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=UTF-8",
    }
    payload = {
        "post_info": {
            "title": CAPTION,
            "privacy_level": "SELF_ONLY",
            "disable_duet": False,
            "disable_comment": False,
            "disable_stitch": False,
        },
        "source_info": {
            "source": "FILE_UPLOAD",
            "photo_cover_index": 0,
            "photo_count": image_count,
        },
        "media_type": "PHOTO",
        "post_mode": "DIRECT_POST",
    }
    r = requests.post(
        "https://open.tiktokapis.com/v2/post/publish/content/init/",
        headers=headers,
        json=payload,
    )
    if not r.ok:
        print("TikTok error response:", r.status_code, r.text)
        r.raise_for_status()
    return r.json()


def upload_image(upload_url, image_path):
    with open(image_path, "rb") as f:
        image_data = f.read()
    headers = {
        "Content-Type": "image/jpeg",
        "Content-Length": str(len(image_data)),
    }
    r = requests.put(upload_url, data=image_data, headers=headers)
    if not r.ok:
        print("Upload error:", r.status_code, r.text)
        r.raise_for_status()
    print(f"Uploaded: {image_path}")


def main():
    print("Refreshing access token...")
    access_token = refresh_access_token()

    print("Finding slideshow folders...")
    folders = get_slideshow_folders()
    print(f"Found folders: {folders}")

    folder = get_next_folder(folders)
    print(f"Posting folder: {folder}")

    print("Downloading images...")
    local_paths = download_images(folder)
    print(f"Downloaded {len(local_paths)} images")

    print("Initializing TikTok post...")
    init_result = initialize_photo_post(access_token, len(local_paths))
    print("Init result:", json.dumps(init_result, indent=2))

    upload_urls = init_result["data"]["upload_urls"]
    for image_path, upload_url in zip(local_paths, upload_urls):
        upload_image(upload_url, image_path)

    print("Done. Posted folder:", folder)


if __name__ == "__main__":
    main()
