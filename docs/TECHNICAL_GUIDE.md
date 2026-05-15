# VIP Promotions — Technical Guide

## Architecture

| Layer | Technology |
|-------|-----------|
| Backend | Flask 3.x + SQLAlchemy + Flask-Login |
| Database | SQLite (file: `events.db`) |
| Frontend | Jinja2 templates, dark mobile-first PWA (no JS framework) |
| Email | Gmail SMTP_SSL (port 465) |
| Calendar | Google Calendar API v3 (service account, read-only) |
| QR | `qrcode` + Pillow |
| Server | Gunicorn → Nginx reverse proxy → Certbot SSL |
| Hosting | GCloud VM `skycam-worker-01` (34.154.177.76) |
| Domain | `events.{org}.solstack.es` |
| Port | 5003 (internal), 443 (public via nginx) |

---

## File Structure

```
app.py              — Flask routes (public + admin, role-based)
models.py           — SQLAlchemy models (6 tables + association tables)
config.py           — Configuration (env vars for secrets)
calendar_sync.py    — Google Calendar read-only integration
qr_generator.py    — QR code PNG/base64 generation
email_sender.py    — Gmail SMTP for confirmations + password resets
env.py             — Local environment variables (not committed)
setup_vm.sh        — GCloud VM provisioning script
deploy.ps1         — PowerShell deployment script (SCP to VM)
requirements.txt   — Python dependencies
static/css/style.css — Dark theme CSS
static/js/app.js   — Minimal JS (flash dismiss, hamburger toggle)
static/uploads/    — Logos, posters, QR PNGs
templates/         — Jinja2 templates
  base.html        — Layout with hamburger nav + bottom tabs
  admin/           — All admin panel templates
docs/              — This documentation
```

---

## Database Schema

### `businesses`
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | Auto-increment |
| name | String(200) | Required |
| slug | String(100) | Unique, uppercase 3-letter + 1-digit code (e.g. MAR1) |
| address | String(500) | |
| phone | String(30) | |
| email | String(120) | |
| website | String(200) | |
| google_calendar_id | String(256) | Google Calendar ID for sync |
| logo_filename | String(256) | Stored in static/uploads/ |
| description | Text | |
| is_active | Boolean | Default True |
| created_at | DateTime | Auto-set |

### `admins`
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | Auto-increment |
| username | String(80) | Unique — IS the email address |
| password_hash | String(256) | Werkzeug scrypt hash |
| name | String(120) | Display name |
| email | String(120) | Legacy field (username = email) |
| phone | String(30) | |
| role | String(20) | One of: cashier, event_security, event_manager, owner, global_admin |
| is_active_admin | Boolean | Default True |
| reset_token | String(64) | UUID hex for password reset |
| reset_token_expires | DateTime | Token expiry (1 hour) |
| created_at | DateTime | Auto-set |

### `admin_businesses` (association)
| Column | Type |
|--------|------|
| admin_id | FK → admins.id |
| business_id | FK → businesses.id |

Links Owners to the businesses they manage.

### `events`
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| business_id | FK → businesses.id | Required |
| gcal_event_id | String(256) | Unique, from Google Calendar sync |
| title | String(200) | Required |
| start_time | DateTime | Required |
| end_time | DateTime | Optional (nullable for open-ended) |
| end_time_text | String(100) | e.g. "Til late" when no fixed end |
| location | String(200) | |
| description | Text | |
| price | Float | Per ticket, default 0 |
| max_capacity | Integer | 0 = unlimited |
| includes | String(500) | What's included in price |
| dress_code | String(200) | |
| poster_filename | String(256) | |
| is_active | Boolean | |
| created_at | DateTime | |
| updated_at | DateTime | Auto-updated |

Computed properties: `tickets_reserved`, `tickets_available`, `is_sold_out`, `is_past`

### `event_managers` (association)
| Column | Type |
|--------|------|
| admin_id | FK → admins.id |
| event_id | FK → events.id |

Links staff (event_manager, event_security, cashier roles) to specific events.

### `reservations`
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| event_id | FK → events.id | |
| reference_code | String(8) | Unique, uppercase hex (e.g. A1B2C3D4) |
| name | String(120) | Customer name |
| email | String(120) | Customer email |
| phone | String(30) | Customer phone |
| num_tickets | Integer | Default 1 |
| status | String(20) | pending / paid / cancelled |
| notes | Text | |
| created_at | DateTime | |
| updated_at | DateTime | |
| paid_at | DateTime | Set when marked paid |
| paid_to_admin_id | FK → admins.id | Who processed payment |

