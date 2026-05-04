"""Marina Club Events — multi-business ticket reservation system."""

import os
from functools import wraps
from datetime import datetime
from flask import (Flask, render_template, request, redirect, url_for,
                   flash, send_from_directory, abort)
from flask_login import (LoginManager, login_user, logout_user,
                         login_required, current_user)
from werkzeug.utils import secure_filename
from config import Config
from models import db, Admin, Business, Event, Reservation, event_managers
from calendar_sync import fetch_upcoming_events
from qr_generator import generate_event_qr

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'admin_login'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Admin, int(user_id))


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def global_admin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_global_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated


def owner_or_above(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if current_user.is_event_manager:
            abort(403)
        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# Public routes
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    """Public landing — lists all active businesses."""
    businesses = Business.query.filter_by(is_active=True).all()
    return render_template('index.html', businesses=businesses)


@app.route('/b/<slug>')
def business_events(slug):
    """Public event listing for a specific business."""
    business = Business.query.filter_by(slug=slug, is_active=True).first_or_404()
    events = Event.query.filter(
        Event.business_id == business.id,
        Event.is_active == True,
        Event.start_time >= datetime.utcnow()
    ).order_by(Event.start_time).all()
    return render_template('business_events.html', business=business, events=events)


@app.route('/reserve/<int:event_id>', methods=['GET', 'POST'])
def reserve(event_id):
    """Public reservation form for a specific event."""
    event = db.session.get(Event, event_id)
    if not event or not event.is_active or event.is_past:
        flash('This event is no longer available.', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        num_tickets = int(request.form.get('num_tickets', 1))

        if not name or not phone:
            flash('Name and phone number are required.', 'error')
            return render_template('reserve.html', event=event)

        if num_tickets < 1:
            flash('You must reserve at least 1 ticket.', 'error')
            return render_template('reserve.html', event=event)

        if event.max_capacity > 0:
            available = event.tickets_available
            if available is not None and num_tickets > available:
                flash(f'Only {available} tickets remaining.', 'error')
                return render_template('reserve.html', event=event)

        reservation = Reservation(
            event_id=event.id,
            reference_code=Reservation.generate_reference(),
            name=name,
            email=email,
            phone=phone,
            num_tickets=num_tickets,
            status='pending'
        )
        db.session.add(reservation)
        db.session.commit()

        return render_template('confirmation.html',
                               event=event, reservation=reservation)

    return render_template('reserve.html', event=event)


@app.route('/embed/<int:event_id>')
def embed_event(event_id):
    """Embeddable reservation form (no header/nav) for iframe use."""
    event = db.session.get(Event, event_id)
    if not event or not event.is_active:
        return render_template('embed.html', event=None)
    return render_template('embed.html', event=event)


@app.route('/embed/b/<slug>')
def embed_business(slug):
    """Embeddable event listing for a business (no header/nav) for iframe use."""
    business = Business.query.filter_by(slug=slug, is_active=True).first()
    events = []
    if business:
        events = Event.query.filter(
            Event.business_id == business.id,
            Event.is_active == True,
            Event.start_time >= datetime.utcnow()
        ).order_by(Event.start_time).all()
    return render_template('embed_business.html', business=business, events=events)


# ---------------------------------------------------------------------------
# Admin — authentication
# ---------------------------------------------------------------------------

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            login_user(admin)
            return redirect(url_for('admin_dashboard'))
        flash('Invalid username or password.', 'error')

    return render_template('admin/login.html')


@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for('admin_login'))


# ---------------------------------------------------------------------------
# Admin — dashboard
# ---------------------------------------------------------------------------

@app.route('/admin')
@login_required
def admin_dashboard():
    businesses = current_user.get_accessible_businesses()
    events = current_user.get_accessible_events()
    upcoming = [e for e in events if not e.is_past]
    pending = Reservation.query.filter(
        Reservation.status == 'pending',
        Reservation.event_id.in_([e.id for e in events])
    ).count() if events else 0
    return render_template('admin/dashboard.html',
                           businesses=businesses,
                           upcoming_events=upcoming,
                           pending_count=pending)


# ---------------------------------------------------------------------------
# Admin — business management (global admin only)
# ---------------------------------------------------------------------------

@app.route('/admin/businesses')
@global_admin_required
def admin_businesses():
    businesses = Business.query.order_by(Business.name).all()
    return render_template('admin/businesses.html', businesses=businesses)


@app.route('/admin/businesses/new', methods=['GET', 'POST'])
@global_admin_required
def admin_business_new():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        slug = request.form.get('slug', '').strip().lower().replace(' ', '-')
        if not name or not slug:
            flash('Name and slug are required.', 'error')
            return render_template('admin/business_form.html', business=None)

        if Business.query.filter_by(slug=slug).first():
            flash('That URL slug is already in use.', 'error')
            return render_template('admin/business_form.html', business=None)

        business = Business(
            name=name,
            slug=slug,
            address=request.form.get('address', '').strip(),
            phone=request.form.get('phone', '').strip(),
            email=request.form.get('email', '').strip(),
            website=request.form.get('website', '').strip(),
            google_calendar_id=request.form.get('google_calendar_id', '').strip(),
            description=request.form.get('description', '').strip(),
        )

        logo = request.files.get('logo')
        if logo and logo.filename and allowed_file(logo.filename):
            filename = secure_filename(f"logo_{slug}_{logo.filename}")
            logo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            business.logo_filename = filename

        db.session.add(business)
        db.session.commit()
        flash(f'Business "{name}" created.', 'success')
        return redirect(url_for('admin_businesses'))

    return render_template('admin/business_form.html', business=None)


@app.route('/admin/businesses/<int:biz_id>', methods=['GET', 'POST'])
@global_admin_required
def admin_business_edit(biz_id):
    business = db.session.get(Business, biz_id)
    if not business:
        abort(404)

    if request.method == 'POST':
        business.name = request.form.get('name', '').strip()
        business.address = request.form.get('address', '').strip()
        business.phone = request.form.get('phone', '').strip()
        business.email = request.form.get('email', '').strip()
        business.website = request.form.get('website', '').strip()
        business.google_calendar_id = request.form.get('google_calendar_id', '').strip()
        business.description = request.form.get('description', '').strip()
        business.is_active = 'is_active' in request.form

        logo = request.files.get('logo')
        if logo and logo.filename and allowed_file(logo.filename):
            filename = secure_filename(f"logo_{business.slug}_{logo.filename}")
            logo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            business.logo_filename = filename

        db.session.commit()
        flash('Business updated.', 'success')
        return redirect(url_for('admin_business_edit', biz_id=business.id))

    return render_template('admin/business_form.html', business=business)


# ---------------------------------------------------------------------------
# Admin — user management (global admin + owner)
# ---------------------------------------------------------------------------

@app.route('/admin/users')
@owner_or_above
def admin_users():
    if current_user.is_global_admin:
        users = Admin.query.order_by(Admin.name).all()
    else:
        users = Admin.query.filter(
            Admin.role == 'event_manager'
        ).order_by(Admin.name).all()
    return render_template('admin/users.html', users=users)


@app.route('/admin/users/new', methods=['GET', 'POST'])
@owner_or_above
def admin_user_new():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        name = request.form.get('name', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', 'event_manager')

        if not current_user.is_global_admin:
            role = 'event_manager'

        if not username or not name or not password:
            flash('Username, name and password are required.', 'error')
            return render_template('admin/user_form.html', user=None)

        if Admin.query.filter_by(username=username).first():
            flash('Username already taken.', 'error')
            return render_template('admin/user_form.html', user=None)

        admin = Admin(
            username=username,
            name=name,
            email=request.form.get('email', '').strip(),
            phone=request.form.get('phone', '').strip(),
            role=role,
        )
        admin.set_password(password)

        if role == 'owner':
            biz_ids = request.form.getlist('business_ids')
            for bid in biz_ids:
                biz = db.session.get(Business, int(bid))
                if biz:
                    admin.businesses.append(biz)

        db.session.add(admin)
        db.session.commit()
        flash(f'User "{name}" created.', 'success')
        return redirect(url_for('admin_users'))

    businesses = Business.query.filter_by(is_active=True).all()
    return render_template('admin/user_form.html', user=None, businesses=businesses)


@app.route('/admin/users/<int:user_id>', methods=['GET', 'POST'])
@owner_or_above
def admin_user_edit(user_id):
    user = db.session.get(Admin, user_id)
    if not user:
        abort(404)

    if not current_user.is_global_admin and user.role != 'event_manager':
        abort(403)

    if request.method == 'POST':
        user.name = request.form.get('name', '').strip()
        user.email = request.form.get('email', '').strip()
        user.phone = request.form.get('phone', '').strip()
        user.is_active_admin = 'is_active_admin' in request.form

        if current_user.is_global_admin:
            user.role = request.form.get('role', user.role)
            if user.role == 'owner':
                user.businesses.clear()
                for bid in request.form.getlist('business_ids'):
                    biz = db.session.get(Business, int(bid))
                    if biz:
                        user.businesses.append(biz)

        new_password = request.form.get('password', '').strip()
        if new_password:
            user.set_password(new_password)

        db.session.commit()
        flash('User updated.', 'success')
        return redirect(url_for('admin_users'))

    businesses = Business.query.filter_by(is_active=True).all()
    return render_template('admin/user_form.html', user=user, businesses=businesses)


# ---------------------------------------------------------------------------
# Admin — events
# ---------------------------------------------------------------------------

@app.route('/admin/events')
@login_required
def admin_events():
    events = current_user.get_accessible_events()
    return render_template('admin/events.html', events=events)


@app.route('/admin/events/sync')
@owner_or_above
def admin_sync_events():
    """Sync events from Google Calendar for accessible businesses."""
    businesses = current_user.get_accessible_businesses()
    total_synced = 0

    for business in businesses:
        if not business.google_calendar_id:
            continue
        try:
            gcal_events = fetch_upcoming_events(
                app.config['GOOGLE_CREDENTIALS_FILE'],
                business.google_calendar_id)

            for ge in gcal_events:
                existing = Event.query.filter_by(gcal_event_id=ge['gcal_event_id']).first()
                if existing:
                    existing.title = ge['title']
                    existing.start_time = ge['start_time']
                    existing.end_time = ge['end_time']
                    existing.location = ge['location']
                    existing.description = ge['description']
                else:
                    event = Event(
                        business_id=business.id,
                        gcal_event_id=ge['gcal_event_id'],
                        title=ge['title'],
                        start_time=ge['start_time'],
                        end_time=ge['end_time'],
                        location=ge['location'],
                        description=ge['description'],
                        is_active=True
                    )
                    db.session.add(event)
                    total_synced += 1

            db.session.commit()
        except Exception as e:
            flash(f'Sync failed for {business.name}: {e}', 'error')

    flash(f'Calendar sync complete — {total_synced} new event(s) added.', 'success')
    return redirect(url_for('admin_events'))


@app.route('/admin/events/<int:event_id>', methods=['GET', 'POST'])
@login_required
def admin_event_detail(event_id):
    """Configure event details and manage its reservations."""
    event = db.session.get(Event, event_id)
    if not event:
        abort(404)
    if not current_user.can_access_event(event):
        abort(403)

    if request.method == 'POST':
        if current_user.is_event_manager and event not in current_user.managed_events:
            abort(403)

        event.price = float(request.form.get('price', 0))
        event.max_capacity = int(request.form.get('max_capacity', 0))
        event.includes = request.form.get('includes', '').strip()
        event.dress_code = request.form.get('dress_code', '').strip()
        event.is_active = 'is_active' in request.form

        poster = request.files.get('poster')
        if poster and poster.filename and allowed_file(poster.filename):
            filename = secure_filename(f"event_{event.id}_{poster.filename}")
            poster.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            event.poster_filename = filename

        if not current_user.is_event_manager:
            event.managers.clear()
            for mid in request.form.getlist('manager_ids'):
                mgr = db.session.get(Admin, int(mid))
                if mgr and mgr.is_event_manager:
                    event.managers.append(mgr)

        db.session.commit()
        flash('Event updated.', 'success')
        return redirect(url_for('admin_event_detail', event_id=event.id))

    reservations = Reservation.query.filter_by(event_id=event.id).order_by(
        Reservation.created_at.desc()).all()
    all_managers = Admin.query.filter_by(role='event_manager', is_active_admin=True).all()
    return render_template('admin/event_detail.html',
                           event=event, reservations=reservations,
                           all_managers=all_managers)


@app.route('/admin/events/<int:event_id>/qr')
@login_required
def admin_generate_qr(event_id):
    """Generate and download QR code for an event."""
    event = db.session.get(Event, event_id)
    if not event:
        abort(404)
    if not current_user.can_access_event(event):
        abort(403)

    filename = generate_event_qr(event.id, app.config['APP_URL'],
                                  app.config['UPLOAD_FOLDER'])
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename,
                               as_attachment=True)


# ---------------------------------------------------------------------------
# Admin — reservations
# ---------------------------------------------------------------------------

@app.route('/admin/reservations')
@login_required
def admin_reservations():
    accessible_events = current_user.get_accessible_events()
    event_ids = [e.id for e in accessible_events]

    event_id = request.args.get('event_id', type=int)
    status = request.args.get('status', '')

    query = Reservation.query.filter(Reservation.event_id.in_(event_ids))
    if event_id:
        query = query.filter(Reservation.event_id == event_id)
    if status:
        query = query.filter(Reservation.status == status)

    reservations = query.order_by(Reservation.created_at.desc()).all()
    return render_template('admin/reservations.html',
                           reservations=reservations,
                           events=accessible_events,
                           selected_event=event_id,
                           selected_status=status)


@app.route('/admin/reservations/<int:res_id>/status', methods=['POST'])
@login_required
def admin_update_reservation(res_id):
    reservation = db.session.get(Reservation, res_id)
    if not reservation:
        abort(404)
    if not current_user.can_access_event(reservation.event):
        abort(403)

    new_status = request.form.get('status')
    if new_status in ('pending', 'paid', 'cancelled'):
        reservation.status = new_status
        if new_status == 'paid':
            reservation.paid_at = datetime.utcnow()
            reservation.paid_to_admin_id = current_user.id
        db.session.commit()
        flash(f'Reservation {reservation.reference_code} marked as {new_status}.', 'success')

    return redirect(request.referrer or url_for('admin_reservations'))


# ---------------------------------------------------------------------------
# Admin — reports
# ---------------------------------------------------------------------------

@app.route('/admin/reports')
@login_required
def admin_reports():
    events = current_user.get_accessible_events()
    report_data = []
    for event in events:
        reservations = Reservation.query.filter_by(event_id=event.id).all()
        total_reserved = sum(r.num_tickets for r in reservations if r.status != 'cancelled')
        total_paid = sum(r.num_tickets for r in reservations if r.status == 'paid')
        total_pending = sum(r.num_tickets for r in reservations if r.status == 'pending')
        total_cancelled = sum(r.num_tickets for r in reservations if r.status == 'cancelled')
        revenue = total_paid * event.price
        report_data.append({
            'event': event,
            'total_reserved': total_reserved,
            'total_paid': total_paid,
            'total_pending': total_pending,
            'total_cancelled': total_cancelled,
            'revenue': revenue,
        })
    return render_template('admin/reports.html', report_data=report_data)


# ---------------------------------------------------------------------------
# Database initialisation
# ---------------------------------------------------------------------------

def init_db():
    """Create tables and default global admin if none exists."""
    with app.app_context():
        db.create_all()
        if not Admin.query.first():
            admin = Admin(username='admin', name='Global Admin', role='global_admin')
            admin.set_password('changeme')
            db.session.add(admin)
            db.session.commit()
            print("Default admin created — username: admin, password: changeme")


if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
