"""One-off helper: generate small JPEG thumbnails for cocktail list views."""

import os

from PIL import Image

IMAGES_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "images", "cocktails")
THUMBS_DIR = os.path.join(IMAGES_DIR, "thumbs")
THUMB_SIZE = 112  # 2x display size (56px) for retina


def generate_cocktail_thumbnails():
    os.makedirs(THUMBS_DIR, exist_ok=True)

    created = 0
    skipped = 0

    for filename in os.listdir(IMAGES_DIR):
        if not filename.endswith(".jpg"):
            continue

        source = os.path.join(IMAGES_DIR, filename)
        dest = os.path.join(THUMBS_DIR, filename)

        if os.path.exists(dest):
            skipped += 1
            continue

        with Image.open(source) as img:
            img = img.convert("RGB")
            img.thumbnail((THUMB_SIZE, THUMB_SIZE))
            img.save(dest, "JPEG", quality=75, optimize=True)
        created += 1

    print(f"Created {created} thumbnails, skipped {skipped} existing")


if __name__ == "__main__":
    generate_cocktail_thumbnails()
