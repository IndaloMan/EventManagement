"""Marina Club Events — multi-business ticket reservation system."""

import env  # noqa: F401
import os
import re
from PIL import Image
import uuid
import stripe
from functools import wraps
from datetime import datetime, timedelta, timezone
from flask import (Flask, render_template, request, redirect, url_for,
                   flash, send_from_directory, abort, jsonify, Response)
from flask_login import (LoginManager, login_user, logout_user,
                         login_required, current_user)
from werkzeug.utils import secure_filename
from config import Config
from models import db, Admin, Business, Event, Reservation, ReservationLog, Maintenance, AppSettings, event_managers
from qr_generator import generate_event_qr, generate_reference_qr_base64
from email_sender import send_confirmation_email, send_cancellation_email, send_password_reset_email
from translations import TRANSLATIONS, SUPPORTED_LANGUAGES, format_date_long, format_date_short

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'admin_login'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf'}

PUBLIC_ROUTES = ('index', 'business_events', 'business_flyer', 'reserve', 'reservation_manage',
                 'embed_event', 'embed_business', 'static', 'manifest_json', 'login_redirect',
                 'stripe_checkout', 'stripe_success', 'stripe_cancel', 'stripe_webhook')


def get_lang():
    """Detect language from URL param or browser Accept-Language header."""
    lang = request.args.get('lang', '').lower()
    if lang in ('en', 'es'):
        return lang
    best = request.accept_languages.best_match(['es', 'en'], default='en')
    return best


@app.context_processor
def inject_globals():
    settings = AppSettings.query.first()
    if not settings:
        settings = AppSettings()
    lang = get_lang()
    return {'app_settings': settings, 't': TRANSLATIONS[lang], 'lang': lang,
            'supported_languages': SUPPORTED_LANGUAGES}


@app.before_request
def check_maintenance():
    if request.endpoint and request.endpoint in PUBLIC_ROUTES:
        maint = Maintenance.query.first()
        if maint and maint.is_active:
            return render_template('maintenance.html', maintenance=maint), 503


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
        if current_user.role_exact not in ('global_admin', 'owner'):
            abort(403)
        return f(*args, **kwargs)
    return decorated


def get_event_file(event, file_type, lang='en'):
    """Return filename for a language-specific event file, with fallbacks.

    Priority: {event_code}_{type}_{lang}.ext → English version → legacy filename.
    """
    upload_folder = app.config.get('UPLOAD_FOLDER', 'static/uploads')
    exts = ['jpg', 'jpeg', 'png', 'gif', 'webp'] if file_type == 'poster' else ['pdf']

    if event.event_code:
        for try_lang in ([lang, 'en'] if lang != 'en' else ['en']):
            for ext in exts:
                fname = f"{event.event_code}_{file_type}_{try_lang}.{ext}"
                if os.path.exists(os.path.join(upload_folder, fname)):
                    return fname

    # Legacy fallback for files uploaded before this convention
    return event.poster_filename if file_type == 'poster' else event.terms_filename


def _save_event_file(file_obj, event_code, file_type, lang):
    """Save uploaded file using naming convention, removing stale extension variants."""
    if not file_obj or not file_obj.filename:
        return
    ext = file_obj.filename.rsplit('.', 1)[-1].lower() if '.' in file_obj.filename else ''
    if file_type == 'poster' and ext not in {'png', 'jpg', 'jpeg', 'gif', 'webp'}:
        return
    if file_type == 'terms' and ext != 'pdf':
        return
    upload_folder = app.config['UPLOAD_FOLDER']
    # Remove existing file for this slot with any extension
    for old_ext in (['jpg', 'jpeg', 'png', 'gif', 'webp'] if file_type == 'poster' else ['pdf']):
        old_path = os.path.join(upload_folder, f"{event_code}_{file_type}_{lang}.{old_ext}")
        if os.path.exists(old_path):
            os.remove(old_path)
    file_obj.save(os.path.join(upload_folder, f"{event_code}_{file_type}_{lang}.{ext}"))


app.jinja_env.globals['event_file'] = get_event_file


@app.template_filter('fmt_eur')
def fmt_eur(value):
    if not value:
        return '0'
    return '{:g}'.format(float(value))


@app.template_filter('fmt_date')
def fmt_date_filter(dt, lang='en', style='long'):
    if dt is None:
        return ''
    if style == 'short':
        return format_date_short(dt, lang)
    return format_date_long(dt, lang)


def generate_event_code():
    """Generate a unique 6-character uppercase alphanumeric event code."""
    while True:
        code = uuid.uuid4().hex[:6].upper()
        if not Event.query.filter_by(event_code=code).first():
            return code


def log_reservation(reservation_id, action, admin_id=None, notes=None):
    log = ReservationLog(
        reservation_id=reservation_id,
        action=action,
        admin_id=admin_id,
        notes=notes,
    )
    db.session.add(log)
    db.session.flush()


# ---------------------------------------------------------------------------
# Dynamic manifest
# ---------------------------------------------------------------------------

