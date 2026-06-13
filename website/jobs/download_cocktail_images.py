"""One-off helper: download remote cocktail images and update the seed JSON to
use local static paths under website/static/images/cocktails/."""

import json
import os
import time

import requests

SEED_FILE = os.path.join(os.path.dirname(__file__), "cocktails_seed.json")
IMAGES_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "images", "cocktails")


def local_image_path(cocktail_id):
    return f"/static/images/cocktails/{cocktail_id}.jpg"


def download_cocktail_images():
    os.makedirs(IMAGES_DIR, exist_ok=True)

    with open(SEED_FILE, encoding="utf-8") as f:
        cocktails = json.load(f)

    session = requests.Session()
    session.headers.update({"User-Agent": "Mixly/1.0 (cocktail catalog seed)"})

    downloaded = 0
    skipped = 0
    failed = []

    for cocktail in cocktails:
        cocktail_id = cocktail["id"]
        dest = os.path.join(IMAGES_DIR, f"{cocktail_id}.jpg")
        local_path = local_image_path(cocktail_id)

        if os.path.exists(dest):
            cocktail["image"] = local_path
            skipped += 1
            continue

        url = cocktail.get("image", "")
        if not url or not url.startswith("http"):
            failed.append((cocktail_id, cocktail.get("name"), "missing or invalid URL"))
            continue

        try:
            resp = session.get(url, timeout=30)
            resp.raise_for_status()
            with open(dest, "wb") as f:
                f.write(resp.content)
            cocktail["image"] = local_path
            downloaded += 1
            time.sleep(0.05)
        except requests.RequestException as exc:
            failed.append((cocktail_id, cocktail.get("name"), str(exc)))

    with open(SEED_FILE, "w", encoding="utf-8") as f:
        json.dump(cocktails, f, ensure_ascii=False, indent=1)

    print(f"Downloaded {downloaded}, already present {skipped}, failed {len(failed)}")
    for cocktail_id, name, error in failed:
        print(f"  Failed {cocktail_id} ({name}): {error}")


if __name__ == "__main__":
    download_cocktail_images()
