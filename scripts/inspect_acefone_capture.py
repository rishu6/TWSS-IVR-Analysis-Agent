"""Compare CDR pagination/direction metadata; never prints customer records."""
import json
import sys
from datetime import datetime,timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from collections import Counter

root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'backend'))
from app.credentials import load_credentials
from app.provider_clients import LiveAcefoneClient

credentials=load_credentials(root/'.env.integrations')
client=LiveAcefoneClient(credentials['ACEFONE_API_TOKEN'])
day=datetime.now(ZoneInfo('Asia/Kolkata')).replace(hour=0,minute=0,second=0,microsecond=0)-timedelta(days=1)
try:
    summaries=[]
    for direction in (None,'inbound','outbound'):
        params={'from_date':day.strftime('%Y-%m-%d %H:%M:%S'),
                'to_date':(day+timedelta(days=1,seconds=-1)).strftime('%Y-%m-%d %H:%M:%S'),'page':'1','limit':'100'}
        if direction:params['direction']=direction
        data=client.transport.request('GET','/v1/call/records',params=params)
        summaries.append({'direction_filter':direction or 'unspecified','page':data.get('page'),
            'reported_limit':data.get('limit'),'count':data.get('count'),'size':data.get('size'),
            'rows_on_page':len(data.get('results',[])),
            'directions_on_page':dict(Counter(r.get('direction') for r in data.get('results',[])))})
    print(json.dumps({'period':'yesterday in IST','metadata':summaries},indent=2))
finally:client.close()
