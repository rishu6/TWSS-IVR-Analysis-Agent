import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    mode: str = os.getenv('APP_MODE', 'demo')
    database_url: str = os.getenv('DATABASE_URL', 'sqlite:///./demo.db')
    demo_password: str = os.getenv('DEMO_PASSWORD', 'synthetic-demo-only')
    secure_cookies: bool = os.getenv('SECURE_COOKIES', 'false').lower() == 'true'
    origin: str = os.getenv('APP_ORIGIN', 'http://localhost:5173')
    redis_url: str = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    recovery_hours: int = int(os.getenv('RECOVERY_WINDOW_HOURS', '24'))
    integrations_file: str = os.getenv('INTEGRATIONS_ENV_FILE', '.env.integrations')
    static_directory: str = os.getenv('STATIC_DIRECTORY', 'frontend/dist')
    source_timezone: str = os.getenv('ACEFONE_TIMEZONE', 'Asia/Kolkata')
    sync_seconds: int = int(os.getenv('SYNC_INTERVAL_SECONDS', '60'))
    initial_sync_days: int = int(os.getenv('INITIAL_SYNC_DAYS', '3'))
    max_provider_pages: int = int(os.getenv('MAX_PROVIDER_PAGES', '1000'))
    auto_sync: bool = os.getenv('AUTO_SYNC', 'true').lower() == 'true'

    def validate(self):
        if self.mode not in ('demo', 'internal'):
            raise RuntimeError('Live mode disabled: provider contracts and production identity are unverified')
        if self.mode == 'internal':
            from urllib.parse import urlsplit
            from zoneinfo import ZoneInfo
            origin = urlsplit(self.origin)
            if origin.scheme not in ('https', 'http') or not origin.hostname or origin.path not in ('', '/'):
                raise ValueError('An exact application origin is required')
            if origin.scheme != 'https' and origin.hostname not in ('localhost', '127.0.0.1', '::1'):
                raise ValueError('HTTPS is required for staff network access')
            if origin.scheme == 'https' and not self.secure_cookies:
                raise ValueError('HTTPS requires Secure session cookies')
            if self.database_url.endswith('demo.db'):
                raise ValueError('Internal mode requires a separate database')
            ZoneInfo(self.source_timezone)
            if not 30 <= self.sync_seconds <= 3600 or not 1 <= self.initial_sync_days <= 90:
                raise ValueError('Invalid sync interval or history window')
        if not 1 <= self.recovery_hours <= 168:
            raise ValueError('Recovery window must be 1–168 hours')
