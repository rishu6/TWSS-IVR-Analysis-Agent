"""Start the authenticated Mac installation, using a separate private data directory."""
import os
import subprocess
import sys
import fcntl
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
os.chdir(ROOT)
os.umask(0o077)
runtime=ROOT/'.runtime'
runtime.mkdir(mode=0o700,exist_ok=True)
os.chmod(runtime,0o700)
lock_fd=os.open(runtime/'server.lock',os.O_CREAT|os.O_RDWR,0o600)
try:fcntl.flock(lock_fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
except BlockingIOError:raise SystemExit('The internal app is already running.')
os.set_inheritable(lock_fd,True)
os.environ.setdefault('APP_MODE','internal')
os.environ.setdefault('APP_ORIGIN','http://localhost:8001')
os.environ.setdefault('DATABASE_URL','sqlite:///'+str(runtime/'internal.db'))
os.environ.setdefault('INTEGRATIONS_ENV_FILE',str(ROOT/'.env.integrations'))
os.environ.setdefault('STATIC_DIRECTORY',str(ROOT/'frontend/dist'))
os.environ['PYTHONPATH']=str(ROOT/'backend')
sys.path.insert(0,str(ROOT/'backend'))
from app.credentials import load_credentials
from app.config import Settings

settings=Settings();settings.validate()
load_credentials(settings.integrations_file)
if not (ROOT/'frontend/dist/index.html').exists():
    raise SystemExit('Build the frontend first: npm --prefix frontend run build')
subprocess.run([sys.executable,'-m','alembic','-c','backend/alembic.ini','upgrade','head'],check=True)
subprocess.run([sys.executable,'-m','app.internal_setup'],check=True)
subprocess.run([sys.executable,'-m','app.rebuild_flows'],check=True)
print('Internal workspace: http://localhost:8001 — individual accounts; no demo data.',flush=True)
os.execv(sys.executable,[sys.executable,'-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8001',
                        '--no-access-log','--workers','1'])
