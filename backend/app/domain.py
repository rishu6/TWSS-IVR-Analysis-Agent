from datetime import UTC, datetime
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

EventType = Literal['INBOUND', 'IVR', 'DTMF', 'QUEUED', 'RING', 'NO_ANSWER', 'ANSWER',
                    'LEG_END', 'HOLD', 'TRANSFER', 'END']


class Event(BaseModel):
    """Our normalized synthetic contract. This is NOT an Acefone webhook schema."""
    model_config = ConfigDict(extra='forbid')
    event_id: str = Field(min_length=1, max_length=120)
    call_id: str = Field(pattern=r'^demo-[a-zA-Z0-9_-]+$', max_length=120)
    caller: str = Field(pattern=r'^\+[1-9][0-9]{7,14}$')
    did: str = Field(pattern=r'^\+[1-9][0-9]{7,14}$')
    direction: Literal['inbound', 'outbound'] = 'inbound'
    attempts_available: bool = True
    type: EventType
    at: AwareDatetime
    sequence: int = Field(default=0, ge=0)
    leg_id: str | None = Field(default=None, max_length=120)
    agent: str | None = Field(default=None, max_length=120)
    department: str | None = Field(default=None, max_length=120)
    node: str | None = Field(default=None, max_length=120)
    key: str | None = Field(default=None, max_length=10)
    reason: Literal['missed', 'ivr_exit', 'abandoned', 'unknown'] | None = None
    source_leg_id: str | None = Field(default=None, max_length=120)
    target_leg_id: str | None = Field(default=None, max_length=120)
    from_department: str | None = Field(default=None, max_length=120)

    @model_validator(mode='after')
    def valid_evidence(self):
        if self.type in {'RING', 'NO_ANSWER', 'ANSWER', 'LEG_END'} and not self.leg_id:
            raise ValueError('Leg events require explicit leg_id')
        if self.type == 'TRANSFER' and not (self.source_leg_id and self.target_leg_id):
            raise ValueError('Transfers require explicit source and target leg IDs')
        if not self.attempts_available and self.type in {'RING', 'NO_ANSWER'}:
            raise ValueError('Ring events contradict unavailable coverage')
        return self


def timestamp(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone(UTC)


def seconds(start, end):
    if not start or not end:
        return None
    elapsed = (timestamp(end) - timestamp(start)).total_seconds()
    return elapsed if elapsed >= 0 else None


def reduce_events(events: list[Event]):
    ordered = sorted(events, key=lambda e: (e.at.astimezone(UTC), e.sequence, e.event_id))
    if not ordered:
        raise ValueError('Cannot reduce empty history')
    base = ordered[0]
    legs, departments, transfers, warnings = {}, [], [], []
    starts = [e for e in ordered if e.type == 'INBOUND']
    answers = [e for e in ordered if e.type == 'ANSWER']
    ends = [e for e in ordered if e.type == 'END']
    iso = lambda e: e.at.astimezone(UTC).isoformat()
    for e in ordered:
        if e.department and e.department not in departments:
            departments.append(e.department)
        if e.type == 'TRANSFER':
            transfers.append(e.model_dump(mode='json'))
        if e.leg_id:
            leg = legs.setdefault(e.leg_id, {'id': e.leg_id, 'agent': None, 'department': None,
                                            'ring_at': None, 'answer_at': None, 'end_at': None,
                                            'disposition': 'UNKNOWN'})
            for key in ('agent', 'department'):
                value = getattr(e, key)
                if value:
                    if leg[key] and leg[key] != value:
                        warnings.append('Conflicting leg metadata')
                    leg[key] = value
            if e.type == 'RING':
                leg['ring_at'] = leg['ring_at'] or iso(e)
            if e.type == 'ANSWER':
                leg['answer_at'] = leg['answer_at'] or iso(e)
                leg['disposition'] = 'ANSWERED'
            if e.type in {'NO_ANSWER', 'LEG_END'}:
                leg['end_at'] = iso(e)
                if e.type == 'NO_ANSWER' and not leg['answer_at']:
                    leg['disposition'] = 'NO_ANSWER'
    for leg in legs.values():
        leg['talk_seconds'] = seconds(leg['answer_at'], leg['end_at'])
        leg['response_seconds'] = seconds(leg['ring_at'], leg['answer_at'])
        if leg['answer_at'] and leg['end_at'] and leg['talk_seconds'] is None:
            warnings.append('Contradictory leg timestamps')
    start = iso(starts[0]) if starts else None
    end = iso(ends[-1]) if ends else None
    answer = iso(answers[0]) if answers else None
    if not starts:
        warnings.append('Inbound start evidence pending')
    if answer and start and seconds(start, answer) is None:
        warnings.append('Answer predates inbound start')
    if end and start and seconds(start, end) is None:
        warnings.append('End predates inbound start')
    if answers:
        status = 'ANSWERED'
    elif not ends:
        status = 'IN_PROGRESS'
    elif ends[-1].reason == 'missed':
        status = 'MISSED'
    elif ends[-1].reason == 'ivr_exit' and not legs:
        status = 'IVR_ONLY'
    elif ends[-1].reason == 'abandoned':
        status = 'ABANDONED'
    else:
        status = 'UNKNOWN'
    return {'id': base.call_id, 'caller': base.caller, 'did': base.did, 'direction': base.direction,
            'status': status, 'started_at': start, 'answered_at': answer, 'ended_at': end,
            'primary_department': departments[0] if departments else None, 'departments': departments,
            'answering_agent': answers[-1].agent if answers else None, 'legs': list(legs.values()),
            'transfers': transfers, 'attempts_available': base.attempts_available,
            'missed_attempts': sum(l['disposition'] == 'NO_ANSWER' for l in legs.values()) if base.attempts_available else None,
            'ring_attempts': sum(l['ring_at'] is not None for l in legs.values()) if base.attempts_available else None,
            'first_response_seconds': seconds(start, answer), 'duration_seconds': seconds(start, end),
            'warnings': sorted(set(warnings)), 'recording_status': 'unavailable from provider',
            'synthetic': True, 'events': [e.model_dump(mode='json') for e in ordered]}