@app.route('/manifest.json')
def manifest_json():
    settings = AppSettings.query.first()
    name = settings.promo_display_name if settings else 'VIP Promotions'
    import json
    data = {
        "name": name,
        "short_name": name,
        "start_url": "/",
        "display": "standalone",
        "background_color": "#0d0d0d",
        "theme_color": "#0d0d0d",
        "icons": [
            {"src": "/static/icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/static/icons/icon-512.png", "sizes": "512x512", "type": "image/png"}
        ]
    }
    return Response(json.dumps(data), mimetype='application/manifest+json')


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
        Event.start_time >= datetime.now(timezone.utc).replace(tzinfo=None)
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

        if not name or not email:
            flash('Name and email are required.', 'error')
            return render_template('reserve.html', event=event)

        if get_event_file(event, 'terms', get_lang()) and not request.form.get('agree_terms'):
            flash('You must agree to the Terms and Conditions.', 'error')
            return render_template('reserve.html', event=event)

        if num_tickets < 1:
            flash('You must reserve at least 1 ticket.', 'error')
            return render_template('reserve.html', event=event)

        if event.max_capacity > 0:
            available = event.tickets_available
            if available is not None and num_tickets > available:
                flash(f'Only {available} tickets remaining.', 'error')
                return render_template('reserve.html', event=event)

        lang = get_lang()
        payment_choice = request.form.get('payment_choice', 'online')
        use_stripe = (
            event.price > 0 and
            event.payment_mode in ('stripe', 'both') and
            (event.payment_mode == 'stripe' or payment_choice == 'online')
        )
        split_tickets = request.form.get('split_tickets') == '1' and num_tickets > 1

        if split_tickets:
            # Create leader reservation (1 ticket)
            leader = Reservation(
                event_id=event.id,
                reference_code=Reservation.generate_reference(),
                name=name, email=email, phone=phone,
                num_tickets=1, status='pending', lang=lang,
            )
            db.session.add(leader)
            db.session.flush()
            log_reservation(leader.id, 'reserved',
                            notes=f'{leader.name}, 1 ticket (group leader)')

            # Create sub-ticket reservations
            sub_reservations = []
            for i in range(2, num_tickets + 1):
                sub_email = request.form.get(f'ticket_email_{i}', '').strip() or None
                sub = Reservation(
                    event_id=event.id,
                    reference_code=Reservation.generate_reference(),
                    name=f'Guest {i}', email=sub_email, phone='',
                    num_tickets=1, status='pending', lang=lang,
                )
                db.session.add(sub)
                db.session.flush()
                log_reservation(sub.id, 'reserved',
                                notes=f'Guest {i}, 1 ticket (group {leader.reference_code})')
                sub_reservations.append(sub)

            group_ref = leader.reference_code
            leader.group_ref = group_ref
            for sub in sub_reservations:
                sub.group_ref = group_ref

            all_reservations = [leader] + sub_reservations

            if use_stripe:
                stripe_keys = _get_stripe_keys(event.business)
                if stripe_keys:
                    try:
                        checkout_session = _create_stripe_session(
                            leader, event, stripe_keys, total_tickets=num_tickets)
                        leader.stripe_payment_intent_id = checkout_session.payment_intent
                        db.session.commit()
                        return redirect(checkout_session.url, code=303)
                    except Exception as e:
                        db.session.rollback()
                        flash(f'Payment setup failed: {e}', 'error')
                        return render_template('reserve.html', event=event)

            # Cash: send group emails
            settings = AppSettings.query.first()
            _send_group_emails(leader, all_reservations, event, settings, lang, paid=False)
            db.session.commit()
            return render_template('confirmation.html', event=event, reservation=leader,
                                   group_reservations=all_reservations)

        else:
            # Solo booking (original flow)
            reservation = Reservation(
                event_id=event.id,
                reference_code=Reservation.generate_reference(),
                name=name, email=email, phone=phone,
                num_tickets=num_tickets, status='pending', lang=lang,
            )
            db.session.add(reservation)
            db.session.flush()
            log_reservation(reservation.id, 'reserved',
                            notes=f'{reservation.name}, {reservation.num_tickets} ticket(s)')

            if use_stripe:
                stripe_keys = _get_stripe_keys(event.business)
                if stripe_keys:
                    try:
                        checkout_session = _create_stripe_session(reservation, event, stripe_keys)
                        reservation.stripe_payment_intent_id = checkout_session.payment_intent
                        db.session.commit()
                        return redirect(checkout_session.url, code=303)
                    except Exception as e:
                        flash(f'Payment setup failed: {e}', 'error')
                        db.session.commit()
                        return render_template('reserve.html', event=event)

            ref_qr_base64 = generate_reference_qr_base64(
                f"{app.config['APP_URL']}/admin/scan/{reservation.reference_code}")
            settings = AppSettings.query.first()
            email_sent = send_confirmation_email(app.config, reservation, event, ref_qr_base64,
                                                 settings=settings, lang=lang)
            if email_sent:
                log_reservation(reservation.id, 'email_sent',
                                notes=f'Confirmation sent to {reservation.email}')
            db.session.commit()
            return render_template('confirmation.html', event=event, reservation=reservation)

    return render_template('reserve.html', event=event)


@app.route('/reservation/<reference_code>', methods=['GET', 'POST'])
def reservation_manage(reference_code):
    """Public page for customers to view/modify/cancel their reservation."""
    reservation = Reservation.query.filter_by(
        reference_code=reference_code.upper()).first_or_404()
    event = reservation.event

    if request.method == 'POST' and reservation.status == 'pending':
        action = request.form.get('action')

        if action == 'update':
            new_qty = int(request.form.get('num_tickets', reservation.num_tickets))
            if new_qty < 1:
                flash('You must have at least 1 ticket.', 'error')
                return render_template('reservation_manage.html',
                                       reservation=reservation, event=event)
            if event.max_capacity > 0:
                other_reserved = event.tickets_reserved - reservation.num_tickets
                available = event.max_capacity - other_reserved
                if new_qty > available:
                    flash(f'Only {available} tickets available.', 'error')
                    return render_template('reservation_manage.html',
                                           reservation=reservation, event=event)
            old_qty = reservation.num_tickets
            reservation.num_tickets = new_qty
            log_reservation(reservation.id, 'modified',
                            notes=f'Tickets changed from {old_qty} to {new_qty}')
            ref_qr_base64 = generate_reference_qr_base64(
                f"{app.config['APP_URL']}/admin/scan/{reservation.reference_code}")
            _settings = AppSettings.query.first()
            send_confirmation_email(app.config, reservation, event, ref_qr_base64,
                                    settings=_settings, lang=get_lang())
            log_reservation(reservation.id, 'email_sent',
                            notes=f'Updated confirmation sent to {reservation.email}')
            db.session.commit()
            flash('Reservation updated. A new confirmation email has been sent.', 'success')

        elif action == 'cancel':
            reservation.status = 'cancelled'
            log_reservation(reservation.id, 'cancelled',
                            notes='Cancelled by customer')
            send_cancellation_email(app.config, reservation, event)
            log_reservation(reservation.id, 'email_sent',
                            notes=f'Cancellation sent to {reservation.email}')
            db.session.commit()
            flash('Reservation cancelled. A confirmation email has been sent.', 'success')

        return redirect(url_for('reservation_manage', reference_code=reference_code))

    return render_template('reservation_manage.html',
                           reservation=reservation, event=event)


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
            Event.start_time >= datetime.now(timezone.utc).replace(tzinfo=None)
        ).order_by(Event.start_time).all()
    return render_template('embed_business.html', business=business, events=events)


@app.route('/b/<slug>/flyer')
def business_flyer(slug):
    """Standalone event listing page for embedding on external websites."""
    business = Business.query.filter_by(slug=slug, is_active=True).first_or_404()
    events = Event.query.filter(
        Event.business_id == business.id,
        Event.is_active == True,
        Event.start_time >= datetime.now(timezone.utc).replace(tzinfo=None)
    ).order_by(Event.start_time).all()
    return render_template('business_flyer.html', business=business, events=events)


