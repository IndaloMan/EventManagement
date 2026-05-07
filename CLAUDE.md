# EventManagement — Project Guide

## Overview
Multi-business event ticket reservation system for Marina Club Gastrobar, Torre Bahia Lounge, and future venues. Flask app hosted on GCloud, embedded via iframe on each business's GoDaddy website builder site. Events sourced from Google Calendar, tickets reserved online, paid at the venue bar.

## Architecture
- **Backend:** Flask + SQLAlchemy + SQLite (on GCloud VM)
- **Frontend:** Dark mobile-first PWA (standard UI spec from CLAUDE.md global instructions)
- **Google Calendar:** Read-only sync via service account — each business has its own calendar
- **Embed:** Each business site embeds `/embed/b/<slug>` or `/b/<slug>` via iframe
- **QR Codes:** Generated per event, placed on printed posters, links to `/reserve/EVENT_ID`

## User Roles
| Role | Scope |
|---|---|
| Global Admin (IndaloMan) | Full access — all businesses, users, events, settings |
| Owner | Manages their businesses, assigns event managers to events |
| Event Manager | Manages reservations for assigned events only (can span multiple businesses) |
| Event Security | Scan-only access — admit paid tickets at the door |
| Cashier | Reservations list + mark as paid at the bar |

## Reservation Flow
1. Admin creates event in Google Calendar
2. Admin syncs calendar in the app, sets price/capacity/poster/managers
3. Admin downloads QR code for the event poster
4. User finds event on business website (iframe) or scans QR on poster
5. User submits reservation (name, phone, optional email, ticket count)
6. User receives 8-character reference code
7. User goes to venue, pays at the bar
8. Staff marks reservation as "paid" in admin panel

## Database Tables
- `businesses` — name, slug, address, phone, email, website, google_calendar_id, logo
- `admins` — username, password_hash, name, email, phone, role (global_admin/owner/event_manager/event_security/cashier)
- `admin_businesses` — links owners to businesses
- `events` — business_id, gcal_event_id, event_code (6-char unique ID), title, dates, price, capacity, includes, dress_code, poster, terms, is_active
- `event_managers` — links event managers to events
- `reservations` — event_id, reference_code, name, email, phone, num_tickets, status (pending/paid/cancelled), is_comp
- `app_settings` — singleton (id=1): promo_display_name, promo_full_name, promo_description, smtp_email, smtp_password, smtp_from_name
- `reservation_logs` — audit trail: reservation_id, admin_id, action, notes, created_at

## Key URLs
| URL | Purpose |
|---|---|
| `/b/<slug>` | Public event listing for a business |
| `/reserve/<event_id>` | Public reservation form (QR target) |
| `/reservation/<reference_code>` | Guest self-service — view/update/cancel reservation |
| `/embed/b/<slug>` | Embeddable event listing (no header/nav) |
| `/embed/<event_id>` | Embeddable reservation form |
| `/admin` | Admin dashboard |
| `/admin/businesses` | Business CRUD (global admin only) |
| `/admin/users` | User management (global admin + owner) |
| `/admin/events` | Event list + sync |
| `/admin/events/<id>` | Event config + reservations + manager assignment |
| `/admin/events/new` | Create manual event (no GCal required) |
| `/admin/reservations` | All reservations (filterable by event/status) |
| `/admin/reservations/<id>` | Reservation detail + audit trail |
| `/admin/reports` | Revenue and ticket stats per event |
| `/admin/scan` | QR scan entry point |
| `/admin/scan/<reference_code>` | Scan result — pay / comp / admit / cancel |
| `/admin/settings` | App name + SMTP email settings (owner+) |
| `/admin/maintenance` | DB maintenance tools (global admin only) |

## File Structure
```
app.py              — Flask routes (public + admin, role-based access)
models.py           — SQLAlchemy models (8 tables)
config.py           — Configuration (DB path, upload folder, calendar ID)
calendar_sync.py    — Google Calendar API read-only integration
qr_generator.py     — QR code PNG generation per event
email_sender.py     — Gmail SMTP: confirmation, cancellation, password reset emails
requirements.txt    — Flask, SQLAlchemy, Flask-Login, google-api, qrcode, Pillow, gunicorn
static/css/style.css — Dark PWA theme (standard UI spec)
static/js/app.js    — Minimal JS (flash auto-dismiss, dirty form tracking)
templates/base.html — App shell: header, hamburger nav, bottom tab nav
templates/          — Jinja2 templates (base, public pages, admin pages)
```

## Key Behaviours
- **Euro formatting:** `fmt_eur` Jinja2 filter — strips trailing zeros (35.0 → 35, 35.5 → 35.5)
- **Comp tickets:** `is_comp=True` on a reservation excludes it from revenue reports; requires event_manager role to apply
- **Audit trail:** Every status change on a reservation is logged to `reservation_logs` with admin and timestamp
- **Dirty form tracking:** Edit forms show muted Save button until a field changes; `beforeunload` warning on unsaved changes
- **Hamburger menu:** Mobile only (≤768px), right-anchored, auto-width to content, UPPERCASE labels
- **App name:** Configurable via `/admin/settings` — stored in `app_settings`, injected globally via context processor
- **Event codes:** 6-character unique identifier (e.g. `A3F9C2`) auto-generated per event; displayed read-only on event form

## Current Status (6 May 2026)
- Fully functional and tested locally
- Git repo: https://github.com/IndaloMan/EventManagement (private)
- NOT YET DONE: Google Calendar service account setup, GCloud deployment
- Default admin: username `admin`, password `changeme` (created on first run)

## Businesses (known)
1. Marina Club Gastrobar — marinaclub.es — Google Calendar: "Marina Club Events"
2. Torre Bahia Lounge — website TBD
3. Third venue — TBD (2027)

## Run Locally
```
pip install -r requirements.txt
python app.py
```
Opens on http://localhost:5000 — creates `events.db` and default admin on first run.

## Branches
| Branch | Purpose |
|---|---|
| `master` | Stable, deployable at all times |
| `feature/spanish-language` | English/Spanish public UI translation (in progress) |

## Reverting the Spanish Language Change
If the language feature needs to be abandoned, from any state:

**Option 1 — Abandon the branch entirely (no merge has happened):**
```
git checkout master
git branch -D feature/spanish-language
```
Master is untouched. No further action needed.

**Option 2 — Already merged to master by mistake:**
Find the last good commit (before the merge):
```
git log --oneline master
```
Then reset master to that commit (replace `<hash>` with the commit hash):
```
git checkout master
git revert -m 1 <merge-commit-hash>
```
This creates a new revert commit rather than rewriting history — safe if the repo has been pushed to GitHub.

**Option 3 — Nuclear option (local only, not yet pushed):**
```
git checkout master
git reset --hard <last-good-commit-hash>
```
Only use this if the bad merge has NOT been pushed to origin.
