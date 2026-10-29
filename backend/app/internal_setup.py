"""Initialize a separate local database and a one-time administrator password."""
import os
import secrets
from pathlib import Path

from sqlalchemy import select

from .config import Settings
from .db import User, database
from .passwords import hash_password


def setup():
    settings=Settings();settings.validate()
    if settings.mode!='internal':raise RuntimeError('Internal mode required')
    engine,sessions=database(settings.database_url)
    with sessions.begin() as db:
        if not db.scalar(select(User).where(User.role=='Admin',User.active==True)):
            password=secrets.token_urlsafe(24)
            path=Path('.runtime/first-login.txt')
            path.parent.mkdir(mode=0o700,exist_ok=True)
            # Never overwrite an unread bootstrap credential.
            fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
            with os.fdopen(fd,'w') as file:
                file.write('Username: localadmin\nTemporary password: '+password+'\nChange at first sign-in. Delete this file afterwards.\n')
            db.add(User(username='localadmin',display_name='Local Admin',role='Admin',password_hash=hash_password(password),
                        active=True,must_change_password=True,failed_attempts=0))
            print('Local Admin created. Open .runtime/first-login.txt locally for the temporary password.')
        else:print('Existing administrator preserved.')
    engine.dispose()


if __name__=='__main__':setup()
