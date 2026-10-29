from sqlalchemy import select

from .adapters import SyntheticAcefoneClient, SyntheticLeadSquaredClient
from .config import Settings
from .crm import enrich
from .db import Call, database
from .demo_data import fixtures, leads
from .ingestion import backfill


def seed(sessions):
    # Replay intentionally includes duplicate and out-of-order events.
    events = fixtures()
    backfill(sessions, SyntheticAcefoneClient(list(reversed(events)) + events[:3]), 'demo_seed')
    with sessions.begin() as db:
        for call in db.scalars(select(Call)):
            enrich(db, call, SyntheticLeadSquaredClient(leads(), unavailable=call.id == 'demo-no-ring-data'), force=True)


if __name__ == '__main__':
    settings = Settings()
    settings.validate()
    engine, sessions = database(settings.database_url)
    seed(sessions)
    engine.dispose()
    print('Synthetic demo seeded; no provider APIs called.')
