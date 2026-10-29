from datetime import UTC, datetime, timedelta

import phonenumbers
from sqlalchemy import delete

from .db import Lead, LeadMatch, LeadPhone, now
from .domain import timestamp


def normalize_phone(raw, region='IN'):
    try:
        parsed = phonenumbers.parse(raw, region)
    except phonenumbers.NumberParseException as exc:
        raise ValueError('Invalid phone number') from exc
    if not phonenumbers.is_valid_number(parsed):
        raise ValueError('Invalid phone number')
    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)


def store_leads(db, candidates):
    for candidate in candidates:
        row = db.get(Lead, candidate['id'])
        fields = {key: candidate[key] for key in ('id', 'display_name', 'current_stage', 'current_owner', 'source')}
        fields['created_at'] = timestamp(candidate['created_at'])
        fields['last_synced_at'] = now()
        if not row:
            row = Lead(**fields)
            db.add(row)
        else:
            for key, value in fields.items():
                setattr(row, key, value)
        db.flush()
        db.execute(delete(LeadPhone).where(LeadPhone.lead_id == row.id))
        for number in set(normalize_phone(p) for p in candidate['phones']):
            db.add(LeadPhone(lead_id=row.id, normalized_number=number))
    db.flush()


def enrich(db, call, adapter, force=False, clock=None):
    clock = clock or datetime.now(UTC)
    old = call.projection.get('crm', {})
    attempt = old.get('attempts', 0)
    if not force:
        if attempt >= 5 and old.get('status', '').startswith('ERROR'):
            return old
        if old.get('next_retry_at') and timestamp(old['next_retry_at']) > clock:
            return old
    try:
        phone = normalize_phone(call.caller_e164)
        candidates = adapter.lookup(phone)
        # Deduplicate lead IDs, preserving every distinct candidate.
        candidates = list({lead['id']: lead for lead in candidates}.values())
        store_leads(db, candidates)
        db.execute(delete(LeadMatch).where(LeadMatch.call_id == call.id))
        status = 'MULTIPLE_MATCHES' if len(candidates) > 1 else 'MATCHED' if candidates else 'NO_MATCH'
        for lead in candidates:
            db.add(LeadMatch(call_id=call.id, lead_id=lead['id'], match_status=status))
        result = {'status': status, 'candidates': [{k: v for k, v in lead.items() if k != 'phones'} for lead in candidates],
                  'snapshot_source': 'current only', 'synced_at': clock.isoformat(),
                  'attempts': attempt + 1, 'next_retry_at': None, 'error': None}
    except (ConnectionError, TimeoutError):
        attempt += 1
        result = {'status': 'ERROR_RETRY_EXHAUSTED' if attempt >= 5 else 'ERROR', 'candidates': old.get('candidates', []),
                  'snapshot_source': 'current only', 'synced_at': old.get('synced_at'), 'attempts': attempt,
                  'next_retry_at': (clock + timedelta(seconds=min(30 * 2**(attempt-1), 900))).isoformat() if attempt < 5 else None,
                  'error': 'CRM unavailable; telephony remains available'}
    except ValueError:
        result = {'status': 'INVALID_PHONE', 'candidates': [], 'snapshot_source': 'current only',
                  'error': 'Phone cannot be normalized', 'attempts': attempt + 1, 'next_retry_at': None, 'synced_at': None}
    call.projection = {**call.projection, 'crm': result}
    return result
