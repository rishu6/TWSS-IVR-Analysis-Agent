"""Scheduled synthetic reconciliation only; no network calls to providers."""
from celery import Celery
from sqlalchemy import select

from .adapters import SyntheticAcefoneClient, SyntheticLeadSquaredClient
from .config import Settings
from .crm import enrich
from .db import Call, database
from .demo_data import fixtures, leads
from .ingestion import backfill

settings = Settings()
settings.validate()
celery = Celery('callatlas', broker=settings.redis_url)
celery.conf.beat_schedule = {'synthetic-reconciliation': {'task': 'demo.reconcile', 'schedule': 60.0}}


@celery.task(name='demo.reconcile')
def reconcile():
    engine, sessions = database(settings.database_url)
    try:
        job_id = backfill(sessions, SyntheticAcefoneClient(fixtures()), kind='reconciliation')
        with sessions.begin() as db:
            for call in db.scalars(select(Call)):
                if call.projection.get('crm', {}).get('status') in {'PENDING', 'ERROR'}:
                    enrich(db, call, SyntheticLeadSquaredClient(leads(), unavailable=call.id == 'demo-no-ring-data'))
        return {'synthetic': True, 'job_id': job_id}
    finally:
        engine.dispose()
