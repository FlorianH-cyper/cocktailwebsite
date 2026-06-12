# Mixly

**Plan the party. Pick the drinks. Get the shopping list.**

Mixly is a party-planning web app: create an event, browse **633 cocktails**, build a menu, and receive an automatically aggregated shopping list — no spreadsheet required.

---

## Features

| | |
|---|---|
| **Party planning** | Set guests, drinks per person, and build a cocktail menu |
| **Cocktail search** | Live search with recipes, images, and community star ratings |
| **Shopping list** | Ingredients rolled up across your menu, ready to shop |
| **Accounts** | Sign up, log in, and keep your parties in one place |

---

## Quick start

```powershell
pip install -r requirements.txt
$env:FLASK_DEBUG = "1"
python main.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000). On first run, SQLite creates `instance/database.db` and seeds the full cocktail catalog automatically.

---

## Tech stack

Flask · SQLAlchemy · SQLite · Flask-Login · Jinja2 · vanilla JS

Production runs on **Gunicorn** (Railway, persistent volume for the database).

---

## Configuration

| Variable | Default | Notes |
|---|---|---|
| `SECRET_KEY` | dev fallback | Set a strong secret in production |
| `DATABASE_PATH` | `instance/database.db` | `/data/database.db` on Railway |
| `FLASK_DEBUG` | off | Enable locally for auto-reload only |

---

## Documentation

For data models, API routes, auth, deployment, and seeding details, see **[ARCHITECTURE.md](ARCHITECTURE.md)**.