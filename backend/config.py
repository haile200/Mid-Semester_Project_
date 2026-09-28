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
