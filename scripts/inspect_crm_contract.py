"""Inspect the shape of one documented read-only CRM page without printing records."""
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.credentials import load_credentials
from app.provider_clients import LiveLeadSquaredClient,ProviderError
from app.live_sync import normalized_lead

credentials=load_credentials(ROOT/'.env.integrations')
client=LiveLeadSquaredClient(credentials)
try:
    page=int(sys.argv[1]) if len(sys.argv)>1 else 1
    if not 1<=page<=1000:raise ValueError('Page outside diagnostic bounds')
    rows=client.page(page,size=1000)
    failures={}
    valid=0
    for row in rows:
        try:normalized_lead(row);valid+=1
        except Exception as exc:failures[type(exc).__name__]=failures.get(type(exc).__name__,0)+1
    print(json.dumps({'request_succeeded':True,'page':page,'rows_in_page':len(rows),'normalizable_rows':valid,
        'failure_types':failures,'required_field_types':{key:sorted({type(r.get(key)).__name__ for r in rows})
            for key in ('ProspectID','CreatedOn','Phone','Mobile','OwnerId')}}))
except Exception as exc:
    print(json.dumps({'request_succeeded':False,'error_type':type(exc).__name__,
        'safe_message':str(exc) if isinstance(exc,ProviderError) else 'Response could not be processed'}))
finally:client.close()
