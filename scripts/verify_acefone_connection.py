"""Read-only, one-record CDR capability check. No values/customer data printed.

Contract discovered in official https://docs.acefone.in/llms.txt:
https://docs.acefone.in/reference/call-detail-records-2.md
Authentication: https://docs.acefone.in/docs/using-managing-api-tokens
"""
import json
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx

from check_integration_config import read_config, configured


def verify(values, transport=None):
    if not configured(values.get('ACEFONE_API_TOKEN', '')):
        return {'verified': False, 'status': 'TOKEN_MISSING'}
    end = datetime.now(ZoneInfo('Asia/Kolkata'))
    params = {'from_date': (end-timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S'),
              'to_date': end.strftime('%Y-%m-%d %H:%M:%S'), 'page': '1', 'limit': '1', 'direction': 'inbound'}
    try:
        with httpx.Client(timeout=30, follow_redirects=False, trust_env=False, transport=transport) as client:
            response = client.get('https://api.acefone.in/v1/call/records', params=params,
                headers={'Authorization': 'Bearer '+values['ACEFONE_API_TOKEN'], 'Accept':'application/json'})
    except httpx.RequestError:
        return {'verified': False, 'status': 'NETWORK_OR_TLS_ERROR'}
    result = {'provider':'acefone', 'verified':False, 'http_status':response.status_code}
    if response.status_code != 200:
        return {**result, 'status':'PROVIDER_REJECTED_REQUEST'}
    try:
        body = response.json()
    except ValueError:
        return {**result, 'status':'INVALID_JSON'}
    if not isinstance(body, dict) or not isinstance(body.get('results'), list):
        return {**result, 'status':'UNEXPECTED_SCHEMA'}
    rows = body['results']
    sample = rows[0] if rows and isinstance(rows[0], dict) else {}
    # Shapes only. No IDs, phone numbers, agent/customer names, URLs or payloads.
    return {**result, 'verified':True, 'status':'READ_ONLY_CDR_VERIFIED', 'sample_received':bool(sample),
            'top_level_fields':sorted(body.keys()),
            'sample_field_types':{k:type(v).__name__ for k,v in sample.items()},
            'flow_entry_shapes':sorted({','.join(sorted(e.keys())) for e in sample.get('call_flow',[]) if isinstance(e,dict)}),
            'flow_types':sorted({str(e.get('type')) for e in sample.get('call_flow',[]) if isinstance(e,dict)}),
            'missed_agent_shapes':sorted({','.join(sorted(e.keys())) for e in sample.get('missed_agents',[]) if isinstance(e,dict)})}


if __name__=='__main__':
    result = verify(read_config(Path(__file__).resolve().parents[1]/'.env.integrations'))
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['verified'] else 1)
