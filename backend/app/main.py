import time
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from sqlalchemy import select
from collections import defaultdict, deque

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse

from . import auth
from .config import Settings
from .db import database, IntegrationState,SyncJob


def create_app(settings=None):
    settings = settings or Settings()
    settings.validate()
    @asynccontextmanager
    async def lifespan(app):
        tasks = []
        if settings.mode == 'internal' and settings.auto_sync:
            from .live_sync import LiveSync
            from .scheduler import repeat_sync
            app.state.live_sync = LiveSync(settings,app.state.sessions)
            worker=app.state.live_sync
            def delay():
                with app.state.sessions() as db:
                    state=db.get(IntegrationState,'leadsquared')
                    indexing=bool(state and state.status=='INDEXING')
                    pending=db.scalar(select(SyncJob.id).where(SyncJob.kind=='history',SyncJob.status.in_(['QUEUED','RUNNING'])).limit(1))
                return 2 if pending or (indexing and not worker.separate_crm) else settings.sync_seconds
            tasks.append(asyncio.create_task(repeat_sync(worker.run,delay)))
            if worker.separate_crm:
                tasks.append(asyncio.create_task(repeat_sync(worker.run_crm,lambda: settings.sync_seconds)))
                tasks.append(asyncio.create_task(repeat_sync(worker.run_matches,lambda: settings.sync_seconds)))
        yield
        for task in tasks: task.cancel()
        for task in tasks:
            try: await task
            except asyncio.CancelledError: pass
        app.state.engine.dispose()

    app = FastAPI(title='TWSS IVR', docs_url=None, redoc_url=None, openapi_url=None,lifespan=lifespan)
    app.state.settings = settings
    app.state.engine, app.state.sessions = database(settings.database_url)
    buckets = defaultdict(deque)

    @app.middleware('http')
    async def protection(request: Request, call_next):
        if settings.migration_pending and request.url.path!='/healthz':
            return JSONResponse({'detail':'TWSS IVR is being set up. Please try again shortly.'},status_code=503)
        # Same-origin cookie requests require an explicit CSRF header for writes.
        if request.method in {'POST', 'PUT', 'PATCH', 'DELETE'}:
            origin = request.headers.get('origin')
            if (origin and origin != settings.origin) or request.headers.get('x-csrf-protection') != '1':
                return JSONResponse({'detail': 'Same-origin CSRF check failed'}, status_code=403)
        key = (request.client.host if request.client else 'local', request.url.path == '/api/v1/auth/login')
        stamps = buckets[key]
        now = time.monotonic()
        while stamps and stamps[0] < now - 60:
            stamps.popleft()
        limit = 20 if key[1] else 240
        if request.url.path=='/healthz' and request.method=='GET':
            return await call_next(request)
        if len(stamps) >= limit:
            return JSONResponse({'detail': 'Rate limit exceeded'}, status_code=429, headers={'Retry-After': '60'})
        stamps.append(now)
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'no-referrer'
        return response

    @app.get('/healthz')
    def readiness():
        from sqlalchemy import text
        with app.state.engine.connect() as connection:connection.execute(text('SELECT 1'))
        return {'status':'ok'}

    app.include_router(auth.router)
    from .api import router
    app.include_router(router)
    from .accounts import router as accounts_router
    app.include_router(accounts_router)
    from .mappings import router as mappings_router
    app.include_router(mappings_router)
    from .history import router as history_router
    app.include_router(history_router)

    @app.get('/api/v1/integrations/health')
    def health(user=Depends(auth.principal),db=Depends(auth.session_db)):
        if settings.mode=='internal':
            states={key:db.get(IntegrationState,key) for key in ('acefone','leadsquared','system')}
            verified=all(states[key] and states[key].last_success_at for key in ('acefone','leadsquared'))
            return {'mode':'internal','synthetic':False,'live_verified':bool(verified and not (states['system'] and states['system'].status=='ERROR')),
                    **{key:row.status if row else 'PENDING' for key,row in states.items()},
                    'details':{key:{'status':row.status,'last_success_at':row.last_success_at,
                                   'last_attempt_at':row.last_attempt_at,'message':row.message,'details':row.details}
                               for key,row in states.items() if row}}
        return {'mode': 'demo', 'synthetic': True, 'acefone': 'DISABLED_UNVERIFIED_CONTRACT',
                'leadsquared': 'SYNTHETIC_ONLY', 'live_verified': False}

    @app.get('/api/v1/admin')
    def admin(user=Depends(auth.require('Admin'))):
        if settings.mode=='internal':
            return {'mode':'internal','integrations_enabled':True,'configuration':'Named accounts; read-only CDR polling and CRM index',
                    'poll_seconds':settings.sync_seconds,'recording_playback':False,'ring_coverage_verified':False}
        return {'mode': 'demo', 'integrations_enabled': False, 'configuration': 'Read-only demo; live setup blocked'}

    if settings.mode=='internal' and Path(settings.static_directory).is_dir():
        from fastapi.responses import FileResponse
        from fastapi.staticfiles import StaticFiles
        root=Path(settings.static_directory).resolve()
        if (root/'assets').is_dir():app.mount('/assets',StaticFiles(directory=root/'assets'),name='assets')
        @app.get('/{path:path}')
        def frontend(path:str):
            if path.startswith('api/'):
                from fastapi import HTTPException
                raise HTTPException(404,'Endpoint not found')
            return FileResponse(root/'index.html',headers={
                'Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'"})
    return app


app = create_app()
