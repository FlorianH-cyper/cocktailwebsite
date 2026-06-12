"""One-off helper: export all cocktails from a local SQLite DB into the
JSON seed file that gets committed to the repo and loaded on app startup."""

import json
import os
import sqlite3

SOURCE_DB = os.path.join(os.path.dirname(__file__), "..", "..", "instance", "database.db")
SEED_FILE = os.path.join(os.path.dirname(__file__), "cocktails_seed.json")


def export_cocktails():
    conn = sqlite3.connect(SOURCE_DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM cocktail").fetchall()
    conn.close()

    cocktails = [dict(row) for row in rows]
    with open(SEED_FILE, "w", encoding="utf-8") as f:
        json.dump(cocktails, f, ensure_ascii=False, indent=1)

    print(f"Exported {len(cocktails)} cocktails to {os.path.abspath(SEED_FILE)}")


if __name__ == "__main__":
    export_cocktails()
