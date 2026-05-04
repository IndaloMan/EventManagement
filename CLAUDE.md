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
- `admins` — username, password_hash, name, email, phone, role (global_admin/owner/event_manager)
- `admin_businesses` — links owners to businesses
- `events` — business_id, gcal_event_id, title, dates, price, capacity, includes, dress_code, poster
- `event_managers` — links event managers to events
- `reservations` — event_id, reference_code, name, email, phone, num_tickets, status (pending/paid/cancelled)

## Key URLs
| URL | Purpose |
|---|---|
| `/b/<slug>` | Public event listing for a business |
| `/reserve/<event_id>` | Public reservation form (QR target) |
| `/embed/b/<slug>` | Embeddable event listing (no header/nav) |
| `/embed/<event_id>` | Embeddable reservation form |
| `/admin` | Admin dashboard |
| `/admin/businesses` | Business CRUD (global admin only) |
| `/admin/users` | User management (global admin + owner) |
| `/admin/events` | Event list + sync |
| `/admin/events/<id>` | Event config + reservations + manager assignment |
| `/admin/reservations` | All reservations (filterable by event/status) |
| `/admin/reports` | Revenue and ticket stats per event |

## File Structure
```
app.py              — Flask routes (public + admin, role-based access)
models.py           — SQLAlchemy models (6 tables)
config.py           — Configuration (DB path, upload folder, calendar ID)
calendar_sync.py    — Google Calendar API read-only integration
qr_generator.py     — QR code PNG generation per event
requirements.txt    — Flask, SQLAlchemy, Flask-Login, MSAL, google-api, qrcode, Pillow, gunicorn
static/css/style.css — Dark PWA theme (standard UI spec)
static/js/app.js    — Minimal JS (flash auto-dismiss)
static/manifest.json — PWA manifest
templates/          — Jinja2 templates (base, public pages, admin pages)
```

## Current Status (4 May 2026)
- Project scaffolding complete — all routes, models, templates built
- Git repo: https://github.com/IndaloMan/EventManagement (private)
- NOT YET DONE: local testing, Google Calendar service account setup, GCloud deployment
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
