"""Consistent SQLite backup to a private local directory; never copies credentials."""
import os
import sqlite3
from datetime import UTC, datetime
from pathlib import Path


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
        path.unlink(missing_ok=True)
        raise
    return path


if __name__=='__main__':
    root=Path(__file__).resolve().parents[1]
    stamp=datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')
    result=backup(root/'.runtime/internal.db',root/f'.runtime/backups/internal-{stamp}.db')
    print('Private database backup created:',result)
