# Mixly

Plan a cocktail party, pick the drinks, get the shopping list.

Mixly is a web app for cocktail party planning: create a party with a number of guests, browse a catalog of **633 cocktails**, build your drink menu — and Mixly aggregates everything into a single shopping list so you know exactly what to buy.

## Features

- **Parties** — create parties with guest count and drinks per person; Mixly tracks how many drinks you still need to plan
- **Cocktail search** — filter 633 cocktails by name, category, alcohol content, and number of ingredients, with recipes and photos
- **Drink menu** — add cocktails to a party with custom amounts
- **Shopping list** — ingredients from all menu items, automatically aggregated per party
- **Accounts** — sign up and keep your parties separate from other users
- **Dark mode** — because cocktails happen at night

## Tech Stack

| | |
|---|---|
| Backend | Python, Flask, Flask-SQLAlchemy, Flask-Login |
| Database | SQLite |
| Frontend | Jinja2 templates, vanilla JavaScript, custom CSS |
| Deployment | Railway (Gunicorn + persistent volume) |

No frontend framework, no build step — one Flask process serves everything.

Curious how it works under the hood? See [ARCHITECTURE.md](ARCHITECTURE.md).

## Run It Locally

Requirements: Python 3.11+

```powershell
git clone https://github.com/FlorianH-cyper/cocktailwebsite.git
cd cocktailwebsite
pip install -r requirements.txt
python main.py
```

Open http://127.0.0.1:5000, sign up, and start planning.

On first start the app creates its database (`instance/database.db`) and seeds the full cocktail catalog automatically — no API keys or manual setup needed.

For development with auto-reload:

```powershell
$env:FLASK_DEBUG = "1"
python main.py
```

## Deployment

The app runs on Railway as a single service:

- `Procfile` starts Gunicorn
- A volume mounted at `/data` keeps the SQLite database across deploys
- Environment variables: `SECRET_KEY` and `DATABASE_PATH=/data/database.db`
- Every push to `main` deploys automatically

The cocktail catalog ships with the repo (`website/jobs/cocktails_seed.json`) and seeds itself on a fresh database.

## Credits

Cocktail data and images from [TheCocktailDB](https://www.thecocktaildb.com/).
