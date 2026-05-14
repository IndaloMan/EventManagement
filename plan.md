# EventManagement — SolStack SSO Integration Test Plan

**Date:** 14 May 2026  
**Purpose:** Verify the SolStack SSO integration is working end-to-end before merging to master.

**Prerequisite:** Both apps are running locally.
- SolStack: http://localhost:5004
- EventManagement: http://localhost:5000

---

## 1. App Startup

**Goal:** Confirm both apps start without errors and the DB migration runs cleanly.

### 1.1 Start EventManagement
```
python app.py
```
**Expected:**
- No import errors or exceptions in the console
- Console shows Flask running on http://localhost:5000
- DB migration runs silently (no errors about missing columns or tables)
- `event_staff` table created (new)
- `solstack_location_id` column added to `businesses` (new)
- `admins`, `admin_businesses`, `event_managers` tables dropped without error

### 1.2 Start SolStack
```
python app.py
```
**Expected:**
- No errors
- Running on http://localhost:5004
- Seed creates `eventmanagement` app entry if not already present

### 1.3 Verify SolStack App Entry
1. Go to http://localhost:5004/admin (log in as global admin)
2. Navigate to Apps
3. Confirm `Event Management` appears with slug `eventmanagement`
4. Confirm available roles include: `staff_event`, `staff_security`, `staff_bar`, `business_manager`, `org_owner`

---

## 2. SSO Redirect Flow

**Goal:** Confirm unauthenticated access to EventManagement admin redirects to SolStack login.

### 2.1 Admin redirect
1. Open a **fresh browser / incognito window** (no existing session)
2. Go to http://localhost:5000/admin
3. **Expected:** Redirected to http://localhost:5004/login?app=eventmanagement&next=http://localhost:5000/auth/callback (or similar)

### 2.2 Login redirect
1. Go to http://localhost:5000/admin/login
2. **Expected:** Same redirect to SolStack login (not a local login form)

### 2.3 Complete SSO login
1. On SolStack login page, log in with your global admin credentials
2. **Expected:** Redirected back to http://localhost:5000/auth/callback, then to http://localhost:5000/admin
3. Dashboard loads without error

### 2.4 Session persistence
1. After logging in, navigate to http://localhost:5000/admin/events
2. **Expected:** Page loads normally — no re-redirect to SolStack

