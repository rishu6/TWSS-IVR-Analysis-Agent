"""Validate local credential presence without displaying values or making requests."""
import json
import shlex
from pathlib import Path
from urllib.parse import urlsplit

KEYS = ('ACEFONE_API_TOKEN', 'LEADSQUARED_API_HOST', 'LEADSQUARED_ACCESS_KEY', 'LEADSQUARED_SECRET_KEY')


def read_config(path):
    values = {}
    for line in Path(path).read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        key, sep, raw = stripped.partition('=')
        key = key.strip()
        if not sep or key not in KEYS:
            raise ValueError('Unexpected setting; use the supplied integration template')
        if key in values:
            raise ValueError('Duplicate setting in integration configuration')
        try:
            parts = shlex.split(raw, comments=True)
        except ValueError:
            raise ValueError('Invalid quoting in integration configuration') from None
        if len(parts) > 1:
            raise ValueError('Values containing whitespace must be quoted')
        values[key] = parts[0] if parts else ''
    return values


def configured(value):
    text = value.strip()
    return bool(text) and not any(s in text.lower() for s in ('<', '>', 'placeholder', 'replace-me', 'your-token', 'your-key'))


def valid_host(value):
    try:
        host = urlsplit(value)
        return bool(host.scheme == 'https' and host.hostname and host.hostname.endswith('.leadsquared.com')
                    and not host.username and not host.password and not host.query and not host.fragment
                    and host.port in (None, 443) and host.path in ('', '/', '/v2', '/v2/'))
    except ValueError:
        return False


def check(values):
    result = {key: configured(values.get(key, '')) for key in KEYS}
    result['LEADSQUARED_API_HOST'] = valid_host(values.get('LEADSQUARED_API_HOST', ''))
    return {'configured': result, 'ready_for_account_validation': all(result.values()),
            'credentials_verified': False, 'network_requests_made': False, 'live_dashboard_enabled': False}


if __name__ == '__main__':
    path = Path(__file__).resolve().parents[1] / '.env.integrations'
    try:
        result = check(read_config(path))
    except (OSError, ValueError):
        print('Configuration could not be validated. Check the file exists and uses the supplied template.')
        raise SystemExit(1)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['ready_for_account_validation'] else 1)
