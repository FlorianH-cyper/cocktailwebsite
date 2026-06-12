import json
import os

from . import db
from .models import Cocktail

SEED_FILE = os.path.join(os.path.dirname(__file__), "jobs", "cocktails_seed.json")


def seed_cocktails_if_empty():
    """Populate the cocktail table from the bundled seed file on first start
    (e.g. on a fresh deployment volume). Does nothing if data already exists."""
    if Cocktail.query.first() is not None:
        return

    if not os.path.exists(SEED_FILE):
        return

    with open(SEED_FILE, encoding="utf-8") as f:
        cocktails = json.load(f)

    for row in cocktails:
        db.session.add(Cocktail(**row))
    db.session.commit()
    print(f"Seeded {len(cocktails)} cocktails from {SEED_FILE}")
