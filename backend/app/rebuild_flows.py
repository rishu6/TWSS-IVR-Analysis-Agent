"""Upgrade derived flows from restricted stored CDRs without altering provider history."""
from sqlalchemy import or_,select

from .cdr import store_record
from .config import Settings
from .db import Call,CallEvent,database
from .mappings import apply_mappings


def rebuild(sessions,timezone='Asia/Kolkata'):
    updated=unavailable=0
    with sessions.begin() as db:
        rows=db.scalars(select(Call).where(Call.provider=='acefone',or_(
            Call.projection['projection_version'].as_integer()==None,
            Call.projection['projection_version'].as_integer()!=3))).all()
        for call in rows:
            snapshot=db.scalar(select(CallEvent).where(CallEvent.call_id==call.id,CallEvent.provider=='acefone')
                .order_by(CallEvent.received_at.desc(),CallEvent.id.desc()).limit(1))
            if not snapshot or not snapshot.payload.get('call_id'):
                unavailable+=1;continue
            store_record(db,snapshot.payload,timezone);updated+=1
        apply_mappings(db)
    return updated,unavailable


if __name__=='__main__':
    settings=Settings();settings.validate()
    if settings.mode!='internal':raise SystemExit('Internal mode required')
    engine,sessions=database(settings.database_url)
    updated,missing=rebuild(sessions,settings.source_timezone)
    engine.dispose()
    print(f'Flow evidence upgraded for {updated} stored calls; {missing} lack retained source payloads.')
