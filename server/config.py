import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Use environment variables with secure defaults
    SECRET_KEY = os.getenv('SECRET_KEY') or os.urandom(32)
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') or 'sqlite:///loki.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File upload settings
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER') or 'uploads'
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size
    
    # Security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    PERMANENT_SESSION_LIFETIME = 1800  # 30 minutes
    
    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.getenv('CSRF_SECRET_KEY') or os.urandom(32)
    
    # Rate limiting
    RATELIMIT_DEFAULT = "200 per day"
    RATELIMIT_STORAGE_URL = "memory://"
    
    # Ensure upload directory exists
    @staticmethod
    def init_app(app):
        upload_dir = Path(app.config['UPLOAD_FOLDER'])
        upload_dir.mkdir(exist_ok=True)
        
        # Set secure file permissions
        upload_dir.chmod(0o750)


class DevelopmentConfig(Config):
    DEBUG = True
    DEVELOPMENT = True
    # Less strict settings for development
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_ENABLED = True


class ProductionConfig(Config):
    DEBUG = False
    DEVELOPMENT = False
    
    # Stricter settings for production
    PREFERRED_URL_SCHEME = 'https'
    SESSION_COOKIE_SECURE = True
    
    # Production-specific rate limits
    RATELIMIT_DEFAULT = "100 per day"
    
    # Use Redis for rate limiting in production if available
    if os.getenv('REDIS_URL'):
        RATELIMIT_STORAGE_URL = os.getenv('REDIS_URL')
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Production logging
        import logging
        from logging.handlers import RotatingFileHandler
        
        file_handler = RotatingFileHandler('loki.log',
                                         maxBytes=10240,
                                         backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        # Ensure all directories have secure permissions
        for path in [Path('instance'), Path('logs'), Path(app.config['UPLOAD_FOLDER'])]:
            path.mkdir(exist_ok=True)
            path.chmod(0o750)


config = {
    'dev': DevelopmentConfig,
    'prod': ProductionConfig,
    'default': DevelopmentConfig
}
