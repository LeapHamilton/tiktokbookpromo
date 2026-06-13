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


def get_image_urls(folder):
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/images/{folder}"
    r = requests.get(url, params={"ref": GITHUB_BRANCH})
    r.raise_for_status()
    files = r.json()
    urls = []
    for f in sorted(files, key=lambda x: x["name"]):
        if f["name"].lower().endswith((".jpg", ".jpeg", ".png")):
            raw = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/images/{folder}/{f['name']}"
            urls.append(raw)
    return urls


def post_photo_slideshow(access_token, image_urls):
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
            "source": "PULL_FROM_URL",
            "photo_images": image_urls,
            "photo_cover_index": 0,
        },
        "media_type": "PHOTO",
    }
    r = requests.post(
        "https://open.tiktokapis.com/v2/post/publish/content/init/",
        headers=headers,
        json=payload,
    )
    r.raise_for_status()
    return r.json()


def main():
    print("Refreshing access token...")
    access_token = refresh_access_token()

    print("Finding slideshow folders...")
    folders = get_slideshow_folders()
    print(f"Found folders: {folders}")

    folder = get_next_folder(folders)
    print(f"Posting folder: {folder}")

    image_urls = get_image_urls(folder)
    print(f"Images: {image_urls}")

    print("Posting to TikTok...")
    result = post_photo_slideshow(access_token, image_urls)
    print("Result:", json.dumps(result, indent=2))

    print(f"Done. Posted: {folder}")


if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