# ---------------------------------------------------------------------------
# Admin — authentication
# ---------------------------------------------------------------------------

@app.route('/login')
def login_redirect():
    return redirect(url_for('admin_login'))


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
            if admin.role_exact == 'event_security':
                return redirect(url_for('admin_scan'))
            if admin.role_exact == 'cashier':
                return redirect(url_for('admin_reservations'))
            return redirect(url_for('admin_dashboard'))
        flash('Invalid username or password.', 'error')

    return render_template('admin/login.html')


@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for('admin_login'))


@app.route('/admin/forgot-password', methods=['GET', 'POST'])
def admin_forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        admin = Admin.query.filter(Admin.username.ilike(email)).first()
        if admin and admin.is_active_admin:
            token = uuid.uuid4().hex
            admin.reset_token = token
            admin.reset_token_expires = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=1)
            db.session.commit()
            reset_url = f"{app.config['APP_URL']}/admin/reset-password/{token}"
            send_password_reset_email(app.config, email, reset_url)
        flash('If an account with that email exists, a reset link has been sent.', 'success')
        return redirect(url_for('admin_login'))
    return render_template('admin/forgot_password.html')


@app.route('/admin/reset-password/<token>', methods=['GET', 'POST'])
def admin_reset_password(token):
    admin = Admin.query.filter_by(reset_token=token).first()
    if not admin or not admin.reset_token_expires or admin.reset_token_expires < datetime.now(timezone.utc).replace(tzinfo=None):
        flash('This reset link is invalid or has expired.', 'error')
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        if not password:
            flash('Password is required.', 'error')
            return render_template('admin/reset_password.html', token=token)
        if password != confirm:
            flash('Passwords do not match.', 'error')
            return render_template('admin/reset_password.html', token=token)
        admin.set_password(password)
        admin.reset_token = None
        admin.reset_token_expires = None
        db.session.commit()
        flash('Password updated. Please sign in.', 'success')
        return redirect(url_for('admin_login'))

    return render_template('admin/reset_password.html', token=token)


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
        slug = request.form.get('slug', '').strip().upper()
        if not name or not slug:
            flash('Name and identifier are required.', 'error')
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
        business.description = request.form.get('description', '').strip()
        business.is_active = 'is_active' in request.form
        business.stripe_enabled = 'stripe_enabled' in request.form
        stripe_pub = request.form.get('stripe_publishable_key', '').strip()
        stripe_sec = request.form.get('stripe_secret_key', '').strip()
        stripe_wh = request.form.get('stripe_webhook_secret', '').strip()
        if stripe_pub:
            business.stripe_publishable_key = stripe_pub
        if stripe_sec:
            business.stripe_secret_key = stripe_sec
        if stripe_wh:
            business.stripe_webhook_secret = stripe_wh

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
            Admin.role.in_(['event_manager', 'event_security', 'cashier'])
        ).order_by(Admin.name).all()
    return render_template('admin/users.html', users=users)


