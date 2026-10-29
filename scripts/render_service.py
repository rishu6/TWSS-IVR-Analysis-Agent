"""Create/manage only the project's explicitly free Render service.

Private inputs: .env.render and .env.integrations. Private service metadata:
.runtime/render/deployment.json. Never prints provider secrets or DB URLs.
"""
import json
import hashlib
import os
import secrets
import sys
from pathlib import Path
import httpx

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.credentials import read_env,load_credentials

REPO='https://github.com/rishu6/TWSS-IVR-Analysis-Agent'
STATE=ROOT/'.runtime/render/deployment.json'


def request(client,method,path,**kwargs):
    response=client.request(method,'https://api.render.com/v1'+path,**kwargs)
    if response.status_code not in (200,201,202,204):
        raise RuntimeError(f'Render request failed with HTTP {response.status_code}')
    return response.json() if response.content else {}


def create(client,settings):
    if STATE.exists():return json.loads(STATE.read_text())
    database_url=settings.get('DATABASE_URL','')
    if not database_url.startswith(('postgres://','postgresql://','postgresql+psycopg://')):
        raise ValueError('Save the Neon PostgreSQL DATABASE_URL before service creation')
    owners=request(client,'GET','/owners',params={'limit':20})
    if len(owners)!=1:raise ValueError('Select the Render workspace explicitly before deployment')
    owner=owners[0]['owner']['id']
    existing=request(client,'GET','/services',params={'ownerId':owner,'limit':100})
    if any(row['service']['name']=='twss-ivr' for row in existing):
        raise ValueError('A service named twss-ivr already exists; inspect it before creating another')
    providers=load_credentials(ROOT/'.env.integrations')
    env={**providers,'DATABASE_URL':database_url,'APP_MODE':'internal','SECURE_COOKIES':'true',
        'RUNTIME_DIRECTORY':'/tmp/twss','MIGRATION_PENDING':'true','AUTO_SYNC':'false',
        'BOOTSTRAP_ADMIN_PASSWORD':secrets.token_urlsafe(32)}
    body={'type':'web_service','name':'twss-ivr','ownerId':owner,'repo':REPO,'branch':'main',
        'autoDeployTrigger':'off','envVars':[{'key':key,'value':value} for key,value in env.items()],
        'serviceDetails':{'runtime':'docker','plan':'free','region':'singapore','numInstances':1,
            'healthCheckPath':'/healthz','envSpecificDetails':{'dockerfilePath':'./Dockerfile','dockerContext':'.'}}}
    if body['serviceDetails']['plan']!='free' or 'disk' in body['serviceDetails']:
        raise ValueError('Only a free service without a disk is authorized')
    result=request(client,'POST','/services',json=body)
    service=result['service']
    state={'service_id':service['id'],'url':service['serviceDetails']['url'],'owner_id':owner,
        'deploy_id':result.get('deployId'),'plan':'free',
        'database_fingerprint':hashlib.sha256(database_url.encode()).hexdigest()}
    STATE.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    fd=os.open(STATE,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    with os.fdopen(fd,'w') as file:json.dump(state,file)
    return state


def main():
    settings=read_env(ROOT/'.env.render')
    action=sys.argv[1] if len(sys.argv)>1 else 'status'
    with httpx.Client(headers={'Authorization':'Bearer '+settings['RENDER_API_KEY'],'Accept':'application/json'},
                      timeout=45,follow_redirects=False) as client:
        if action=='create':print(create(client,settings));return
        state=json.loads(STATE.read_text());id=state['service_id']
        if action=='status':
            rows=request(client,'GET',f'/services/{id}/deploys',params={'limit':3})
            print({'service_id':id,'url':state['url'],'deploys':[{'id':r['deploy']['id'],'status':r['deploy']['status']} for r in rows]})
        elif action=='activate':
            proof=json.loads((ROOT/'.runtime/render/migration-verified.json').read_text())
            if proof['database_fingerprint']!=state.get('database_fingerprint'):
                raise ValueError('Database migration must be verified before activation')
            # Only run after imported rows/accounts have been verified.
            request(client,'PUT',f'/services/{id}/env-vars/AUTO_SYNC',json={'value':'true'})
            request(client,'PUT',f'/services/{id}/env-vars/MIGRATION_PENDING',json={'value':'false'})
            result=request(client,'POST',f'/services/{id}/deploys',json={'clearCache':'do_not_clear'})
            print({'deploy_id':result['id'],'status':result['status'],'url':state['url']})
        else:raise ValueError('Unknown Render action')


if __name__=='__main__':
    try:main()
    except Exception as exc:
        print({'render_action':'failed','error_type':type(exc).__name__})
        raise SystemExit(1)
