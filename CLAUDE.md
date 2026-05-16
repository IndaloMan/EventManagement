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
All authentication is via SolStack SSO — there are no local user accounts. Roles are assigned in SolStack under the `eventmanagement` app.

| Role | Scope |
|---|---|
| `global_admin` | Full access — all businesses, all events, settings (SolStack platform role) |
| `org_owner` | Full access to everything in the org instance — same as global_admin within EventManagement |
| `staff_manager` | Full access to their business only (scoped by solstack_business_id) |
| `staff_event` | Per-event assignment — can create and manage their assigned events + reservations |
| `staff_security` | Per-event assignment — scan/admit at the door only |
| `staff_bar` | Business-scoped — view all reservations for their business, mark as paid |

`is_full_access` = global_admin, org_owner, staff_manager (full admin panel access)  
`staff_event` and `staff_security` are assigned per-event via the `event_staff` table.  
`staff_bar` is business-scoped only (not per-event).

## Reservation Flow
1. Admin creates event in Google Calendar
2. Admin syncs calendar in the app, sets price/capacity/poster/staff assignments, chooses payment mode (cash / online / both)
3. Admin downloads QR code for the event poster
4. User finds event on business website (iframe) or scans QR on poster
5. User submits reservation (name, phone, optional email, ticket count)
6. **Cash mode:** User receives 8-character reference code, pays at the bar. Staff marks as paid in admin panel.
7. **Stripe mode:** User is redirected to Stripe Checkout after submitting. On success, reservation is automatically marked paid and a paid confirmation email is sent.
8. **Both mode:** User chooses online or at-the-bar at reservation time.

## Database Tables
- `businesses` — name, slug, address, phone, email, website, google_calendar_id, logo, **solstack_business_id** (links to SolStack Business)
- `events` — business_id, gcal_event_id, event_code (6-char unique ID), title, dates, price, capacity, includes, dress_code, poster, terms, is_active, payment_mode (cash/stripe/both)
- `event_staff` — per-event staff assignments: event_id, solstack_user_id, role (staff_event/staff_security), name (snapshot), email
- `reservations` — event_id, reference_code, name, email, phone, num_tickets, status (pending/paid/cancelled), is_comp, stripe_payment_intent_id
- `app_settings` — singleton (id=1): promo_display_name, promo_full_name, promo_description, smtp_email, smtp_password, smtp_from_name, stripe_publishable_key, stripe_secret_key, stripe_webhook_secret
- `reservation_logs` — audit trail: reservation_id, admin_id (SolStack user_id), action, notes, created_at

**Removed tables (post SolStack integration):** `admins`, `admin_businesses`, `event_managers`

## Key URLs
| URL | Purpose |
|---|---|
| `/b/<slug>` | Public event listing for a business |
| `/reserve/<event_id>` | Public reservation form (QR target) |
| `/reservation/<reference_code>` | Guest self-service — view/update/cancel reservation |
| `/embed/b/<slug>` | Embeddable event listing (no header/nav) |
| `/embed/<event_id>` | Embeddable reservation form |
| `/login` | SSO redirect → SolStack login (no local login form) |
| `/admin/login` | SSO redirect (alias) |
| `/auth/callback` | SSO callback — validates SolStack token, creates session |
| `/admin/logout` | Clears session, redirects to SolStack logout |
| `/admin` | Admin dashboard |
| `/admin/businesses` | Business CRUD (full_access only) |
| `/admin/events` | Event list + sync |
| `/admin/events/<id>` | Event config + reservations + staff assignment |
| `/admin/events/<id>/staff/add` | Add staff_event or staff_security to event |
| `/admin/events/<id>/staff/remove/<staff_id>` | Remove staff from event |
| `/admin/events/new` | Create manual event (no GCal required) |
| `/admin/reservations` | All reservations (filterable by event/status) |
| `/admin/reservations/<id>` | Reservation detail + audit trail |
| `/admin/reports` | Revenue and ticket stats per event |
| `/admin/scan` | QR scan entry point |
| `/admin/scan/<reference_code>` | Scan result — pay / comp / admit / cancel |
| `/admin/settings` | App name + SMTP email settings (full_access+) |
| `/admin/maintenance` | DB maintenance tools (full_access only) |
| `/stripe/checkout/<reference_code>` | Create Stripe Checkout session for a reservation |
| `/stripe/success` | Stripe payment success landing — marks reservation paid |
| `/stripe/cancel` | Stripe payment cancel landing — returns user to reservation |
| `/stripe/webhook` | Stripe webhook endpoint — handles async payment events |