@app.route('/admin/users/new', methods=['GET', 'POST'])
@owner_or_above
def admin_user_new():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        name = request.form.get('name', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', 'event_manager')

        if not current_user.is_global_admin:
            if role not in ('event_manager', 'event_security', 'cashier'):
                role = 'event_manager'

        form_data = {
            'name': name,
            'phone': request.form.get('phone', '').strip(),
            'role': role,
            'business_ids': request.form.getlist('business_ids'),
            'event_ids': request.form.getlist('event_ids'),
        }
        businesses = Business.query.filter_by(is_active=True).all()
        events = current_user.get_accessible_events()

        if not email or not name or not password:
            flash('Email, name and password are required.', 'error')
            return render_template('admin/user_form.html', user=None, businesses=businesses, events=events, form_data=form_data)

        if not re.match(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$', email):
            flash('Please enter a valid email address.', 'error')
            return render_template('admin/user_form.html', user=None, businesses=businesses, events=events, form_data=form_data)

        if Admin.query.filter(Admin.username.ilike(email)).first():
            flash('A user with that email already exists.', 'error')
            return render_template('admin/user_form.html', user=None, businesses=businesses, events=events, form_data=form_data)

        admin = Admin(
            username=email,
            name=name,
            email=email,
            phone=request.form.get('phone', '').strip(),
            role=role,
        )
        admin.set_password(password)

        if role in ('owner', 'cashier'):
            biz_ids = request.form.getlist('business_ids')
            for bid in biz_ids:
                biz = db.session.get(Business, int(bid))
                if biz:
                    admin.businesses.append(biz)

        if role in ('event_manager', 'event_security'):
            for eid in request.form.getlist('event_ids'):
                event = db.session.get(Event, int(eid))
                if event:
                    admin.managed_events.append(event)

        db.session.add(admin)
        db.session.commit()
        flash(f'User "{name}" created.', 'success')
        return redirect(url_for('admin_users'))

    businesses = Business.query.filter_by(is_active=True).all()
    events = current_user.get_accessible_events()
    return render_template('admin/user_form.html', user=None, businesses=businesses, events=events)


@app.route('/admin/users/<int:user_id>', methods=['GET', 'POST'])
@owner_or_above
def admin_user_edit(user_id):
    user = db.session.get(Admin, user_id)
    if not user:
        abort(404)

    if not current_user.is_global_admin and user.role not in ('event_manager', 'event_security', 'cashier'):
        abort(403)

    if request.method == 'POST':
        user.name = request.form.get('name', '').strip()
        user.email = request.form.get('email', '').strip()
        user.phone = request.form.get('phone', '').strip()
        user.is_active_admin = 'is_active_admin' in request.form

        if current_user.is_global_admin:
            user.role = request.form.get('role', user.role)
        if user.role in ('owner', 'cashier'):
            user.businesses.clear()
            for bid in request.form.getlist('business_ids'):
                biz = db.session.get(Business, int(bid))
                if biz:
                    user.businesses.append(biz)
        if user.role in ('event_manager', 'event_security'):
            user.managed_events.clear()
            for eid in request.form.getlist('event_ids'):
                event = db.session.get(Event, int(eid))
                if event:
                    user.managed_events.append(event)

        new_password = request.form.get('password', '').strip()
        if new_password:
            user.set_password(new_password)

        db.session.commit()
        flash('User updated.', 'success')
        return redirect(url_for('admin_users'))

    businesses = Business.query.filter_by(is_active=True).all()
    events = current_user.get_accessible_events()
    return render_template('admin/user_form.html', user=user, businesses=businesses, events=events)


# ---------------------------------------------------------------------------
# Admin — events
# ---------------------------------------------------------------------------

@app.route('/admin/events')
@login_required
def admin_events():
    events = current_user.get_accessible_events()
    return render_template('admin/events.html', events=events)


@app.route('/admin/events/new', methods=['GET', 'POST'])
@owner_or_above
def admin_event_new():
    """Manually create an event (without Google Calendar)."""
    businesses = current_user.get_accessible_businesses()

    if request.method == 'POST':
        business_id = int(request.form.get('business_id', 0))
        title = request.form.get('title', '').strip()
        start_date = request.form.get('start_date', '')
        start_time_val = request.form.get('start_time_val', '')

        if not title or not start_date or not start_time_val or not business_id:
            flash('Business, title, start date and start time are required.', 'error')
            return render_template('admin/event_form.html', businesses=businesses)

        biz = db.session.get(Business, business_id)
        if not biz or not current_user.can_access_business(biz):
            abort(403)

        start_time = datetime.strptime(f'{start_date}T{start_time_val}', '%Y-%m-%dT%H:%M')

        no_fixed_end = 'no_fixed_end' in request.form
        end_time_text = None
        if no_fixed_end:
            end_time = datetime.strptime(f'{start_date}T23:59', '%Y-%m-%dT%H:%M').replace(hour=0, minute=0) + timedelta(days=1)
            end_time_text = request.form.get('end_time_text', 'Til late').strip() or 'Til late'
        else:
            end_date = request.form.get('end_date', '')
            end_time_val = request.form.get('end_time_val', '')
            if end_date and end_time_val:
                end_time = datetime.strptime(f'{end_date}T{end_time_val}', '%Y-%m-%dT%H:%M')
            else:
                end_time = None

        event = Event(
            business_id=business_id,
            event_code=generate_event_code(),
            title=title,
            start_time=start_time,
            end_time=end_time,
            end_time_text=end_time_text,
            location=request.form.get('location', '').strip(),
            description=request.form.get('description', '').strip(),
            price=float(request.form.get('price', 0) or 0),
            max_capacity=int(request.form.get('max_capacity', 0) or 0),
            includes=request.form.get('includes', '').strip(),
            dress_code=request.form.get('dress_code', '').strip(),
            payment_mode=request.form.get('payment_mode', 'cash'),
            is_active=True,
        )

        poster = request.files.get('poster')
        if poster and poster.filename and allowed_file(poster.filename):
            db.session.flush()
            filename = secure_filename(f"event_{event.id}_{poster.filename}")
            poster.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            event.poster_filename = filename

        terms = request.files.get('terms')
        if terms and terms.filename and terms.filename.lower().endswith('.pdf'):
            db.session.flush()
            filename = secure_filename(f"terms_{event.id}_{terms.filename}")
            terms.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            event.terms_filename = filename

        db.session.add(event)
        db.session.commit()
        flash(f'Event "{title}" created.', 'success')
        return redirect(url_for('admin_event_detail', event_id=event.id))

    return render_template('admin/event_form.html', businesses=businesses)



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
        if current_user.role_exact == 'event_manager' and event not in current_user.managed_events:
            abort(403)

        title = request.form.get('title', '').strip()
        if title:
            event.title = title
        event.location = request.form.get('location', '').strip()
        event.description = request.form.get('description', '').strip()

        start_date = request.form.get('start_date', '')
        start_time_val = request.form.get('start_time_val', '')
        if start_date and start_time_val:
            try:
                event.start_time = datetime.strptime(f'{start_date}T{start_time_val}', '%Y-%m-%dT%H:%M')
            except ValueError:
                flash('Invalid start date/time.', 'error')
                return redirect(url_for('admin_event_detail', event_id=event.id))

        no_fixed_end = 'no_fixed_end' in request.form
        if no_fixed_end:
            event.end_time = None
            event.end_time_text = request.form.get('end_time_text', 'Til late').strip() or 'Til late'
        else:
            end_date = request.form.get('end_date', '')
            end_time_val = request.form.get('end_time_val', '')
            if end_date and end_time_val:
                try:
                    event.end_time = datetime.strptime(f'{end_date}T{end_time_val}', '%Y-%m-%dT%H:%M')
                except ValueError:
                    pass
            event.end_time_text = request.form.get('end_time_text', '').strip() or None

        event.price = float(request.form.get('price', 0) or 0)
        event.max_capacity = int(request.form.get('max_capacity', 0) or 0)
        event.includes = request.form.get('includes', '').strip()
        event.dress_code = request.form.get('dress_code', '').strip()
        event.payment_mode = request.form.get('payment_mode', 'cash')
        event.is_active = 'is_active' in request.form

        for lang_code, _ in SUPPORTED_LANGUAGES:
            _save_event_file(request.files.get(f'poster_{lang_code}'),
                             event.event_code, 'poster', lang_code)
            _save_event_file(request.files.get(f'terms_{lang_code}'),
                             event.event_code, 'terms', lang_code)

        if current_user.role_exact in ('global_admin', 'owner'):
            event.managers.clear()
            for mid in request.form.getlist('manager_ids'):
                mgr = db.session.get(Admin, int(mid))
                if mgr and mgr.role in ('event_manager', 'event_security'):
                    event.managers.append(mgr)

        db.session.commit()
        flash('Event updated.', 'success')
        return redirect(url_for('admin_event_detail', event_id=event.id))

    reservations = Reservation.query.filter_by(event_id=event.id).order_by(
        Reservation.created_at.desc()).all()
    all_managers = Admin.query.filter(
        Admin.role.in_(['event_manager', 'event_security']),
        Admin.is_active_admin == True).all()
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
                                  app.config['UPLOAD_FOLDER'], event.title)
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename,
                               as_attachment=True)


# ---------------------------------------------------------------------------
# Admin — reservations
# ---------------------------------------------------------------------------

@app.route('/admin/reservations/<int:res_id>')
@login_required
def admin_reservation_detail(res_id):
    reservation = db.session.get(Reservation, res_id)
    if not reservation:
        abort(404)
    if not current_user.can_access_event(reservation.event):
        abort(403)
    logs = ReservationLog.query.filter_by(reservation_id=reservation.id).order_by(
        ReservationLog.created_at).all()
    return render_template('admin/reservation_detail.html',
                           reservation=reservation,
                           event=reservation.event,
                           logs=logs)


