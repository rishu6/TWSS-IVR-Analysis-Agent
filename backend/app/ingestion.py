import hashlib
import json
from datetime import UTC

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from .db import Call, CallEvent, CallLeg, IntegrationEvent, SyncJob, now
from .domain import Event, reduce_events


def ingest(db, incoming: list[Event]):
    accepted = duplicates = 0
    insert = sqlite_insert if db.bind.dialect.name == 'sqlite' else pg_insert
    # Canonical lock order avoids deadlocks between batches on PostgreSQL.
    for event in sorted(incoming, key=lambda e: (e.call_id, e.event_id)):
        payload = event.model_dump(mode='json')
        canonical = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        hash_value = hashlib.sha256(canonical.encode()).hexdigest()
        db.execute(insert(Call).values(id=event.call_id, provider='synthetic', provider_call_id=event.call_id,
            caller_e164=event.caller, dialed_did=event.did, direction=event.direction,
            final_status='UNKNOWN', projection={}).on_conflict_do_nothing(index_elements=['id']))
        root = db.scalar(select(Call).where(Call.id == event.call_id).with_for_update())
        if (root.caller_e164, root.dialed_did, root.direction) != (event.caller, event.did, event.direction):
            raise ValueError('Conflicting root metadata')
        if root.projection and root.projection['attempts_available'] != event.attempts_available:
            raise ValueError('Conflicting ring coverage')
        event_key = hashlib.sha256(('synthetic:' + event.event_id).encode()).hexdigest()
        previous = db.get(CallEvent, event_key)
        if previous:
            if previous.dedupe_hash != hash_value:
                raise ValueError('Conflicting payload for event ID')
            duplicates += 1
            db.add(IntegrationEvent(provider='synthetic', payload=payload, status='DUPLICATE'))
            continue
        db.add(CallEvent(id=event_key, provider='synthetic', provider_event_id=event.event_id,
                         call_id=event.call_id, event_type=event.type, event_at=event.at.astimezone(UTC),
                         dedupe_hash=hash_value, payload=payload))
        db.add(IntegrationEvent(provider='synthetic', payload=payload, status='PROCESSED'))
        db.flush()
        history = db.scalars(select(CallEvent).where(CallEvent.call_id == event.call_id)).all()
        projection = reduce_events([Event.model_validate(row.payload) for row in history])
        if 'crm' in root.projection:
            projection['crm'] = root.projection['crm']
        root.projection = projection
        root.started_at = next((e.event_at for e in history if e.event_type == 'INBOUND'), None)
        root.final_status = projection['status']
        db.execute(delete(CallLeg).where(CallLeg.call_id == root.id))
        for leg in projection['legs']:
            db.add(CallLeg(id=f'{root.id}:{leg["id"]}', call_id=root.id, provider_leg_id=leg['id'],
                           agent=leg['agent'], department=leg['department'], evidence=leg))
        db.flush()
        accepted += 1
    return {'accepted': accepted, 'duplicates': duplicates}


def backfill(sessions, client, kind='backfill'):
    with sessions() as db:
        job = SyncJob(provider='synthetic', kind=kind, status='RUNNING')
        db.add(job)
        db.commit()
        job_id = job.id
    cursor = None
    try:
        while True:
            events, next_cursor = client.history(cursor)
            with sessions.begin() as db:
                ingest(db, events)
                job = db.get(SyncJob, job_id)
                job.cursor = next_cursor
            cursor = next_cursor
            if cursor is None:
                break
        with sessions.begin() as db:
            job = db.get(SyncJob, job_id)
            job.status, job.completed_at = 'SUCCEEDED', now()
    except Exception:
        with sessions.begin() as db:
            job = db.get(SyncJob, job_id)
            job.status, job.error, job.completed_at = 'ERROR', 'Synthetic sync failed; inspect restricted event history', now()
        raise
    return job_id
