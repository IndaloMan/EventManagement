from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

db = SQLAlchemy()


class Business(db.Model):
    __tablename__ = 'businesses'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    address = db.Column(db.String(500))
    phone = db.Column(db.String(30))
    email = db.Column(db.String(120))
    website = db.Column(db.String(200))
    google_calendar_id = db.Column(db.String(256))
    logo_filename = db.Column(db.String(256))
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    events = db.relationship('Event', backref='business', lazy=True)


admin_businesses = db.Table('admin_businesses',
    db.Column('admin_id', db.Integer, db.ForeignKey('admins.id'), primary_key=True),
    db.Column('business_id', db.Integer, db.ForeignKey('businesses.id'), primary_key=True)
)

event_managers = db.Table('event_managers',
    db.Column('admin_id', db.Integer, db.ForeignKey('admins.id'), primary_key=True),
    db.Column('event_id', db.Integer, db.ForeignKey('events.id'), primary_key=True)
)


class Admin(UserMixin, db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(30))
    role = db.Column(db.String(20), nullable=False, default='event_manager')
    is_active_admin = db.Column(db.Boolean, default=True)
    reset_token = db.Column(db.String(64))
    reset_token_expires = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    businesses = db.relationship('Business', secondary=admin_businesses, backref='admins')
    managed_events = db.relationship('Event', secondary=event_managers, backref='managers')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    ROLE_HIERARCHY = ['cashier', 'event_security', 'event_manager', 'owner', 'global_admin']

    @property
    def role_level(self):
        try:
            return self.ROLE_HIERARCHY.index(self.role)
        except ValueError:
            return -1

    @property
    def is_global_admin(self):
        return self.role == 'global_admin'

    @property
    def is_owner(self):
        return self.role_level >= self.ROLE_HIERARCHY.index('owner')

    @property
    def is_event_manager(self):
        return self.role_level >= self.ROLE_HIERARCHY.index('event_manager')

    @property
    def is_event_security(self):
        return self.role_level >= self.ROLE_HIERARCHY.index('event_security')

    @property
    def is_cashier(self):
        return self.role_level >= self.ROLE_HIERARCHY.index('cashier')

    @property
    def role_exact(self):
        return self.role

    def can_access_business(self, business):
        if self.is_global_admin:
            return True
        if self.role in ('owner', 'cashier'):
            return business in self.businesses
        return any(e.business_id == business.id for e in self.managed_events)

    def can_access_event(self, event):
        if self.is_global_admin:
            return True
        if self.role in ('owner', 'cashier'):
            return event.business in self.businesses
        return event in self.managed_events

    def get_accessible_businesses(self):
        if self.is_global_admin:
            return Business.query.filter_by(is_active=True).all()
        if self.role in ('owner', 'cashier'):
            return [b for b in self.businesses if b.is_active]
        business_ids = {e.business_id for e in self.managed_events}
        return Business.query.filter(Business.id.in_(business_ids)).all()

    def get_accessible_events(self):
        if self.is_global_admin:
            return Event.query.order_by(Event.start_time.desc()).all()
        if self.role in ('owner', 'cashier'):
            biz_ids = [b.id for b in self.businesses]
            return Event.query.filter(Event.business_id.in_(biz_ids)).order_by(Event.start_time.desc()).all()
        return list(self.managed_events)


class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=False)
    gcal_event_id = db.Column(db.String(256), unique=True)
    event_code = db.Column(db.String(6), unique=True)
    title = db.Column(db.String(200), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime)
    end_time_text = db.Column(db.String(100))
    location = db.Column(db.String(200))
    description = db.Column(db.Text)
    price = db.Column(db.Float, default=0.0)
    max_capacity = db.Column(db.Integer, default=0)
    includes = db.Column(db.String(500))
    dress_code = db.Column(db.String(200))
    poster_filename = db.Column(db.String(256))
    terms_filename = db.Column(db.String(256))
    is_active = db.Column(db.Boolean, default=True)
    payment_mode = db.Column(db.String(10), default='cash')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    reservations = db.relationship('Reservation', backref='event', lazy=True)

    @property
    def tickets_reserved(self):
        return sum(r.num_tickets for r in self.reservations if r.status != 'cancelled')

    @property
    def tickets_available(self):
        if self.max_capacity == 0:
            return None
        return self.max_capacity - self.tickets_reserved

    @property
    def is_sold_out(self):
        if self.max_capacity == 0:
            return False
        return self.tickets_reserved >= self.max_capacity

    @property
    def is_past(self):
        return self.start_time < datetime.now(timezone.utc).replace(tzinfo=None)


class Reservation(db.Model):
    __tablename__ = 'reservations'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    reference_code = db.Column(db.String(8), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(30))
    num_tickets = db.Column(db.Integer, nullable=False, default=1)
    status = db.Column(db.String(20), default='pending')
    lang = db.Column(db.String(2), default='en')
    is_comp = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)
    stripe_payment_intent_id = db.Column(db.String(256))
    group_ref = db.Column(db.String(8))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    paid_at = db.Column(db.DateTime)
    paid_to_admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'))

    logs = db.relationship('ReservationLog', backref='reservation', lazy=True,
                           order_by='ReservationLog.created_at')

    @staticmethod
    def generate_reference():
        return uuid.uuid4().hex[:8].upper()


class AppSettings(db.Model):
    __tablename__ = 'app_settings'
    id = db.Column(db.Integer, primary_key=True)
    promo_display_name = db.Column(db.String(24), nullable=False, default='VIP Promotions')
    promo_full_name = db.Column(db.String(200))
    promo_description = db.Column(db.Text)
    smtp_email = db.Column(db.String(120))
    smtp_password = db.Column(db.String(256))
    smtp_from_name = db.Column(db.String(100))
    stripe_publishable_key = db.Column(db.String(256))
    stripe_secret_key = db.Column(db.String(256))
    stripe_webhook_secret = db.Column(db.String(256))


class Maintenance(db.Model):
    __tablename__ = 'maintenance'
    id = db.Column(db.Integer, primary_key=True)
    is_active = db.Column(db.Boolean, default=False)
    message = db.Column(db.Text, default='The system is currently undergoing scheduled maintenance.')
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ReservationLog(db.Model):
    __tablename__ = 'reservation_logs'
    id = db.Column(db.Integer, primary_key=True)
    reservation_id = db.Column(db.Integer, db.ForeignKey('reservations.id'), nullable=False)
    action = db.Column(db.String(30), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'))
    notes = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    admin = db.relationship('Admin', lazy=True)
