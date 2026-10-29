"""No vendor URLs or vendor wire-field assumptions belong in demo adapters."""
from typing import Protocol

from .domain import Event


class AcefoneClient(Protocol):
    def history(self, cursor: str | None = None) -> tuple[list[Event], str | None]: ...


class LeadSquaredClient(Protocol):
    def lookup(self, normalized_phone: str) -> list[dict]: ...


from .provider_clients import LiveAcefoneClient, LiveLeadSquaredClient


class SyntheticAcefoneClient:
    def __init__(self, events: list[Event], page_size=25):
        self.events, self.page_size = events, page_size

    def history(self, cursor=None):
        offset = int(cursor or 0)
        page = self.events[offset:offset + self.page_size]
        next_cursor = str(offset + self.page_size) if offset + self.page_size < len(self.events) else None
        return page, next_cursor


class SyntheticLeadSquaredClient:
    def __init__(self, leads: list[dict], unavailable=False):
        self.leads, self.unavailable = leads, unavailable

    def lookup(self, normalized_phone):
        if self.unavailable:
            raise ConnectionError('Synthetic CRM outage')
        return [lead for lead in self.leads if normalized_phone in lead['phones']]
