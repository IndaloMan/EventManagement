# VIP Promotions — UI/UX Style Guide

This document defines every visual and behavioural convention used in this application.
Copy it verbatim to a new app and it will match this one exactly.

---

## 1. Stack

- **Backend:** Flask + Jinja2
- **Frontend:** Pure HTML/CSS/JS — no frameworks, no build step
- **Type:** Dark mobile-first PWA

---

## 2. Colour Tokens

Defined in `:root` in `style.css`. Use these variables everywhere — never hardcode colours.

| Variable | Hex | Purpose |
|---|---|---|
| `--bg` | `#0d0d0d` | Page background |
| `--surface` | `#1c1c1e` | Card / form group background |
| `--surface2` | `#2c2c2e` | Table header background |
| `--accent` | `#0a84ff` | Primary blue — links, active tabs, primary action |
| `--accent2` | `#30d158` | Green — success, paid status, create actions |
| `--danger` | `#ff453a` | Red — destructive actions, cancelled status |
| `--warning` | `#ff9f0a` | Amber — pending status, caution |
| `--text` | `#ffffff` | Primary text |
| `--text2` | `#ffffff` | Secondary text (currently same as text) |
| `--text3` | `#ffffff` | Muted/meta text (currently same as text) |
| `--border` | `#38383a` | Dividers, card borders, input borders |
| `--tab-h` | `56px` | Bottom tab bar height |
| `--safe-bottom` | `env(safe-area-inset-bottom, 0px)` | iPhone home bar notch |

---

## 3. Typography

```css
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
-webkit-font-smoothing: antialiased;
```

| Element | Size | Weight | Notes |
|---|---|---|---|
| App title (h1) | `1.25rem` | 700 | `letter-spacing: -0.3px` |
| Section title | `0.7rem` | 600 | Uppercase, `letter-spacing: 0.8px` |
| Card title | `0.95rem` | 600 | |
| Card meta | `0.85rem` | 400 | Right-aligned, `white-space: nowrap` |
| Field label | `0.75rem` | 600 | Uppercase, `letter-spacing: 0.5px`, `width: 130px` — wide enough to prevent wrapping on two-word labels |
| Field value | `0.95rem` | 400 | |
| Badge | `0.7rem` | 600 | Uppercase |
| Flash message | `0.85rem` | 500 | |
| Tab label | `0.65rem` | 600 | |
| Stat value | `1.8rem` | 700 | |
| Stat label | `0.7rem` | 400 | Uppercase, `letter-spacing: 0.5px` |
| Confirmation ref | `2rem` | 700 | `letter-spacing: 2px` |

---

## 4. Page Layout

The app shell is a full-height flex column: **header → scrollable content → bottom tab bar**.

```
┌─────────────────────────────┐
│  #header  (fixed top)       │
├─────────────────────────────┤
│                             │
│  #content  (flex:1,         │
│             overflow-y:auto)│
│                             │
├─────────────────────────────┤
│  #tabs  (fixed bottom)      │
└─────────────────────────────┘
```

```css
#app { display: flex; flex-direction: column; height: 100dvh; }
#header { padding: 14px 16px; border-bottom: 1px solid var(--border); }
#content { flex: 1; overflow-y: auto; -webkit-overflow-scrolling: touch; padding: 16px; }
#tabs { height: calc(var(--tab-h) + var(--safe-bottom)); padding-bottom: var(--safe-bottom); }
```

---

## 5. Buttons

### Base class — `.btn`

All buttons use `.btn` as the base. Never use `btn-sm` on page-level action buttons.

```css
.btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border: none;
    border-radius: 12px;
    padding: 14px;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: opacity 0.2s;
    text-decoration: none;
    color: var(--text);
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.btn:hover { opacity: 0.85; }
.btn:disabled { opacity: 0.45; cursor: not-allowed; }
```

### Colour variants