@app.route('/admin/reservations')
@login_required
def admin_reservations():
    accessible_events = current_user.get_accessible_events()
    event_ids = [e.id for e in accessible_events]

    event_id = request.args.get('event_id', type=int)
    status = request.args.get('status', '')
    group_ref = request.args.get('group', '').upper()

    query = Reservation.query.filter(Reservation.event_id.in_(event_ids))
    if event_id:
        query = query.filter(Reservation.event_id == event_id)
    if status:
        query = query.filter(Reservation.status == status)
    if group_ref:
        query = query.filter(Reservation.group_ref == group_ref)

    reservations = query.order_by(Reservation.created_at.desc()).all()
    return render_template('admin/reservations.html',
                           reservations=reservations,
                           events=accessible_events,
                           selected_event=event_id,
                           selected_status=status,
                           selected_group=group_ref)


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
            reservation.paid_at = datetime.now(timezone.utc).replace(tzinfo=None)
            reservation.paid_to_admin_id = current_user.id
        log_reservation(reservation.id, new_status, admin_id=current_user.id)
        db.session.commit()

        if new_status == 'paid':
            return redirect(url_for('admin_print_ticket', res_id=reservation.id))

        flash(f'Reservation {reservation.reference_code} marked as {new_status}.', 'success')

    return redirect(request.referrer or url_for('admin_reservations'))


@app.route('/admin/reservations/<int:res_id>/ticket')
@login_required
def admin_print_ticket(res_id):
    reservation = db.session.get(Reservation, res_id)
    if not reservation:
        abort(404)
    if not current_user.can_access_event(reservation.event):
        abort(403)

    qr_base64 = generate_reference_qr_base64(
        f"{app.config['APP_URL']}/admin/scan/{reservation.reference_code}")
    log_reservation(reservation.id, 'ticket_printed', admin_id=current_user.id)
    db.session.commit()
    return render_template('admin/ticket.html',
                           reservation=reservation,
                           event=reservation.event,
                           qr_base64=qr_base64)


# ---------------------------------------------------------------------------
# Admin — scanning (event security + all roles)
# ---------------------------------------------------------------------------

@app.route('/admin/scan')
@login_required
def admin_scan():
    return render_template('admin/scan.html')


@app.route('/admin/scan/<reference_code>')
@login_required
def admin_scan_lookup(reference_code):
    reservation = Reservation.query.filter_by(
        reference_code=reference_code.upper()).first()
    if not reservation:
        flash('Ticket not found.', 'error')
        return render_template('admin/scan.html')

    if not current_user.can_access_event(reservation.event):
        abort(403)

    already_scanned = ReservationLog.query.filter_by(
        reservation_id=reservation.id, action='scanned_in').first()

    return render_template('admin/scan_result.html',
                           reservation=reservation,
                           event=reservation.event,
                           already_scanned=already_scanned)


@app.route('/admin/scan/<reference_code>/admit', methods=['POST'])
@login_required
def admin_scan_admit(reference_code):
    reservation = Reservation.query.filter_by(
        reference_code=reference_code.upper()).first()
    if not reservation:
        abort(404)
    if not current_user.can_access_event(reservation.event):
        abort(403)

    already_scanned = ReservationLog.query.filter_by(
        reservation_id=reservation.id, action='scanned_in').first()
    if already_scanned:
        flash(f'Already scanned in at {already_scanned.created_at.strftime("%H:%M")}', 'error')
        return redirect(url_for('admin_scan_lookup', reference_code=reference_code))

    if reservation.status != 'paid':
        flash(f'Ticket status is {reservation.status} — not paid.', 'error')
        return redirect(url_for('admin_scan_lookup', reference_code=reference_code))

    log_reservation(reservation.id, 'scanned_in', admin_id=current_user.id)
    db.session.commit()
    flash(f'{reservation.name} — {reservation.num_tickets} ticket(s) admitted.', 'success')
    return redirect(url_for('admin_scan_lookup', reference_code=reference_code))


@app.route('/admin/scan/<reference_code>/pay', methods=['POST'])
@login_required
def admin_scan_pay(reference_code):
    reservation = Reservation.query.filter_by(reference_code=reference_code.upper()).first_or_404()
    if not current_user.can_access_event(reservation.event):
        abort(403)
    if reservation.status == 'pending':
        reservation.status = 'paid'
        reservation.paid_at = datetime.now(timezone.utc).replace(tzinfo=None)
        reservation.paid_to_admin_id = current_user.id
        log_reservation(reservation.id, 'paid', admin_id=current_user.id)
        db.session.commit()
        flash(f'{reservation.reference_code} marked as paid.', 'success')
    return redirect(url_for('admin_scan_lookup', reference_code=reference_code))


@app.route('/admin/scan/<reference_code>/cancel', methods=['POST'])
@login_required
def admin_scan_cancel(reference_code):
    reservation = Reservation.query.filter_by(reference_code=reference_code.upper()).first_or_404()
    if not current_user.can_access_event(reservation.event):
        abort(403)
    if reservation.status == 'pending':
        reservation.status = 'cancelled'
        log_reservation(reservation.id, 'cancelled', admin_id=current_user.id,
                        notes='Cancelled at scan')
        db.session.commit()
        flash(f'{reservation.reference_code} cancelled.', 'success')
    return redirect(url_for('admin_scan_lookup', reference_code=reference_code))


@app.route('/admin/scan/<reference_code>/comp', methods=['POST'])
@login_required
def admin_scan_comp(reference_code):
    if not current_user.is_event_manager:
        abort(403)
    reservation = Reservation.query.filter_by(reference_code=reference_code.upper()).first_or_404()
    if not current_user.can_access_event(reservation.event):
        abort(403)
    if reservation.status == 'pending':
        reservation.status = 'paid'
        reservation.is_comp = True
        reservation.paid_at = datetime.now(timezone.utc).replace(tzinfo=None)
        reservation.paid_to_admin_id = current_user.id
        log_reservation(reservation.id, 'comp', admin_id=current_user.id,
                        notes='Complimentary — 0€')
        db.session.commit()
        flash(f'{reservation.reference_code} marked as complimentary.', 'success')
    return redirect(url_for('admin_scan_lookup', reference_code=reference_code))


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
        total_comp = sum(r.num_tickets for r in reservations if r.status == 'paid' and r.is_comp)
        total_pending = sum(r.num_tickets for r in reservations if r.status == 'pending')
        total_cancelled = sum(r.num_tickets for r in reservations if r.status == 'cancelled')
        revenue = sum(r.num_tickets * event.price for r in reservations
                      if r.status == 'paid' and not r.is_comp)
        report_data.append({
            'event': event,
            'total_reserved': total_reserved,
            'total_paid': total_paid,
            'total_comp': total_comp,
            'total_pending': total_pending,
            'total_cancelled': total_cancelled,
            'revenue': revenue,
        })
    return render_template('admin/reports.html', report_data=report_data)


