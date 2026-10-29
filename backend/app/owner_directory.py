"""Resolve LeadSquared OwnerId through the documented read-only user directory."""
import re
from datetime import UTC,datetime,timedelta
from .db import IntegrationState
from .provider_clients import LiveLeadSquaredClient,ProviderError

PROVIDER='leadsquared-users'
OWNER_ID=re.compile(r'^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$',re.I)


def utc(value):
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def refresh_owner_directory(sessions,credentials,force=False,client_factory=None,clock=None):
    clock=clock or datetime.now(UTC)
    with sessions() as db:
        state=db.get(IntegrationState,PROVIDER)
        if state and not force:
            if state.status=='HEALTHY' and state.last_success_at and clock-utc(state.last_success_at)<timedelta(hours=1):
                return {'status':'CACHED','count':len(state.details.get('owners',{}))}
            if state.status=='ERROR' and state.last_attempt_at and clock-utc(state.last_attempt_at)<timedelta(minutes=5):
                return {'status':'RETRY_LATER','count':len(state.details.get('owners',{}))}
    client=None
    try:
        client=(client_factory or LiveLeadSquaredClient)(credentials)
        rows=client.users()
        owners={str(row['ID']).strip().casefold():' '.join(str(row.get(part) or '').strip() for part in ('FirstName','LastName')).strip()[:120]
                for row in rows}
        owners={key:value for key,value in owners.items() if value}
        with sessions.begin() as db:
            state=db.get(IntegrationState,PROVIDER)
            if not state:state=IntegrationState(provider=PROVIDER,status='HEALTHY',details={});db.add(state)
            state.status='HEALTHY';state.last_attempt_at=state.last_success_at=clock
            state.details={'owners':owners,'count':len(owners)}
            state.message='Lead owner names refreshed from official user directory'
        return {'status':'UPDATED','count':len(owners)}
    except Exception as exc:
        # No raw provider errors, credentials, emails or responses in status messages.
        with sessions.begin() as db:
            state=db.get(IntegrationState,PROVIDER)
            if not state:state=IntegrationState(provider=PROVIDER,status='ERROR',details={});db.add(state)
            state.status='ERROR';state.last_attempt_at=clock
            state.message='Owner name refresh failed; previous directory retained'
        return {'status':'ERROR','count':0}
    finally:
        if client:
            try:client.close()
            except Exception:pass


def owner_names(db):
    state=db.get(IntegrationState,PROVIDER)
    return state.details.get('owners',{}) if state else {}


def resolve_owner_name(owner,names):
    owner=str(owner or '').strip()
    if not owner or owner.casefold() in ('unknown','unavailable'):return None
    if OWNER_ID.fullmatch(owner):return names.get(owner.casefold())
    return owner  # Existing synthetic/direct-name values remain names.
