"""Read local settings without shell evaluation, logging or interpolation."""
import os
import shlex
from pathlib import Path


def read_env(path):
    values = {}
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        key, sep, raw = line.partition('=')
        if not sep or not key.strip().replace('_', '').isalnum():
            raise ValueError('Invalid local settings file')
        parts = shlex.split(raw, comments=True)
        if len(parts) > 1 or key.strip() in values:
            raise ValueError('Invalid or duplicate local setting')
        values[key.strip()] = parts[0] if parts else ''
    return values


def load_credentials(path):
    path = Path(path)
    if path.stat().st_mode & 0o077:
        raise ValueError('Credential file must be private (chmod 600)')
    values = read_env(path)
    names = ('ACEFONE_API_TOKEN', 'LEADSQUARED_API_HOST', 'LEADSQUARED_ACCESS_KEY', 'LEADSQUARED_SECRET_KEY')
    if any(not values.get(key) for key in names):
        raise ValueError('Provider credentials are incomplete')
    return values