| Class | Background | Width | Use for |
|---|---|---|---|
| `.btn-primary` | `var(--accent)` `#0a84ff` | `100%` | Primary action — Add, Look Up, Print |
| `.btn-success` | `var(--accent2)` `#30d158` | `100%` | Creation / main entry — New Event, Scan QR |
| `.btn-danger` | `var(--danger)` `#ff453a` | auto | Destructive — Cancel, Delete |
| `.btn-surface` | `#48484a` | auto | Secondary — Edit, Manage, Download, Sign Out |
| `.btn-back` | `#6E4AC7` | auto | Navigation back — always "Back" or "← Back" |

### Colour logic

- **Green (`btn-success`)** — the single most important positive action on the page (create / enter)
- **Blue (`btn-primary`)** — another positive action when green is taken, or the primary action on a page where creation is not the purpose
- **Purple (`btn-back`)** — navigation back only; used on every screen; distinct so it is instantly recognisable on mobile
- **Grey (`btn-surface`)** — everything else: secondary navigation, admin tools, non-destructive actions
- **Red (`btn-danger`)** — destructive or negative actions only

### Small variant — `.btn-sm`

Reserved **only** for tiny inline table-row action buttons (Paid / Cancel / Ticket / Trail inside data tables). Never use on page-level buttons.

```css
.btn-sm { border-radius: 8px; padding: 7px 14px; font-size: 0.8rem; font-weight: 600; }
```

### Button rows — `.btn-row`

Use for any horizontal group of page-level buttons. Add `style="flex: 1"` to each button for equal widths.

```css
.btn-row { display: flex; gap: 10px; margin-top: 12px; }
```

```html
<div class="btn-row" style="margin-bottom: 16px;">
    <a href="..." class="btn btn-success" style="flex: 1;">New Event</a>
    <a href="..." class="btn btn-back" style="flex: 1;">Back</a>
</div>
```

For a standalone full-width button, use `style="width: 100%"`:

```html
<a href="..." class="btn btn-back" style="width: 100%;">Back</a>
```

### Conditional button in a row

When one button is conditionally hidden, the remaining button still gets `flex: 1` and expands to fill the row:

```html
<div class="btn-row" style="margin-bottom: 16px;">
    {% if can_create %}
    <a href="..." class="btn btn-success" style="flex: 1;">New Event</a>
    {% endif %}
    <a href="..." class="btn btn-back" style="flex: 1;">Back</a>
</div>
```

### Dirty-form Save button

Edit forms start with a muted Save button (`opacity: 0.45`, `btn-surface`). It activates green (`btn-success`, `opacity: 1`) as soon as any field is changed. Add `data-track-changes` to the `<form>` tag — handled automatically by `app.js`.

New record forms do **not** use `data-track-changes` — the Save button starts fully active.

---

## 6. Cards

Collapsed by default (one-line header). Tap to expand. `2px` gap between cards.

```css
.card { background: var(--surface); border-radius: 12px; margin-bottom: 2px; overflow: hidden; }
.card.expanded { border: 1px solid var(--border); }
.card-body { display: none; padding: 0 14px 14px; }
.card.expanded .card-body { display: block; }
.card.expanded .card-chevron { transform: rotate(90deg); }
```

```html
<div class="card" onclick="this.classList.toggle('expanded')">
    <div class="card-header">
        <span class="card-title">Title</span>
        <span class="card-meta">Meta text</span>
        <span class="card-chevron">&rsaquo;</span>
    </div>
    <div class="card-body">
        <!-- expanded content + btn-row -->
    </div>
</div>
```

---

## 7. Forms — Field Groups

Forms are grouped visually using `.field-group` containers. Each row is a `.field-row`.

```html
<div class="field-group">
    <p class="field-group-label">Section Name</p>
    <div class="field-row">
        <label for="name">Name <span style="color: var(--danger);">*</span></label>
        <input type="text" id="name" name="name" required>
    </div>
    <div class="field-row">
        <label for="notes">Notes</label>
        <input type="text" id="notes" name="notes" placeholder="Optional">
    </div>
</div>
```

