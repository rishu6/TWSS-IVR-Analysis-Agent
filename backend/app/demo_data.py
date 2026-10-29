"""Fictional people and reserved North American example numbers. No calls are placed."""
from datetime import UTC, datetime, timedelta

from .domain import Event

ANCHOR = datetime(2026, 10, 27, 4, 30, tzinfo=UTC)
DID = '+12025550199'


def scenario(call_id, phone, specs, offset=0, coverage=True, direction='inbound'):
    return [Event(event_id=f'{call_id}-{i:03}', call_id=call_id, caller=phone, did=DID,
                  direction=direction, attempts_available=coverage, type=kind,
                  at=ANCHOR + timedelta(seconds=offset + second), sequence=i, **fields)
            for i, (second, kind, fields) in enumerate(specs)]


def four_agents():
    specs = [(0, 'INBOUND', {}), (2, 'IVR', {'node': 'Welcome menu'}),
             (5, 'DTMF', {'node': 'Welcome menu', 'key': '1'}),
             (6, 'QUEUED', {'department': 'Sales'})]
    for i, agent in enumerate(['Priya Shah', 'Arjun Mehta', 'Sara Khan', 'Dev Patel']):
        leg = {'leg_id': f'leg-{i+1}', 'agent': agent, 'department': 'Sales'}
        specs.append((10 + 22*i, 'RING', leg))
        specs.append((30 + 22*i if i < 3 else 80, 'NO_ANSWER' if i < 3 else 'ANSWER', leg))
    specs.extend([(200, 'LEG_END', {'leg_id': 'leg-4', 'agent': 'Dev Patel', 'department': 'Sales'}),
                  (201, 'END', {'reason': 'unknown'})])
    return scenario('demo-four-agents', '+12025550101', specs)


def fixtures():
    events = four_agents()
    events += scenario('demo-ivr-exit', '+12025550102', [
        (0, 'INBOUND', {}), (2, 'IVR', {'node': 'Welcome menu'}), (16, 'END', {'reason': 'ivr_exit'})], offset=600)
    events += scenario('demo-transfer', '+12025550103', [
        (0, 'INBOUND', {}), (5, 'QUEUED', {'department': 'Sales'}),
        (8, 'RING', {'leg_id': 'sales-leg', 'agent': 'Dev Patel', 'department': 'Sales'}),
        (12, 'ANSWER', {'leg_id': 'sales-leg', 'agent': 'Dev Patel', 'department': 'Sales'}),
        (55, 'HOLD', {'leg_id': 'sales-leg'}),
        (60, 'TRANSFER', {'source_leg_id': 'sales-leg', 'target_leg_id': 'support-leg',
                          'from_department': 'Sales', 'department': 'Support'}),
        (60, 'LEG_END', {'leg_id': 'sales-leg'}),
        (61, 'RING', {'leg_id': 'support-leg', 'agent': 'Neha Rao', 'department': 'Support'}),
        (66, 'ANSWER', {'leg_id': 'support-leg', 'agent': 'Neha Rao', 'department': 'Support'}),
        (180, 'LEG_END', {'leg_id': 'support-leg'}), (181, 'END', {'reason': 'unknown'})], offset=1200)
    events += scenario('demo-missed', '+12025550104', [
        (0, 'INBOUND', {}), (3, 'QUEUED', {'department': 'Support'}),
        (5, 'RING', {'leg_id': 'support-1', 'agent': 'Neha Rao', 'department': 'Support'}),
        (25, 'NO_ANSWER', {'leg_id': 'support-1'}), (26, 'END', {'reason': 'missed'})], offset=1800)
    events += scenario('demo-callback', '+12025550104', [
        (0, 'INBOUND', {}), (5, 'RING', {'leg_id': 'callback-1', 'agent': 'Neha Rao', 'department': 'Support'}),
        (10, 'ANSWER', {'leg_id': 'callback-1', 'agent': 'Neha Rao', 'department': 'Support'}),
        (90, 'LEG_END', {'leg_id': 'callback-1'}), (91, 'END', {'reason': 'unknown'})], offset=2400, direction='outbound')
    events += scenario('demo-no-ring-data', '+12025550105', [
        (0, 'INBOUND', {}), (15, 'ANSWER', {'leg_id': 'known-answer', 'agent': 'Sara Khan', 'department': 'Sales'}),
        (100, 'LEG_END', {'leg_id': 'known-answer'}), (101, 'END', {'reason': 'unknown'})], offset=3000, coverage=False)
    events += scenario('demo-live', '+12025550106', [
        (0, 'INBOUND', {}), (4, 'IVR', {'node': 'Welcome menu'}),
        (9, 'QUEUED', {'department': 'Admissions'})], offset=3600)
    events += scenario('demo-unknown', '+12025550107', [
        (0, 'INBOUND', {}), (5, 'END', {'reason': 'unknown'})], offset=4200)
    events += scenario('demo-abandoned', '+12025550108', [
        (0, 'INBOUND', {}), (2, 'QUEUED', {'department': 'Admissions'}),
        (20, 'END', {'reason': 'abandoned'})], offset=4800)
    return events


def leads():
    rows = [
        ('lead-101', 'Avery Morgan', '+12025550101', 'Qualified', 'Mira Sen', 'Website'),
        ('lead-103', 'Jordan Lee', '+12025550103', 'Customer', 'Mira Sen', 'Referral'),
        ('lead-104a', 'Casey Taylor', '+12025550104', 'New', 'Rohan Das', 'Campaign'),
        ('lead-104b', 'Casey Taylor · duplicate', '+12025550104', 'Contacted', 'Mira Sen', 'Import'),
        ('lead-105', 'Alex Quinn', '+12025550105', 'Qualified', 'Rohan Das', 'Website'),
    ]
    return [dict(id=id, display_name=name, phones=[phone], created_at='2026-09-21T06:30:00+00:00',
                 current_stage=stage, current_owner=owner, source=source)
            for id, name, phone, stage, owner, source in rows]
