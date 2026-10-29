"""Single-instance HTTPS deployment entrypoint; never seeds synthetic data."""
import fcntl
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1]


def configure(environment,root=ROOT):
    origin=environment.get('APP_ORIGIN') or environment.get('RENDER_EXTERNAL_URL')
    parsed=urlsplit(origin or '')
    if parsed.scheme!='https' or not parsed.hostname or parsed.path not in ('','/') or parsed.query or parsed.fragment or parsed.username:
        raise ValueError('Cloud deployment requires its exact HTTPS APP_ORIGIN or RENDER_EXTERNAL_URL')
    runtime=Path(environment.get('RUNTIME_DIRECTORY','/tmp/twss'))
    if not runtime.is_absolute():raise ValueError('Cloud RUNTIME_DIRECTORY must be an absolute private path')
    port=int(environment.get('PORT','10000'))
    if not 1<=port<=65535:raise ValueError('Invalid PORT')
    environment['APP_MODE']='internal';environment['APP_ORIGIN']=origin.rstrip('/')
    environment['SECURE_COOKIES']='true';environment['RUNTIME_DIRECTORY']=str(runtime)
    from_url=environment.get('DATABASE_URL','')
    if not from_url.startswith(('postgres://','postgresql://','postgresql+psycopg://')):
        raise ValueError('Free cloud deployment requires a persistent PostgreSQL DATABASE_URL')
    if from_url.startswith('postgres://'):from_url='postgresql+psycopg://'+from_url[len('postgres://'):]
    elif from_url.startswith('postgresql://'):from_url='postgresql+psycopg://'+from_url[len('postgresql://'):]
    environment['DATABASE_URL']=from_url
    environment['STATIC_DIRECTORY']=str(root/'frontend/dist')
    environment['PYTHONPATH']=str(root/'backend')
    if environment.get('MIGRATION_PENDING','false').lower()=='true':environment['AUTO_SYNC']='false'
    return runtime,port


def main():
    os.chdir(ROOT);os.umask(0o077)
    runtime,port=configure(os.environ)
    runtime.mkdir(mode=0o700,parents=True,exist_ok=True);os.chmod(runtime,0o700)
    lock_fd=os.open(runtime/'server.lock',os.O_CREAT|os.O_RDWR,0o600)
    try:fcntl.flock(lock_fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:raise SystemExit('An instance already uses this data directory.')
    os.set_inheritable(lock_fd,True)
    sys.path.insert(0,str(ROOT/'backend'))
    from app.config import Settings
    from app.credentials import load_credentials
    settings=Settings();settings.validate();load_credentials(settings.integrations_file)
    if not (ROOT/'frontend/dist/index.html').is_file():raise SystemExit('Production frontend build is missing')
    subprocess.run([sys.executable,'-m','alembic','-c','backend/alembic.ini','upgrade','head'],check=True)
    subprocess.run([sys.executable,'-m','app.internal_setup'],check=True)
    subprocess.run([sys.executable,'-m','app.rebuild_flows'],check=True)
    print('TWSS IVR starting with persistent storage and individual accounts.',flush=True)
    os.execv(sys.executable,[sys.executable,'-m','uvicorn','app.main:app','--host','0.0.0.0','--port',str(port),
        '--no-access-log','--workers','1'])


if __name__=='__main__':main()
