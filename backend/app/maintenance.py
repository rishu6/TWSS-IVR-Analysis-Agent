"""Private local backups and bounded raw-payload/session retention."""
import os
import sqlite3
from datetime import timedelta
from pathlib import Path

from sqlalchemy import delete,select,update
from sqlalchemy.engine import make_url

from .db import AuditLog,CallEvent,IntegrationEvent,LiveTicket,SessionToken,now


def backup(source,destination):
    if not Path(source).is_file():raise ValueError('Internal database does not exist')
    path=Path(destination)
    path.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    if path.exists():raise ValueError('Backup destination already exists')
    fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.close(fd)
    try:
        with sqlite3.connect(f'file:{Path(source).resolve()}?mode=ro',uri=True) as src,sqlite3.connect(path) as dst:
            src.backup(dst)
            if dst.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('Backup integrity check failed')
    except Exception:
        path.unlink(missing_ok=True);raise
    return path


def maintain(settings,sessions):
    with sessions.begin() as db:
        expired=select(SessionToken.token_hash).where(SessionToken.expires_at<now())
        db.execute(delete(LiveTicket).where(LiveTicket.session_hash.in_(expired)))
        db.execute(delete(LiveTicket).where(LiveTicket.expires_at<now()))
        db.execute(delete(SessionToken).where(SessionToken.expires_at<now()))
        cutoff=now()-timedelta(days=90)
        db.execute(delete(IntegrationEvent).where(IntegrationEvent.received_at<cutoff))
        # Keep event identity/order/hash and derived journey; expire raw payload only.
        db.execute(update(CallEvent).where(CallEvent.received_at<cutoff).values(payload={}))
    url=make_url(settings.database_url)
    if url.drivername.startswith('sqlite') and url.database and url.database!=':memory:':
        root=Path(url.database).resolve().parent
        target=root/'backups'/('auto-'+now().strftime('%Y%m%d')+'.db')
        if not target.exists():backup(url.database,target)
        for older in (root/'backups').glob('auto-????????.db'):
            if older.is_file() and older.stat().st_mtime<(now()-timedelta(days=7)).timestamp():
                older.unlink()
