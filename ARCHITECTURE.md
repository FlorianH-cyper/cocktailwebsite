# Mixly – Architecture

Mixly is a party-planning web app: create a party, pick cocktails from a catalog of 633 drinks, and get an automatically aggregated shopping list.

It is built as a classic **server-rendered Flask monolith** — one process serves the HTML pages, the JSON endpoints, and the static assets, backed by a single SQLite database.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| ORM / Database | Flask-SQLAlchemy, SQLite |
| Authentication | Flask-Login (session cookies) |
| Frontend | Jinja2 templates, vanilla JavaScript, custom CSS |
| Production server | Gunicorn |
| Hosting | Railway (single service + persistent volume) |

## Project Structure

```
cocktailWebsite_new/
├── main.py                     # Entry point: creates the app, runs dev server
├── Procfile                    # Production start command (gunicorn)
├── requirements.txt            # Python dependencies
└── website/
    ├── __init__.py             # App factory: config, DB init, blueprints, seeding
    ├── models.py               # SQLAlchemy models
    ├── views.py                # Main routes (parties, search, JSON APIs)
    ├── auth.py                 # Login / sign-up / logout
    ├── rate_limit.py           # In-memory rate limiting for auth endpoints
    ├── seed.py                 # Fills cocktail table on first start
    ├── utils/                  # Shopping list aggregation helpers
    ├── jobs/
    │   ├── cocktails_seed.json # Bundled cocktail catalog (633 drinks)
    │   ├── export_cocktails_seed.py  # Regenerates the seed file from a local DB
    │   └── ...                 # Original RapidAPI import scripts (one-off)
    ├── templates/              # Jinja2 HTML pages
    └── static/                 # index.js + styles.css
```

## Application Flow

```mermaid
flowchart LR
    Browser[Browser]
    subgraph flaskApp [Flask App]
        Auth[auth.py - login and signup]
        Views[views.py - pages and JSON APIs]
        Templates[Jinja2 templates]
        Static[static JS and CSS]
    end
    DB[(SQLite database.db)]

    Browser -->|HTTP requests| Auth
    Browser -->|HTTP requests| Views
    Views --> Templates
    Views --> DB
    Auth --> DB
    Browser -->|loads| Static
```

- **Pages** (`/`, `/cocktailsearch`, `/partydetails`, `/login`, `/sign-up`) are rendered server-side with Jinja2.
- **JSON endpoints** (`/add-cocktail-to-party`, `/delete-party`, `/delete-menu-item`, `/api/cocktails`, `/api/cocktails/<id>/rate`) are called from `static/index.js` via `fetch`.
- **Auth** uses Flask-Login session cookies; all main pages require login. Passwords are hashed with Werkzeug (`pbkdf2`/`scrypt`); legacy plaintext passwords still work at login and are re-hashed automatically. Login and sign-up POSTs are rate-limited to **5 attempts per IP per 5 minutes** (in-memory, per process).

## Data Model

```mermaid
erDiagram
    USER ||--o{ PARTY : owns
    USER ||--o{ RATING : gives
    PARTY ||--o{ MENUITEM : contains
    COCKTAIL ||--o{ MENUITEM : "is referenced by"
    COCKTAIL ||--o{ RATING : receives
    MENUITEM ||--o{ SHOPPINGLISTITEM : generates

    USER {
        int id
        string email
        string password_hash
        string first_name
    }
    PARTY {
        int id
        string name
        int number_of_participants
        int drinks_per_participant
    }
    MENUITEM {
        int id
        int amount
    }
    COCKTAIL {
        int id
        string name
        string category
        string ingredients_1_to_15
        string measures_1_to_15
    }
    RATING {
        int id
        int user_id
        int cocktail_id
        int stars
    }
    SHOPPINGLISTITEM {
        int id
        string ingredient
        string measure
    }
```