@app.route('/admin/reports/event/<int:event_id>/reservations')
@login_required
def admin_report_reservations(event_id):
    event = db.session.get(Event, event_id)
    if not event or not current_user.can_access_event(event):
        abort(403)
    status_filter = request.args.get('status', '')
    query = Reservation.query.filter_by(event_id=event.id)
    if status_filter:
        query = query.filter_by(status=status_filter)
    reservations = query.order_by(Reservation.name).all()
    return render_template('admin/report_reservations.html',
                           event=event, reservations=reservations,
                           status_filter=status_filter, now=datetime.now(timezone.utc).replace(tzinfo=None))


@app.route('/admin/reports/reservation/<int:res_id>')
@login_required
def admin_report_booking(res_id):
    reservation = db.session.get(Reservation, res_id)
    if not reservation or not current_user.can_access_event(reservation.event):
        abort(403)
    return render_template('admin/report_booking.html',
                           reservation=reservation, event=reservation.event)


# ---------------------------------------------------------------------------
# Admin — maintenance mode (global admin only)
# ---------------------------------------------------------------------------

@app.route('/admin/maintenance', methods=['GET', 'POST'])
@global_admin_required
def admin_maintenance():
    maint = Maintenance.query.first()
    if not maint:
        maint = Maintenance()
        db.session.add(maint)
        db.session.commit()

    if request.method == 'POST':
        maint.is_active = 'is_active' in request.form
        maint.message = request.form.get('message', '').strip()
        start_date = request.form.get('start_date', '')
        start_time = request.form.get('start_time_val', '')
        end_date = request.form.get('end_date', '')
        end_time = request.form.get('end_time_val', '')
        if start_date and start_time:
            maint.start_time = datetime.strptime(f'{start_date}T{start_time}', '%Y-%m-%dT%H:%M')
        if end_date and end_time:
            maint.end_time = datetime.strptime(f'{end_date}T{end_time}', '%Y-%m-%dT%H:%M')
        db.session.commit()
        flash('Maintenance settings updated.', 'success')
        return redirect(url_for('admin_maintenance'))

    return render_template('admin/maintenance.html', maintenance=maint)


# ---------------------------------------------------------------------------
# Admin — app settings (owner+)
# ---------------------------------------------------------------------------

@app.route('/admin/settings', methods=['GET', 'POST'])
@owner_or_above
def admin_settings():
    settings = AppSettings.query.first()
    if not settings:
        settings = AppSettings()
        db.session.add(settings)
        db.session.commit()

    if request.method == 'POST':
        display_name = request.form.get('promo_display_name', '').strip()[:24]
        if not display_name:
            flash('Display name is required.', 'error')
            return render_template('admin/settings.html', settings=settings)
        settings.promo_display_name = display_name
        settings.promo_full_name = request.form.get('promo_full_name', '').strip()
        settings.promo_description = request.form.get('promo_description', '').strip()

        smtp_email = request.form.get('smtp_email', '').strip()
        smtp_password = request.form.get('smtp_password', '').strip()
        smtp_from_name = request.form.get('smtp_from_name', '').strip()
        if smtp_email:
            settings.smtp_email = smtp_email
        if smtp_password:
            settings.smtp_password = smtp_password
        settings.smtp_from_name = smtp_from_name

        icon = request.files.get('app_icon')
        if icon and icon.filename and allowed_file(icon.filename):
            icons_dir = os.path.join(app.static_folder, 'icons')
            os.makedirs(icons_dir, exist_ok=True)
            img = Image.open(icon).convert('RGBA')
            for size in [192, 512]:
                resized = img.resize((size, size), Image.LANCZOS)
                bg = Image.new('RGB', (size, size), '#0d0d0d')
                bg.paste(resized, mask=resized.split()[3])
                bg.save(os.path.join(icons_dir, f'icon-{size}.png'))

        stripe_publishable_key = request.form.get('stripe_publishable_key', '').strip()
        stripe_secret_key = request.form.get('stripe_secret_key', '').strip()
        stripe_webhook_secret = request.form.get('stripe_webhook_secret', '').strip()
        if stripe_publishable_key:
            settings.stripe_publishable_key = stripe_publishable_key
        if stripe_secret_key:
            settings.stripe_secret_key = stripe_secret_key
        if stripe_webhook_secret:
            settings.stripe_webhook_secret = stripe_webhook_secret

        db.session.commit()

        if settings.smtp_email:
            app.config['SMTP_EMAIL'] = settings.smtp_email
        if settings.smtp_password:
            app.config['SMTP_PASSWORD'] = settings.smtp_password

        flash('Settings saved.', 'success')
        return redirect(url_for('admin_dashboard'))

    icon_exists = os.path.exists(os.path.join(app.static_folder, 'icons', 'icon-192.png'))
    return render_template('admin/settings.html', settings=settings,
                           icon_exists=icon_exists, now=int(datetime.now(timezone.utc).replace(tzinfo=None).timestamp()))


# ---------------------------------------------------------------------------
# Stripe payment routes
# ---------------------------------------------------------------------------

def _send_group_emails(leader, all_members, event, settings, lang, paid=False):
    """Send confirmation emails for a group booking. Leader gets extras for no-email members."""
    extra_tickets = []
    for res in all_members:
        if res.id == leader.id:
            continue
        ref_qr = generate_reference_qr_base64(f"{app.config['APP_URL']}/admin/scan/{res.reference_code}")
        if res.email:
            sent = send_confirmation_email(app.config, res, event, ref_qr,
                                           settings=settings, lang=lang, paid=paid)
            if sent:
                log_reservation(res.id, 'email_sent', notes=f'Confirmation sent to {res.email}')
        else:
            extra_tickets.append({'ref': res.reference_code, 'name': res.name})
    ref_qr = generate_reference_qr_base64(f"{app.config['APP_URL']}/admin/scan/{leader.reference_code}")
    sent = send_confirmation_email(app.config, leader, event, ref_qr,
                                   settings=settings, lang=lang, paid=paid,
                                   extra_tickets=extra_tickets if extra_tickets else None)
    if sent:
        log_reservation(leader.id, 'email_sent', notes=f'Confirmation sent to {leader.email}')


