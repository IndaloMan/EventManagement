from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
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
    stripe_enabled = db.Column(db.Boolean, default=False)
    stripe_publishable_key = db.Column(db.String(256))
    stripe_secret_key = db.Column(db.String(256))
    stripe_webhook_secret = db.Column(db.String(256))
    solstack_location_id = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    events = db.relationship('Event', backref='business', lazy=True)


class EventStaff(db.Model):
    """Per-event staff assignment keyed by SolStack user_id."""
    __tablename__ = 'event_staff'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    solstack_user_id = db.Column(db.Integer, nullable=False)
    role = db.Column(db.String(30), nullable=False)  # staff_event or staff_security
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120))


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
    staff = db.relationship('EventStaff', backref='event', lazy=True,
                            cascade='all, delete-orphan')

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
    paid_to_admin_id = db.Column(db.Integer)  # stores SolStack user_id of who marked paid

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
    admin_id = db.Column(db.Integer)  # stores SolStack user_id of who took action
    notes = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