### `reservation_logs`
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| reservation_id | FK → reservations.id | |
| action | String(30) | reserved, email_sent, paid, cancelled, scanned_in, ticket_printed |
| admin_id | FK → admins.id | Nullable (public reservations have no admin) |
| notes | String(500) | |
| created_at | DateTime | |

---

## Role Hierarchy

```
global_admin (level 4) — full system access
    └── owner (level 3) — manages assigned businesses
        └── event_manager (level 2) — manages assigned events
            └── event_security (level 1) — scans tickets at door
                └── cashier (level 0) — takes payment at bar
```

**Hierarchical properties** (`is_owner`, `is_event_manager`, etc.) return True for the named role AND all roles above it. Use `role_exact` when you need exact role matching.

| Property | cashier | event_security | event_manager | owner | global_admin |
|----------|---------|----------------|---------------|-------|--------------|
| is_cashier | ✓ | ✓ | ✓ | ✓ | ✓ |
| is_event_security | ✗ | ✓ | ✓ | ✓ | ✓ |
| is_event_manager | ✗ | ✗ | ✓ | ✓ | ✓ |
| is_owner | ✗ | ✗ | ✗ | ✓ | ✓ |
| is_global_admin | ✗ | ✗ | ✗ | ✗ | ✓ |

---

## Authentication

- **Login**: Username (= email) + password. Flask-Login session cookie.
- **Password storage**: Werkzeug `scrypt` hash (`generate_password_hash` / `check_password_hash`).
- **Password reset**: UUID4 hex token, stored in `reset_token` column, expires after 1 hour. Reset link sent via Gmail SMTP.
- **Login redirects**: Event Security → Scan page. Cashier → Reservations page. All others → Dashboard.
- **Username validation**: Server-side regex accepts either alphanumeric or valid email format.

---

## Access Control Decorators

| Decorator | Minimum Role |
|-----------|-------------|
| `@login_required` | Any authenticated user |
| `@owner_or_above` | owner or global_admin (uses `role_exact`) |
| `@global_admin_required` | global_admin only |

**Business/Event access** uses `can_access_business()` and `can_access_event()` methods on Admin model:
- Global admin: access all
- Owner: access their assigned businesses and those businesses' events
- Event manager/security/cashier: access only events they're assigned to via `event_managers` table

---

## Routes

### Public Routes

| Method | URL | Purpose |
|--------|-----|---------|
| GET | `/` | Landing page — lists active businesses |
| GET | `/b/<slug>` | Event listing for a business |
| GET/POST | `/reserve/<event_id>` | Reservation form |
| GET | `/embed/<event_id>` | Embeddable reservation (iframe) |
| GET | `/embed/b/<slug>` | Embeddable event listing (iframe) |

### Admin — Authentication

| Method | URL | Purpose |
|--------|-----|---------|
| GET/POST | `/admin/login` | Login form |
| GET | `/admin/logout` | Logout |
| GET/POST | `/admin/forgot-password` | Request reset link |
| GET/POST | `/admin/reset-password/<token>` | Set new password |

### Admin — Dashboard & Management

| Method | URL | Access | Purpose |
|--------|-----|--------|---------|
| GET | `/admin` | Any auth | Dashboard |
| GET | `/admin/businesses` | global_admin | Business list |
| GET/POST | `/admin/businesses/new` | global_admin | Create business |
| GET/POST | `/admin/businesses/<id>` | global_admin | Edit business |
| GET | `/admin/users` | owner+ | User list |
| GET/POST | `/admin/users/new` | owner+ | Create user |
| GET/POST | `/admin/users/<id>` | owner+ | Edit user |
| GET | `/admin/events` | Any auth | Event list |
| GET/POST | `/admin/events/new` | owner+ | Create event |
| GET | `/admin/events/sync` | owner+ | Google Calendar sync |
| GET/POST | `/admin/events/<id>` | Event access | Event detail + config |
| GET | `/admin/events/<id>/qr` | Event access | Download QR code |
| GET | `/admin/reservations` | Any auth | Reservation list |
| POST | `/admin/reservations/<id>/status` | Event access | Update status |
| GET | `/admin/reservations/<id>/ticket` | Event access | Print ticket |
| GET | `/admin/scan` | Any auth | QR scanner page |
| GET | `/admin/scan/<code>` | Event access | Lookup by reference |
| POST | `/admin/scan/<code>/admit` | Event access | Mark as admitted |
| GET | `/admin/reports` | Any auth | Revenue/ticket stats |

