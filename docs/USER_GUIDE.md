# VIP Promotions — User Guide

## What is VIP Promotions?

VIP Promotions is a ticket reservation system for venue events. Customers reserve tickets online (or by scanning a QR code on a poster), receive a reference code, then pay at the venue bar. Staff use the admin panel to manage events, process payments, and scan tickets at the door.

**Live URL**: https://events.ego2.net

---

## Roles

There are 5 user roles. Each role includes the permissions of all roles below it.

### Cashier
**Purpose**: Takes payment at the bar and marks reservations as paid.

**Can do**:
- View reservations for assigned events
- Mark reservations as "paid" or "cancelled"
- Print tickets after payment
- View reports for assigned events

**Sees on login**: Bookings page (reservation list)

---

### Event Security
**Purpose**: Scans tickets at the door and admits guests.

**Can do**:
- Everything a Cashier can do
- Scan QR codes / enter reference codes
- Admit guests (mark as scanned in)
- See duplicate scan warnings

**Sees on login**: Scan page (QR scanner)

---

### Event Manager
**Purpose**: Manages the events they are assigned to.

**Can do**:
- Everything Event Security can do
- View Dashboard with event statistics
- Edit event details (price, capacity, poster, dress code, includes)
- Download event QR codes for posters
- View all reservations across assigned events
- View revenue reports

**Cannot do**: Create new events, sync calendar, manage users, manage businesses.

---

### Owner
**Purpose**: Manages their business(es) and all staff/events within them.

**Can do**:
- Everything Event Manager can do
- Create new events (manually or via Google Calendar sync)
- Sync events from Google Calendar
- Create and edit users (Cashier, Event Security, Event Manager roles)
- Assign staff to events
- Access all events across their assigned businesses

**Cannot do**: Create businesses, manage other owners, manage global admins.

---

### Global Admin
**Purpose**: Full system control across all businesses.

**Can do**:
- Everything Owner can do
- Create and manage businesses (venues)
- Create and edit ALL user roles (including Owner and Global Admin)
- Access all events across all businesses
- Full system configuration

---

## How to Log In

1. Go to https://events.ego2.net/admin/login
2. Enter your email address in the "User" field
3. Enter your password
4. Click "Sign In"

If you forget your password:
1. Click "Forgotten password?" on the login page
2. Enter your email address
3. Check your inbox for a reset link (valid for 1 hour)
4. Click the link and set a new password

---

## Common Tasks

### Taking Payment (Cashier)

1. Customer arrives at the bar with their reference code
2. Go to **Bookings** tab
3. Find the reservation (filter by event if needed)
4. Click **Mark Paid**
5. A ticket is printed/displayed — give to customer
6. Customer takes ticket to the door

### Scanning Tickets (Event Security)

1. Go to **Scan** tab
2. Either scan the QR code on the customer's ticket, or type the 8-character reference code
3. Check the result:
   - **Green** = Valid, paid ticket. Click **Admit** to let them in.
   - **Orange** = Already scanned (duplicate entry attempt). Shows original scan time.
   - **Red** = Not paid or invalid code.

### Creating an Event (Owner / Global Admin)

**From Google Calendar:**
1. Add the event to the venue's Google Calendar
2. In VIP Promotions, go to **Events** → **Sync Calendar**
3. The event appears in the list
4. Click on it to set: price, capacity, poster image, dress code, inclusions
5. Assign event managers/security/cashiers

**Manually:**
1. Go to **Events** → **New Event**
2. Fill in: business, title, date/time, price, capacity
3. Upload a poster image
4. Save and assign staff

### Downloading a QR Code (for posters)

1. Go to **Events** → click on the event
2. Click **Download QR Code**
3. Print the QR code on your event poster
4. When scanned, it takes customers directly to the reservation form

### Managing Users (Owner / Global Admin)

1. Go to **Users** tab
2. Click **Add User**
3. Enter their email (this is their login username), display name, and a temporary password
4. Select their role
5. Save — tell them their login credentials

**Owners** can create: Cashier, Event Security, Event Manager
**Global Admins** can additionally create: Owner, Global Admin

### Assigning Staff to Events (Owner / Global Admin)

1. Go to **Events** → click on the event
2. Scroll to "Assigned Managers" section
3. Select staff members from the list
4. Save

Staff will only see events they are assigned to (unless they are Owner/Global Admin).

---

## Customer Flow (Public)

1. Customer finds the event on the business website (iframe embed) or scans a QR code on a poster
2. Fills in: name, email, phone, number of tickets
3. Receives an 8-character reference code on screen and by email
4. Goes to the venue on event day
5. Shows reference code at the bar → pays → gets ticket printed
6. Shows ticket at the door → security scans and admits

---

## Navigation

**On desktop**: Bottom tab bar with icons (Dashboard, Events, Bookings, Scan, Reports, Users, Venues, Sign Out — visible tabs depend on your role).

**On mobile**: Hamburger menu (three lines) in the top-right corner. Tap to open the dropdown menu.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Can't log in | Check you're using your email as username. Use "Forgotten password?" if needed. |
| Don't see an event | You may not be assigned to it. Ask your Owner/Admin to assign you. |
| Customer says they reserved but not in list | Check the email — reservation confirmation has the reference code. Search by code. |
| QR scan shows "not paid" | Customer hasn't paid yet. Send them to the bar first. |
| QR scan shows "already scanned" | Duplicate entry attempt. Shows when they were first scanned in. |