### 2.5 Logout
1. Click Logout in the hamburger menu (or navigate to http://localhost:5000/admin/logout)
2. **Expected:** Session cleared, redirected to SolStack logout page (or SolStack login)
3. Navigate to http://localhost:5000/admin — **Expected:** redirected to SolStack login again

---

## 3. Role: global_admin / org_owner

**Goal:** Full access to everything — all businesses, all events, all settings.

Log in via SolStack as a user with `global_admin` or `org_owner` role on the `eventmanagement` app.

### 3.1 Navigation
- Go to http://localhost:5000/admin
- **Expected:** Hamburger menu shows: Dashboard, Events, Reservations, Scan, Reports, Settings, Businesses
- Users link must **NOT** appear anywhere

### 3.2 Businesses
- Go to http://localhost:5000/admin/businesses
- **Expected:** All businesses listed (not filtered by location)

### 3.3 Events
- Go to http://localhost:5000/admin/events
- **Expected:** All events across all businesses listed

### 3.4 Event Detail — Staff Assignment
1. Click Manage on any event
2. **Expected:** Event Staff and Security Staff sections visible
3. **Expected:** "Assign Staff" section visible with a dropdown of SolStack users who have the `eventmanagement` role
4. Select a user from the dropdown, select role `Event Staff`, click Add
5. **Expected:** Page reloads, user appears in the Event Staff list
6. Click Remove next to that user
7. **Expected:** User removed from the list

### 3.5 Settings
- Go to http://localhost:5000/admin/settings
- **Expected:** Page loads, SMTP and app name fields visible

### 3.6 Reports
- Go to http://localhost:5000/admin/reports
- **Expected:** Page loads, shows events from all businesses

---

## 4. Role: business_manager

**Goal:** Full access to their location's business only — cannot see other businesses.

Log in via SolStack as a user with `business_manager` role assigned to one specific business location.

### 4.1 Navigation
- Go to http://localhost:5000/admin
- **Expected:** Hamburger menu shows: Dashboard, Events, Reservations, Scan, Reports, Settings
- Businesses link must **NOT** appear (business_manager cannot manage other businesses)

### 4.2 Events scoped to location
- Go to http://localhost:5000/admin/events
- **Expected:** Only events for their assigned business location are listed (not events from other businesses)

### 4.3 Reservations scoped to location
- Go to http://localhost:5000/admin/reservations
- **Expected:** Only reservations for events at their business location

### 4.4 Reports scoped to location
- Go to http://localhost:5000/admin/reports
- **Expected:** Only their location's events in the report

### 4.5 Staff assignment still visible
- Go to an event detail page for their location
- **Expected:** Staff assignment section visible (business_manager has full_access)

---

## 5. Role: staff_event

**Goal:** Can only see and manage events they are explicitly assigned to.

Log in via SolStack as a user with `staff_event` role. Ensure this user is assigned to at least one event (and NOT assigned to at least one other event).

### 5.1 Navigation
- Go to http://localhost:5000/admin
- **Expected:** Hamburger menu shows: Dashboard, Events, Reservations (limited scope)
- Settings, Reports, Businesses must **NOT** appear

### 5.2 Events filtered to assigned only
- Go to http://localhost:5000/admin/events
- **Expected:** Only events where this user has an EventStaff assignment appear
- Events they are NOT assigned to must NOT appear

### 5.3 Reservations filtered to assigned events
- Go to http://localhost:5000/admin/reservations
- **Expected:** Only reservations for their assigned events

### 5.4 Staff assignment section hidden
- Go to the detail page for one of their assigned events
- **Expected:** Event Staff and Security Staff assignment sections are NOT visible (is_full_access required)

### 5.5 New Event button
- Go to http://localhost:5000/admin/events
- **Expected:** "New Event" button IS visible (staff_event can create events — guarded by `is_full_access or is_staff_event`)

---

## 6. Role: staff_security

**Goal:** Scan-only access — admit paid tickets at the door. No reservations or event management.

Log in via SolStack as a user with `staff_security` role.

### 6.1 Navigation
- Go to http://localhost:5000/admin
- **Expected:** Hamburger menu shows Scan only (or minimal items)
- Events, Reservations, Settings, Reports must NOT appear

### 6.2 Scan access
- Go to http://localhost:5000/admin/scan
- **Expected:** QR scan interface loads

### 6.3 Scan a reservation
1. Look up the reference code for a paid reservation
2. Go to http://localhost:5000/admin/scan/REFCODE (replace REFCODE with actual reference)
3. **Expected:** Admit button is visible
4. Click Admit — **Expected:** Reservation marked as admitted/scanned

### 6.4 Cannot mark as paid
- On the scan result page for a pending reservation
- **Expected:** No "Mark as Paid" button (that is staff_bar only)

### 6.5 Cannot comp
- On the scan result page
- **Expected:** No "Comp" button (that is full_access only)

---

## 7. Role: staff_bar

**Goal:** View all reservations for their location, mark as paid. No event management.

Log in via SolStack as a user with `staff_bar` role assigned to a specific location.

### 7.1 Navigation
- Go to http://localhost:5000/admin
- **Expected:** Hamburger menu shows Reservations (and Scan)
- Events, Settings, Reports, Businesses must NOT appear

### 7.2 Reservations scoped to location
- Go to http://localhost:5000/admin/reservations
- **Expected:** All reservations for their location's events (not filtered to specific events — all location events)

### 7.3 Mark as paid
1. Find a pending reservation in the list
2. Click the Paid button or go to the reservation detail
3. **Expected:** Reservation status changes to paid

### 7.4 Cannot manage events
- Go to http://localhost:5000/admin/events
- **Expected:** Either redirected (access denied) or events visible but no management actions

---

## 8. Public Routes — No Login Required

**Goal:** All public-facing routes work for anonymous users.

Log out of EventManagement first (or use incognito).

### 8.1 Business event listing
- Go to http://localhost:5000/b/marinaclub (replace slug with actual business slug)
- **Expected:** Page loads showing upcoming events, no login required

### 8.2 Reservation form
1. Find an active event ID from the events admin page (e.g. `1`)
2. Go to http://localhost:5000/reserve/1
- **Expected:** Reservation form loads, no login required
3. Submit a test reservation (use a test name/phone)
4. **Expected:** Confirmation page with reference code shown

### 8.3 Guest reservation lookup
1. Take the reference code from 8.2
2. Go to http://localhost:5000/reservation/REFCODE
3. **Expected:** Reservation details shown to guest, no login required

### 8.4 Embedded listing
- Go to http://localhost:5000/embed/b/marinaclub (replace slug)
- **Expected:** Event listing loads without header/nav (iframe-safe)

### 8.5 Embedded reservation form
- Go to http://localhost:5000/embed/1 (replace with event ID)
- **Expected:** Reservation form loads without header/nav

---

## 9. DB Migration — Data Integrity

**Goal:** Existing events, reservations, and businesses are all preserved after migration.

### 9.1 Businesses intact
- Go to http://localhost:5000/admin/businesses (log in as full_access user)
- **Expected:** All previously created businesses still present with correct names and slugs

### 9.2 Events intact
- Go to http://localhost:5000/admin/events
- **Expected:** All previously created events still present

### 9.3 Reservations intact
- Go to http://localhost:5000/admin/reservations
- **Expected:** All previously created reservations still present with correct status and reference codes

### 9.4 Legacy tables removed
- Run in SQLite browser or via Flask shell:
  ```
  SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;
  ```
- **Expected tables present:** businesses, events, reservations, reservation_logs, event_staff, app_settings, maintenance, google_calendar_syncs (or similar — all active tables)
- **Expected tables ABSENT:** admins, admin_businesses, event_managers

### 9.5 New columns present
- Inspect `businesses` table schema
- **Expected:** `solstack_location_id` column present (may be NULL for all existing rows — that is correct)

---

## 10. Audit Trail

**Goal:** Audit trail still renders correctly using SolStack user names (not broken Admin references).

### 10.1 Reservation detail audit trail
1. Find a reservation that has been updated (has audit log entries)
2. Go to http://localhost:5000/admin/reservations/ID
3. Scroll to Audit Trail section
4. **Expected:** Action column shows badge, "By" column shows either a name (if admin_id matches a SolStack user) or "—" (for actions taken by the old Admin system)
5. **Expected:** No template errors / crashes

### 10.2 Scan lookup audit trail
1. Go to http://localhost:5000/admin/scan/REFCODE
2. Scroll to audit trail
3. **Expected:** Renders without error, names shown or "—"

### 10.3 Report booking audit trail
1. Go to http://localhost:5000/admin/reports
2. Click through to a booking report for a reservation that has log entries
3. **Expected:** Audit table renders, "By" column shows "—" for old entries (acceptable)

---

## 11. Stripe Flow (if Stripe keys configured)

Only run if Stripe publishable key and secret key are set in Settings.

### 11.1 Online payment reservation
1. Find an event with `payment_mode = stripe` or `both`
2. Go to http://localhost:5000/reserve/EVENT_ID
3. Complete the reservation form — select online payment if prompted
4. **Expected:** Redirected to Stripe Checkout

### 11.2 Payment success
1. Complete payment on Stripe using test card `4242 4242 4242 4242`
2. **Expected:** Redirected to success page, reservation marked as paid
3. Check reservation in admin — **Expected:** status = paid, paid_at timestamp set

---

## Pass / Fail Tracking

| # | Test | Result | Notes |
|---|---|---|---|
| 1.1 | App startup — no errors | | |
| 1.2 | SolStack starts | | |
| 1.3 | SolStack app entry | | |
| 2.1 | Admin redirects to SolStack | | |
| 2.2 | /admin/login redirects | | |
| 2.3 | SSO login completes | | |
| 2.4 | Session persistence | | |
| 2.5 | Logout | | |
| 3.1–3.6 | global_admin full access | | |
| 4.1–4.5 | business_manager scoped access | | |
| 5.1–5.5 | staff_event scoped access | | |
| 6.1–6.5 | staff_security scan only | | |
| 7.1–7.4 | staff_bar reservations access | | |
| 8.1–8.5 | Public routes anonymous | | |
| 9.1–9.5 | DB migration data integrity | | |
| 10.1–10.3 | Audit trail renders | | |
| 11.1–11.2 | Stripe flow (optional) | | |