**Removed URLs (post SolStack integration):** `/admin/users`, `/admin/users/new`, `/admin/users/<id>/edit`, `/admin/forgot-password`, `/admin/reset-password/<token>`

## File Structure
```
app.py              — Flask routes (public + admin, role-based access)
models.py           — SQLAlchemy models (8 tables)
config.py           — Configuration (DB path, upload folder, calendar ID)
calendar_sync.py    — Google Calendar API read-only integration
qr_generator.py     — QR code PNG generation per event
email_sender.py     — Gmail SMTP: confirmation, cancellation, password reset emails
requirements.txt    — Flask, SQLAlchemy, Flask-Login, google-api, qrcode, Pillow, gunicorn, stripe
static/css/style.css — Dark PWA theme (standard UI spec)
static/js/app.js    — Minimal JS (flash auto-dismiss, dirty form tracking)
templates/base.html — App shell: header, hamburger nav, bottom tab nav
templates/          — Jinja2 templates (base, public pages, admin pages)
```

## Key Behaviours
- **SSO auth:** `_validate_auth_token()` reads `solstack.db` directly to validate one-use 5-minute TTL tokens. `SessionUser` rebuilt from Flask session on each request (no local DB query). `APP_SLUG = 'eventmanagement'`.
- **Scoping:** `_get_scoped_business()` returns None for full_access roles (no filter), or the business matching `session['business_id']` for business-scoped roles. `_get_accessible_events()` returns all events in scope, or only EventStaff-assigned events for staff_event/staff_security.
- **Audit trail names:** `admin_id` on `reservation_logs` stores SolStack user_id (integer). Templates use a `staff_names = {id: name}` dict passed from the route handler via `_get_solstack_users_for_app()`.
- **Euro formatting:** `fmt_eur` Jinja2 filter — strips trailing zeros (35.0 → 35, 35.5 → 35.5)
- **Comp tickets:** `is_comp=True` on a reservation excludes it from revenue reports; requires `is_full_access` to apply
- **Dirty form tracking:** Edit forms show muted Save button until a field changes; `beforeunload` warning on unsaved changes
- **Hamburger menu:** Mobile only (≤768px), right-anchored, auto-width to content, UPPERCASE labels
- **App name:** Configurable via `/admin/settings` — stored in `app_settings`, injected globally via context processor
- **Event codes:** 6-character unique identifier (e.g. `A3F9C2`) auto-generated per event; displayed read-only on event form
- **Stripe payments:** Optional per-event — `payment_mode` = `cash` (default), `stripe` (online only), or `both` (guest chooses). Stripe keys configured in `/admin/settings`. On success, reservation auto-marked paid and paid-specific confirmation email sent. Webhook at `/stripe/webhook` handles async confirmation.

## Current Status (14 May 2026)
- SolStack SSO integration complete — all local auth removed, SessionUser pattern implemented
- App starts cleanly, DB migration runs on startup (legacy tables dropped, new columns/tables added)
- **NOT YET TESTED:** End-to-end SSO flow, role-scoping per role, event staff assignment UI — see `docs/PLAN_SSO_INTEGRATION.md`
- Git repo: https://github.com/IndaloMan/EventManagement (private)
- NOT YET DONE: Google Calendar service account setup, GCloud deployment
- Stripe payments implemented — requires Stripe keys configured in settings before use
- No default admin — login requires SolStack SSO; start SolStack on http://localhost:5004 first

## Businesses (known)
1. Marina Club Gastrobar — marinaclub.es — Google Calendar: "Marina Club Events"
2. Torre Bahia Lounge — website TBD
3. Third venue — TBD (2027)

## Run Locally
```
pip install -r requirements.txt
python app.py
```
Opens on http://localhost:5000 — creates `events.db` and migrates schema on first run.  
**Requires SolStack running on http://localhost:5004** — all admin login goes through SolStack SSO.  
Set `SOLSTACK_DB_PATH` env var if SolStack is not at `../SolStack/solstack.db`.

## Branches
| Branch | Purpose |
|---|---|
| `master` | Stable, deployable at all times |
| `feature/spanish-language` | English/Spanish public UI translation (in progress) |
| `feature/stripe-payments` | Optional Stripe online payment per event (merged into master) |

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