---

## Email System

**Provider**: Gmail SMTP_SSL (port 465)
**Credentials**: Set via environment variables `SMTP_EMAIL` and `SMTP_PASSWORD` (app password).

Two email types:
1. **Reservation confirmation** — sent to customer after booking. Contains: reference code, event details, venue, ticket count, total price.
2. **Password reset** — sent to admin user. Contains: reset link button (valid 1 hour).

Both use dark-themed HTML matching the app's visual style.

---

## Google Calendar Integration

- Uses a **service account** (credentials.json file)
- Read-only access (`calendar.readonly` scope)
- Sync triggered manually by Owner/Global Admin via "Sync Calendar" button
- Each business has its own `google_calendar_id`
- Sync fetches up to 50 upcoming events
- Existing events (matched by `gcal_event_id`) are updated; new ones are created
- Event metadata (title, times, location, description) syncs from calendar; business-specific fields (price, capacity, poster, managers) are set in the app

---

## QR Code System

Two QR code types:
1. **Event QR** (`generate_event_qr`) — encodes `/reserve/<event_id>` URL. Downloaded as PNG for printing on posters. Links directly to the public reservation form.
2. **Ticket QR** (`generate_reference_qr_base64`) — encodes `/admin/scan/<reference_code>` URL. Shown on the printed ticket after payment. Used by event security for admission scanning.

---

## Deployment

### VM Details
- Instance: `skycam-worker-01` (GCloud, europe-southwest1)
- IP: 34.154.177.76
- OS: Debian/Ubuntu
- User: nhorncastle
- App directory: `/opt/eventmanagement`

### Stack
```
Client → Nginx (port 443, SSL) → Gunicorn (port 5003) → Flask app
```

### Port Registry (all apps on same VM)
| Port | App |
|------|-----|
| 5000 | CostOfLiving |
| 5001 | MyLife |
| 5002 | SkyCamAlexa |
| 5003 | EventManagement |

### Systemd Service
- Unit: `eventmanagement.service`
- 2 Gunicorn workers
- Auto-restart on failure
- Environment: APP_URL, SECRET_KEY, SMTP_EMAIL, SMTP_PASSWORD via env.py

### SSL
- Certbot with nginx plugin
- Auto-renewal via certbot timer
- Domain: events.{org}.solstack.es

### Deployment Process
1. Run `deploy.ps1` on Windows — stages files to `C:\Users\indal\deploy_em\`, SCPs to VM
2. SSH to VM, restart service: `sudo systemctl restart eventmanagement`

---

## Database Migrations

SQLite does not support `ALTER TABLE DROP COLUMN`. Migrations are handled in `init_db()`:
- Check existing columns via `PRAGMA table_info(tablename)`
- Add missing columns with `ALTER TABLE ... ADD COLUMN`
- Never delete the database file — always migrate

---

## Configuration (config.py)

| Setting | Source | Default |
|---------|--------|---------|
| SECRET_KEY | `$SECRET_KEY` env var | `dev-key-change-in-production` |
| SQLALCHEMY_DATABASE_URI | Computed | `sqlite:///events.db` |
| UPLOAD_FOLDER | Computed | `static/uploads/` |
| MAX_CONTENT_LENGTH | Hardcoded | 10 MB |
| GOOGLE_CALENDAR_ID | `$GOOGLE_CALENDAR_ID` env var | (empty) |
| GOOGLE_CREDENTIALS_FILE | Computed | `credentials.json` |
| APP_URL | `$APP_URL` env var | `http://localhost:5000` |
| SMTP_SERVER | Hardcoded | `smtp.gmail.com` |
| SMTP_PORT | Hardcoded | 465 |
| SMTP_EMAIL | `$SMTP_EMAIL` env var | (empty) |
| SMTP_PASSWORD | `$SMTP_PASSWORD` env var | (empty) |

---

## Security Notes

- Passwords hashed with Werkzeug scrypt (not plaintext, not MD5)
- Password reset tokens are single-use (cleared after use) and time-limited (1 hour)
- Role checks on every admin route via decorators + model methods
- File uploads validated by extension whitelist (png, jpg, jpeg, gif, webp)
- Filenames sanitized via `secure_filename()`
- CSRF protection via Flask's session-based approach
- SQL injection prevented by SQLAlchemy ORM (no raw SQL with user input)
- Upload size capped at 10 MB