**Mandatory fields:** Red asterisk `<span style="color: var(--danger);">*</span>` after the label text.

**Optional fields:** Show `placeholder="Optional"` on the input — no asterisk.

Field labels are `width: 130px`, uppercase, `0.75rem`. Inputs are `flex: 1`, transparent background, no border. The width must be wide enough to prevent wrapping on two-word labels such as "Publishable Key" or "Webhook Secret".

---

## 8. Section Titles

Used above card lists and major page sections.

```html
<p class="section-title">Upcoming Events</p>
```

```css
.section-title { font-size: 0.7rem; font-weight: 600; text-transform: uppercase;
    color: var(--text); letter-spacing: 0.8px; margin: 20px 0 10px; }
```

---

## 9. Status Badges

```html
<span class="badge badge-pending">Pending</span>
<span class="badge badge-paid">Paid</span>
<span class="badge badge-cancelled">Cancelled</span>
```

```css
.badge { display: inline-block; padding: 3px 10px; border-radius: 20px;
    font-size: 0.7rem; font-weight: 600; text-transform: uppercase; }
.badge-pending  { background: rgba(255,159,10,0.15); color: var(--warning); }
.badge-paid     { background: rgba(48,209,88,0.15);  color: var(--accent2); }
.badge-cancelled{ background: rgba(255,69,58,0.15);  color: var(--danger); }
```

---

## 10. Flash Messages

Displayed at top of `#content`. Auto-dismiss after 5 seconds via `app.js`.

```html
<div class="flash flash-success">Record saved.</div>
<div class="flash flash-error">Something went wrong.</div>
```

```css
.flash { padding: 12px 14px; border-radius: 10px; margin-bottom: 12px;
    font-size: 0.85rem; font-weight: 500; }
.flash-success { background: rgba(48,209,88,0.15); color: var(--accent2); }
.flash-error   { background: rgba(255,69,58,0.15); color: var(--danger); }
```

In Flask, inject via `{% with messages = get_flashed_messages(with_categories=true) %}`.

---

## 11. Stat Cards

Used on Dashboard and Report pages.

```html
<div class="stat-grid">
    <div class="stat-card">
        <div class="stat-value">12</div>
        <div class="stat-label">Upcoming Events</div>
    </div>
</div>
```

```css
.stat-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-bottom: 16px; }
.stat-card { background: var(--surface); border-radius: 12px; padding: 16px; text-align: center; }
.stat-value { font-size: 1.8rem; font-weight: 700; color: var(--accent); }
.stat-label { font-size: 0.7rem; color: var(--text3); text-transform: uppercase;
    letter-spacing: 0.5px; margin-top: 4px; }
```

---

## 12. Admin Data Table — `.admin-table`

Used for sortable data lists (reservations, audit trails).

```css
.admin-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
.admin-table th { text-align: left; padding: 10px 8px; font-size: 0.7rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid var(--border); }
.admin-table td { padding: 10px 8px; border-bottom: 1px solid var(--border); color: var(--text2); }
.admin-table tr:last-child td { border-bottom: none; }
```

Wrap in a `.field-group` with `overflow-x: auto` for horizontal scroll on mobile.

---

## 13. Bottom Tab Navigation

Visible on desktop only. Hidden on mobile (≤768px) — replaced by hamburger menu.

Each tab: icon (22×22 SVG) + label. Active tab uses `var(--accent)`.

```html
<nav id="tabs">
    <a href="/admin" class="tab {% if request.endpoint == 'admin_dashboard' %}active{% endif %}">
        <svg ...></svg>
        <span>Dashboard</span>
    </a>
</nav>
```

```css
.tab { flex: 1; display: flex; flex-direction: column; align-items: center;
    justify-content: center; gap: 3px; font-size: 0.65rem; font-weight: 600; padding: 6px 0; }
.tab.active { color: var(--accent); }
```

