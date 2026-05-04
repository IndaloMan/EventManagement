import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'events.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB max upload
    GOOGLE_CALENDAR_ID = os.environ.get('GOOGLE_CALENDAR_ID', '')
    GOOGLE_CREDENTIALS_FILE = os.path.join(BASE_DIR, 'credentials.json')
    APP_URL = os.environ.get('APP_URL', 'http://localhost:5000')
    SMTP_SERVER = 'smtp.gmail.com'
    SMTP_PORT = 465
    SMTP_EMAIL = os.environ.get('SMTP_EMAIL', '')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
