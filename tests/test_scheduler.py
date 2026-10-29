import asyncio
import threading
from app.scheduler import repeat_sync
from test_internal import internal


def test_scheduler_retries_transient_failure(monkeypatch):
    calls=[]
    async def sleep(seconds):
        assert seconds==60
        if len(calls)==2:raise asyncio.CancelledError
    def action():
        calls.append(1)
        if len(calls)==1:raise ConnectionError('private database URL')
    monkeypatch.setattr('app.scheduler.asyncio.sleep',sleep)
    async def check():
        try:await repeat_sync(action,lambda:60)
        except asyncio.CancelledError:pass
    asyncio.run(check())
    assert len(calls)==2


def test_cloud_telephony_does_not_wait_for_crm(internal,monkeypatch):
    from app.live_sync import LiveSync
    from dataclasses import replace
    worker=LiveSync(replace(internal.app.state.settings,database_url='postgresql+psycopg://unused'),internal.app.state.sessions)
    entered=threading.Event();release=threading.Event();polls=[]
    monkeypatch.setattr('app.live_sync.load_credentials',lambda _: {})
    monkeypatch.setattr('app.owner_directory.refresh_owner_directory',lambda *a,**k:None)
    monkeypatch.setattr('app.history.process_history',lambda *a:False)
    monkeypatch.setattr('app.maintenance.maintain',lambda *a:None)
    monkeypatch.setattr(worker,'state',lambda *a:None)
    def crm(_):
        entered.set();release.wait(5)
    monkeypatch.setattr(worker,'crm',crm)
    monkeypatch.setattr(worker,'telephony',lambda _:polls.append(1))
    thread=threading.Thread(target=worker.run_crm)
    thread.start()
    try:
        assert entered.wait(2)
        assert worker.run()=={'status':'FINISHED'}
        assert worker.run()=={'status':'FINISHED'}
        assert len(polls)==2
        assert worker.run_crm()=={'status':'ALREADY_RUNNING'}
    finally:
        release.set();thread.join(5)