- `Cocktail` stores up to 15 ingredient/measure pairs as flat columns (mirrors TheCocktailDB API shape).
- `Rating` stores one 1–5 star vote per user per cocktail (`unique_user_cocktail_rating`); averages are computed in `utils/` and rounded to one decimal.
- When a cocktail is added to a party, `Shoppinglistitem` rows are created per ingredient; `utils/` aggregates them into the shopping list shown on the party details page.

## Authentication Security

- **Password hashing** — `User.set_password()` uses Werkzeug `generate_password_hash`; `check_password()` verifies hashes and still accepts legacy plaintext rows. On successful login, `upgrade_password_if_legacy()` re-hashes plaintext passwords in place.
- **Rate limiting** — `rate_limit.py` tracks POST attempts per endpoint and client IP in process memory. The `@rate_limit_auth` decorator on `/login` and `/sign-up` blocks further POSTs after 5 attempts within 5 minutes and shows a flash message. Counters reset on app restart and are not shared across Gunicorn workers.

## Star Ratings

Users can rate cocktails on `/cocktailsearch`:

- **UI** — each search result shows the community average (e.g. `★ 4.2 · 3 ratings`) and clickable 1–5 star buttons; the recipe modal (`base.html`) shows the same summary and stars.
- **API** — `POST /api/cocktails/<id>/rate` with JSON `{"stars": 1-5}` upserts the current user's rating and returns `{avg, count, user_stars}`. Live search results from `GET /api/cocktails` include the same fields.
- **Rules** — one rating per user per cocktail; submitting again updates the existing row. Stars must be integers 1–5 (enforced in the model and view).

## Configuration

All environment-specific settings come from environment variables, with safe local defaults:

| Variable | Local default | Production (Railway) |
|---|---|---|
| `SECRET_KEY` | `dev-only-fallback` | Random 64-char hex secret |
| `DATABASE_PATH` | `instance/database.db` | `/data/database.db` (volume) |
| `FLASK_DEBUG` | unset (off) | never set |

## Cocktail Seeding

The cocktail catalog was originally imported from TheCocktailDB (RapidAPI) by the scripts in `website/jobs/`. Since the API key is no longer needed at runtime, the catalog now ships with the repo:

1. `website/jobs/cocktails_seed.json` contains all 633 cocktails.
2. On every app start, `website/seed.py` checks whether the `cocktail` table is empty.
3. If empty (fresh database/volume), it loads the JSON and inserts all rows. Otherwise it does nothing.

This makes deployments self-contained: a brand-new environment gets the full catalog automatically, with no external API dependency.

## Deployment (Railway)

```mermaid
flowchart LR
    Dev[Local machine] -->|git push| GitHub[GitHub repo]
    GitHub -->|auto deploy| Railway

    subgraph Railway [Railway service]
        Gunicorn[Gunicorn] --> App[Flask app]
        App --> Volume[("Volume mounted at /data<br/>database.db")]
    end

    Friends[Users] -->|HTTPS| Gunicorn
```

- **One service** runs `gunicorn main:app --bind 0.0.0.0:$PORT` (see `Procfile`).
- **Persistent volume** mounted at `/data` holds the SQLite file, so users, parties, and cocktails survive redeploys and restarts.
- **Deploys** happen automatically on every push to `main`.
- TLS/HTTPS is handled by Railway.

The database files themselves (`*.db`, `instance/`) are excluded from git — only the JSON seed travels with the code.

## Local Development

```powershell
pip install -r requirements.txt
$env:FLASK_DEBUG = "1"   # enables auto-reload
python main.py            # http://127.0.0.1:5000
```

The local database lives in `instance/database.db` and is created (and seeded with cocktails) automatically on first start. New tables and columns are applied via `db.create_all()` on every startup — there is no separate migration step.

## Known Limitations

- **Auth rate limits are in-memory** — counters reset on restart and are per-process, so limits are weaker under multiple Gunicorn workers.
- SQLite handles one writer at a time — fine at friends-scale, would need PostgreSQL for serious concurrent traffic.