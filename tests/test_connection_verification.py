import importlib.util
import json
import sys
from pathlib import Path

import httpx
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
from verify_leadsquared_connection import verify

VALUES = {'ACEFONE_API_TOKEN': 'test-acefone-token', 'LEADSQUARED_API_HOST': 'https://api-in21.leadsquared.com/v2/',
          'LEADSQUARED_ACCESS_KEY': 'test-access-value', 'LEADSQUARED_SECRET_KEY': 'test-secret-value'}


def test_metadata_check_uses_documented_endpoint_and_headers():
    def handler(request):
        assert request.method == 'GET'
        assert request.url.path == '/v2/LeadManagement.svc/LeadsMetaData.Get'
        assert not request.url.query
        assert request.headers['x-LSQ-SecretKey'] == VALUES['LEADSQUARED_SECRET_KEY']
        assert 'authorization' not in request.headers  # Acefone token is never sent to CRM.
        return httpx.Response(200, json=[{'SchemaName': 'Phone'}, {'SchemaName': 'Mobile'}])
    result = verify(VALUES, httpx.MockTransport(handler))
    assert result['verified'] and result['field_count'] == 2
    assert 'test-secret-value' not in json.dumps(result)


@pytest.mark.parametrize('code', [301, 401, 403, 429, 500])
def test_failures_are_redacted_and_redirects_not_followed(code):
    result = verify(VALUES, httpx.MockTransport(lambda r: httpx.Response(code, json={'error': 'test-secret-value'})))
    assert not result['verified']
    assert 'test-secret-value' not in json.dumps(result)


def test_success_http_with_wrong_schema_is_not_verified():
    result = verify(VALUES, httpx.MockTransport(lambda r: httpx.Response(200, json={'Status': 'Error'})))
    assert not result['verified']


def test_credentials_never_sent_to_unverified_subdomain():
    values = {**VALUES, 'LEADSQUARED_API_HOST': 'https://unverified.leadsquared.com'}
    def handler(request):
        raise AssertionError('No request to an unverified host is permitted')
    result = verify(values, httpx.MockTransport(handler))
    assert result['status'] == 'HOST_NOT_IN_VERIFIED_OFFICIAL_LIST'
