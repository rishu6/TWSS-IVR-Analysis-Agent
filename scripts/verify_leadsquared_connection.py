"""One read-only metadata request; never prints credentials or provider payloads.

Contract: https://apidocs.leadsquared.com/meta-data/
Header authentication: https://apidocs.leadsquared.com/authentication/
"""
import json
from pathlib import Path
from urllib.parse import urlsplit

import httpx

from check_integration_config import check, read_config

# Independently verified at https://apidocs.leadsquared.com/api-host/
TRUSTED_API_HOSTS = frozenset({'api.leadsquared.com', 'api-us11.leadsquared.com',
    'api-in21.leadsquared.com', 'api-in22.leadsquared.com', 'api-me61.leadsquared.com',
    'api-ir31.leadsquared.com', 'api-ca12.leadsquared.com'})


def verify(values, transport=None):
    if not check(values)['ready_for_account_validation']:
        return {'provider': 'leadsquared', 'verified': False, 'status': 'CONFIGURATION_INCOMPLETE'}
    host = urlsplit(values['LEADSQUARED_API_HOST'])
    if host.hostname not in TRUSTED_API_HOSTS:
        return {'provider': 'leadsquared', 'verified': False, 'status': 'HOST_NOT_IN_VERIFIED_OFFICIAL_LIST'}
    url = f'https://{host.netloc}/v2/LeadManagement.svc/LeadsMetaData.Get'
    headers = {'x-LSQ-AccessKey': values['LEADSQUARED_ACCESS_KEY'],
               'x-LSQ-SecretKey': values['LEADSQUARED_SECRET_KEY'], 'Accept': 'application/json'}
    try:
        with httpx.Client(timeout=20, follow_redirects=False, trust_env=False, transport=transport) as client:
            response = client.get(url, headers=headers)
    except httpx.RequestError:
        return {'provider': 'leadsquared', 'verified': False, 'status': 'NETWORK_OR_TLS_ERROR'}
    result = {'provider': 'leadsquared', 'verified': False, 'http_status': response.status_code}
    if response.status_code != 200:
        result['status'] = {401: 'AUTHENTICATION_OR_HOST_REJECTED', 403: 'ACCESS_DENIED',
                            429: 'RATE_LIMITED'}.get(response.status_code, 'PROVIDER_RESPONSE_REJECTED')
        return result
    try:
        data = response.json()
    except ValueError:
        return {**result, 'status': 'INVALID_JSON_RESPONSE'}
    if not isinstance(data, list) or not data or not all(isinstance(row, dict) and isinstance(row.get('SchemaName'), str) for row in data):
        return {**result, 'status': 'UNEXPECTED_METADATA_RESPONSE'}
    fields = {row['SchemaName'] for row in data}
    return {**result, 'verified': True, 'status': 'READ_ONLY_METADATA_VERIFIED', 'field_count': len(data),
            'phone_field_present': 'Phone' in fields, 'mobile_field_present': 'Mobile' in fields,
            'live_dashboard_enabled': False}


if __name__ == '__main__':
    try:
        values = read_config(Path(__file__).resolve().parents[1] / '.env.integrations')
        result = verify(values)
    except (OSError, ValueError):
        result = {'provider': 'leadsquared', 'verified': False, 'status': 'CONFIGURATION_ERROR'}
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['verified'] else 1)
