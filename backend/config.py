import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

class Config:
    SECRET_KEY = 'replace_with_a_strong_secret_key'
    CORS_ORIGINS = [
        'http://localhost:5173',
        'http://127.0.0.1:5173',
        'http://localhost:5174',
        'http://127.0.0.1:5174'
    ]
    SESSION_SECURE = os.getenv('SESSION_SECURE', '').lower() in ('1', 'true', 'yes')
    DB_HOST = os.getenv('DB_HOST')
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_NAME = os.getenv('DB_NAME')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    # "or", not a getenv default: docker compose passes GEMINI_MODEL="" when .env leaves it blank.
    GEMINI_MODEL = os.getenv('GEMINI_MODEL') or 'gemini-3.8-flash'
    BRAIN_MODE = os.getenv('BRAIN_MODE', '')
    # Where the site is served; links in emails point here.
    APP_URL = (os.getenv('APP_URL') or 'http://localhost:5173').rstrip('/')
    # Gmail: smtp.gmail.com on 465 with an app password. Without SMTP_USER and SMTP_PASSWORD,
    # emails are written to the log instead of sent.
    SMTP_HOST = os.getenv('SMTP_HOST') or 'smtp.gmail.com'
    SMTP_PORT = int(os.getenv('SMTP_PORT') or 465)
    SMTP_USER = os.getenv('SMTP_USER', '')
    # Google shows app passwords in groups of four separated by spaces; the spaces are not part of it.
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '').replace(' ', '')
    MAIL_FROM = os.getenv('MAIL_FROM', '')
    # Uploaded images. In Docker this folder is a volume that nginx also reads.
    UPLOAD_DIR = os.getenv('UPLOAD_DIR') or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_UPLOAD_MB = 5