def _get_stripe_keys(business):
    """Return (publishable_key, secret_key, webhook_secret) for a business.

    Uses business-level keys when the business has Stripe enabled and its own
    keys configured; falls back to global app_settings keys when enabled but no
    business keys are set; returns None if Stripe is not enabled for the business.
    """
    if not business or not business.stripe_enabled:
        return None
    if business.stripe_secret_key:
        return (business.stripe_publishable_key,
                business.stripe_secret_key,
                business.stripe_webhook_secret)
    settings = AppSettings.query.first()
    if settings and settings.stripe_secret_key:
        return (settings.stripe_publishable_key,
                settings.stripe_secret_key,
                settings.stripe_webhook_secret)
    return None


def _create_stripe_session(reservation, event, keys, total_tickets=None):
    """Create a Stripe Checkout Session for the given reservation."""
    stripe.api_key = keys[1]
    lang = reservation.lang or 'en'
    qty = total_tickets if total_tickets is not None else reservation.num_tickets
    if lang == 'es':
        ticket_label = 'entrada' if qty == 1 else 'entradas'
    else:
        ticket_label = 'ticket' if qty == 1 else 'tickets'
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        locale=lang,
        line_items=[{
            'price_data': {
                'currency': 'eur',
                'product_data': {
                    'name': f'{event.title} — {qty} {ticket_label}',
                },
                'unit_amount': int(event.price * 100),
            },
            'quantity': qty,
        }],
        mode='payment',
        success_url=f"{app.config['APP_URL']}/stripe/success?ref={reservation.reference_code}&session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{app.config['APP_URL']}/stripe/cancel?ref={reservation.reference_code}",
        metadata={'reference_code': reservation.reference_code},
        customer_email=reservation.email,
    )
    return session


@app.route('/stripe/checkout/<reference_code>', methods=['POST'])
def stripe_checkout(reference_code):
    """Retry Stripe checkout for an existing pending reservation."""
    reservation = Reservation.query.filter_by(reference_code=reference_code.upper()).first_or_404()
    event = reservation.event

    if reservation.status != 'pending':
        flash('This reservation cannot be paid online.', 'error')
        return redirect(url_for('reservation_manage', reference_code=reservation.reference_code))

    stripe_keys = _get_stripe_keys(event.business)
    if not stripe_keys:
        flash('Online payment is not available.', 'error')
        return redirect(url_for('reservation_manage', reference_code=reservation.reference_code))

    try:
        session = _create_stripe_session(reservation, event, stripe_keys)
        reservation.stripe_payment_intent_id = session.payment_intent
        db.session.commit()
        return redirect(session.url, code=303)
    except Exception as e:
        flash(f'Payment setup failed: {e}', 'error')
        return redirect(url_for('reservation_manage', reference_code=reservation.reference_code))


@app.route('/stripe/success')
def stripe_success():
    ref = request.args.get('ref', '').upper()
    session_id = request.args.get('session_id', '')
    reservation = Reservation.query.filter_by(reference_code=ref).first_or_404()
    event = reservation.event
    lang = reservation.lang or 'en'

    group_reservations = []
    if reservation.status == 'pending' and session_id:
        settings = AppSettings.query.first()
        stripe_keys = _get_stripe_keys(event.business)
        if stripe_keys:
            stripe.api_key = stripe_keys[1]
            try:
                cs = stripe.checkout.Session.retrieve(session_id)
                if cs.payment_status == 'paid':
                    reservation.status = 'paid'
                    reservation.paid_at = datetime.now(timezone.utc).replace(tzinfo=None)
                    log_reservation(reservation.id, 'paid', notes='Stripe online payment')

                    # Mark group members paid
                    if reservation.group_ref:
                        all_members = Reservation.query.filter_by(
                            group_ref=reservation.group_ref).all()
                        for member in all_members:
                            if member.id != reservation.id and member.status == 'pending':
                                member.status = 'paid'
                                member.paid_at = datetime.now(timezone.utc).replace(tzinfo=None)
                                log_reservation(member.id, 'paid',
                                                notes='Stripe online payment (group)')
                        db.session.commit()
                        group_reservations = all_members
                        _send_group_emails(reservation, all_members, event, settings,
                                           lang, paid=True)
                    else:
                        db.session.commit()
                        ref_qr_base64 = generate_reference_qr_base64(
                            f"{app.config['APP_URL']}/admin/scan/{reservation.reference_code}")
                        email_sent = send_confirmation_email(app.config, reservation, event,
                                                            ref_qr_base64, settings=settings,
                                                            lang=lang, paid=True)
                        if email_sent:
                            log_reservation(reservation.id, 'email_sent',
                                            notes=f'Confirmation sent to {reservation.email}')
                            db.session.commit()
            except Exception:
                pass
    elif reservation.group_ref:
        group_reservations = Reservation.query.filter_by(
            group_ref=reservation.group_ref).all()

    t = TRANSLATIONS.get(lang, TRANSLATIONS['en'])
    date_str = format_date_long(event.start_time, lang)
    return render_template('stripe_success.html', reservation=reservation, event=event,
                           t=t, date_str=date_str, group_reservations=group_reservations)


@app.route('/stripe/cancel')
def stripe_cancel():
    ref = request.args.get('ref', '').upper()
    reservation = Reservation.query.filter_by(reference_code=ref).first_or_404()
    event = reservation.event
    lang = reservation.lang or 'en'
    t = TRANSLATIONS.get(lang, TRANSLATIONS['en'])
    return render_template('stripe_cancel.html', reservation=reservation, event=event, t=t)