---

## 14. Hamburger Menu (Mobile ≤768px)

Shown in the header right side when authenticated. Drops down from top-right. Role-based links. Labels uppercase.

```html
<button class="nav-hamburger" id="navToggle">
    <span></span><span></span><span></span>
</button>
<ul class="nav-links" id="navLinks">
    <li><a href="/admin/events">Events</a></li>
</ul>
```

```js
document.getElementById('navToggle').addEventListener('click', function() {
    document.getElementById('navLinks').classList.toggle('open');
});
```

Properties: `position: absolute`, `top: 56px`, `right: 0`, `width: max-content`, `min-width: 160px`, `border-radius: 0 0 0 10px`, `box-shadow: 0 4px 12px rgba(0,0,0,0.5)`.

---

## 15. Spinner

```html
<span class="spinner"></span>
```

```css
.spinner { width: 16px; height: 16px; border: 2px solid rgba(255,255,255,.3);
    border-top-color: #fff; border-radius: 50%; animation: spin .6s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
```

---

## 16. Embed Mode

When the page is embedded in an iframe (e.g. on a business website), add class `embed-mode` to `<body>`. This hides the header and tab bar, and makes content fill the full viewport.

```css
.embed-mode #header, .embed-mode #tabs { display: none; }
.embed-mode #content { height: 100dvh; }
```

---

## 17. Login Page

```html
<div class="login-container">
    <p class="login-title">App Name</p>
    <div class="field-group"> ... </div>
    <button class="btn btn-primary">Sign In</button>
</div>
```

```css
.login-container { max-width: 360px; margin: 60px auto; }
.login-title { font-size: 1.5rem; font-weight: 700; text-align: center; margin-bottom: 24px; }
```

---

## 18. Date Formats

| Context | Format | Example |
|---|---|---|
| Short (card meta, table) | `'%a %d %b %Y'` | Sat 13 Jun 2026 |
| Short with time (tables) | `'%d %b %Y %H:%M'` | 13 Jun 2026 14:00 |
| Full (expanded/detail views) | `'%A %d %B %Y, %H:%M'` | Saturday 13 June 2026, 14:00 |

---

## 19. JavaScript Behaviours (`app.js`)

Two behaviours are always active — include `app.js` on every page.

### Flash auto-dismiss
All `.flash` elements fade out and are removed after 5 seconds.

### Dirty form tracking
Add `data-track-changes` to any edit form. The submit button:
- Starts muted: `opacity: 0.45`, class `btn-surface`
- Activates on first field change: `opacity: 1`, class switches to `btn-success`
- `beforeunload` warning fires if the user tries to navigate away with unsaved changes

```html
<form method="POST" data-track-changes>
    ...
    <button type="submit" class="btn btn-surface" style="flex: 1;">Save</button>
</form>
```

Do **not** add `data-track-changes` to new-record forms — the save button should start fully active.

---

## 20. Poster / Image Upload Zone

```html
<div class="poster-zone" id="posterZone">
    <span>Tap to upload image</span>
    <input type="file" id="posterInput" accept="image/*" hidden>
</div>
```

```css
.poster-zone { border: 2px dashed var(--border); border-radius: 16px; min-height: 140px;
    display: flex; align-items: center; justify-content: center; cursor: pointer;
    color: var(--text3); font-size: 0.85rem; transition: border-color 0.2s; }
.poster-zone:hover { border-color: var(--accent); }
.poster-zone.has-image { border-style: solid; border-color: var(--accent); }
.poster-zone img { max-width: 100%; border-radius: 14px; }
```

---

## 21. PWA Manifest & Meta Tags

Required in `<head>` for PWA behaviour and iPhone status bar:

```html
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="theme-color" content="#0d0d0d">
<link rel="manifest" href="/manifest.json">
```

---

## 22. CSS Reset

Applied globally before all other rules:

```css
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
```
