"""Retry polling after transient database failures without losing the worker."""
import asyncio
import logging


async def repeat_sync(action, delay):
    while True:
        seconds = 60
        try:
            await asyncio.to_thread(action)
            seconds = delay()
        except Exception as exc:
            # URLs, credentials and provider response bodies must never enter logs.
            logging.getLogger(__name__).warning('Sync cycle will retry (%s)', type(exc).__name__)
        await asyncio.sleep(seconds)