@app.route('/stripe/webhook', methods=['POST'])
def stripe_webhook():
    import json as _json
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature', '')

    # Parse payload to find the reference code so we can resolve the business
    try:
        raw_event = _json.loads(payload)
    except ValueError:
        return '', 400

    ref = ''
    if raw_event.get('type') == 'checkout.session.completed':
        cs = raw_event.get('data', {}).get('object', {})
        ref = (cs.get('metadata') or {}).get('reference_code', '')

    # Resolve Stripe keys from the business, falling back to global settings
    stripe_keys = None
    if ref:
        reservation = Reservation.query.filter_by(reference_code=ref).first()
        if reservation:
            stripe_keys = _get_stripe_keys(reservation.event.business)
    if not stripe_keys:
        settings = AppSettings.query.first()
        if settings and settings.stripe_secret_key:
            stripe_keys = (settings.stripe_publishable_key,
                           settings.stripe_secret_key,
                           settings.stripe_webhook_secret)
    if not stripe_keys:
        return '', 400

    stripe.api_key = stripe_keys[1]
    webhook_secret = stripe_keys[2]

    if webhook_secret:
        try:
            event_obj = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        except (ValueError, stripe.error.SignatureVerificationError):
            return '', 400
    else:
        event_obj = raw_event

    if event_obj['type'] == 'checkout.session.completed':
        cs = event_obj['data']['object']
        ref = (cs.get('metadata') or {}).get('reference_code', '')
        if ref:
            reservation = Reservation.query.filter_by(reference_code=ref).first()
            if reservation and reservation.status == 'pending':
                reservation.status = 'paid'
                reservation.paid_at = datetime.now(timezone.utc).replace(tzinfo=None)
                log_reservation(reservation.id, 'paid', notes='Stripe webhook confirmation')
                if reservation.group_ref:
                    group_members = Reservation.query.filter_by(
                        group_ref=reservation.group_ref).all()
                    for member in group_members:
                        if member.id != reservation.id and member.status == 'pending':
                            member.status = 'paid'
                            member.paid_at = datetime.now(timezone.utc).replace(tzinfo=None)
                            log_reservation(member.id, 'paid',
                                            notes='Stripe webhook confirmation (group)')
                db.session.commit()

    return '', 200


# ---------------------------------------------------------------------------
# Database initialisation
# ---------------------------------------------------------------------------

def init_db():
    """Create tables and default global admin if none exists."""
    with app.app_context():
        db.create_all()
        with db.engine.connect() as conn:
            cols = [r[1] for r in conn.execute(db.text("PRAGMA table_info(admins)"))]
            if 'reset_token' not in cols:
                conn.execute(db.text("ALTER TABLE admins ADD COLUMN reset_token VARCHAR(64)"))
                conn.execute(db.text("ALTER TABLE admins ADD COLUMN reset_token_expires DATETIME"))
                conn.commit()
            event_cols = [r[1] for r in conn.execute(db.text("PRAGMA table_info(events)"))]
            if 'end_time_text' not in event_cols:
                conn.execute(db.text("ALTER TABLE events ADD COLUMN end_time_text VARCHAR(100)"))
                conn.commit()
            if 'terms_filename' not in event_cols:
                conn.execute(db.text("ALTER TABLE events ADD COLUMN terms_filename VARCHAR(256)"))
                conn.commit()
            res_cols = [r[1] for r in conn.execute(db.text("PRAGMA table_info(reservations)"))]
            if 'is_comp' not in res_cols:
                conn.execute(db.text("ALTER TABLE reservations ADD COLUMN is_comp BOOLEAN DEFAULT 0"))
                conn.commit()
            if 'lang' not in res_cols:
                conn.execute(db.text("ALTER TABLE reservations ADD COLUMN lang VARCHAR(2) DEFAULT 'en'"))
                conn.commit()
            ev_cols = [r[1] for r in conn.execute(db.text("PRAGMA table_info(events)"))]
            if 'event_code' not in ev_cols:
                conn.execute(db.text("ALTER TABLE events ADD COLUMN event_code VARCHAR(6)"))
                conn.commit()
            if 'payment_mode' not in ev_cols:
                conn.execute(db.text("ALTER TABLE events ADD COLUMN payment_mode VARCHAR(10) DEFAULT 'cash'"))
                conn.commit()
            res_cols2 = [r[1] for r in conn.execute(db.text("PRAGMA table_info(reservations)"))]
            if 'stripe_payment_intent_id' not in res_cols2:
                conn.execute(db.text("ALTER TABLE reservations ADD COLUMN stripe_payment_intent_id VARCHAR(256)"))
                conn.commit()
            if 'group_ref' not in res_cols2:
                conn.execute(db.text("ALTER TABLE reservations ADD COLUMN group_ref VARCHAR(8)"))
                conn.commit()
            biz_cols = [r[1] for r in conn.execute(db.text("PRAGMA table_info(businesses)"))]
            if 'stripe_enabled' not in biz_cols:
                conn.execute(db.text("ALTER TABLE businesses ADD COLUMN stripe_enabled BOOLEAN DEFAULT 0"))
                conn.execute(db.text("ALTER TABLE businesses ADD COLUMN stripe_publishable_key VARCHAR(256)"))
                conn.execute(db.text("ALTER TABLE businesses ADD COLUMN stripe_secret_key VARCHAR(256)"))
                conn.execute(db.text("ALTER TABLE businesses ADD COLUMN stripe_webhook_secret VARCHAR(256)"))
                conn.commit()
            settings_cols = [r[1] for r in conn.execute(db.text("PRAGMA table_info(app_settings)"))]
            if 'stripe_publishable_key' not in settings_cols:
                conn.execute(db.text("ALTER TABLE app_settings ADD COLUMN stripe_publishable_key VARCHAR(256)"))
                conn.execute(db.text("ALTER TABLE app_settings ADD COLUMN stripe_secret_key VARCHAR(256)"))
                conn.execute(db.text("ALTER TABLE app_settings ADD COLUMN stripe_webhook_secret VARCHAR(256)"))
                conn.commit()
        for ev in Event.query.filter(Event.event_code == None).all():
            ev.event_code = generate_event_code()
        db.session.commit()
        if not Admin.query.first():
            admin = Admin(username='admin', name='Global Admin', role='global_admin')
            admin.set_password('changeme')
            db.session.add(admin)
            db.session.commit()
            print("Default admin created — username: admin, password: changeme")
        if not Maintenance.query.first():
            db.session.add(Maintenance())
            db.session.commit()
        if not AppSettings.query.first():
            db.session.add(AppSettings(promo_display_name='VIP Promotions'))
            db.session.commit()
        settings = AppSettings.query.first()
        if settings and settings.smtp_email:
            app.config['SMTP_EMAIL'] = settings.smtp_email
        if settings and settings.smtp_password:
            app.config['SMTP_PASSWORD'] = settings.smtp_password


os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
init_db()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
