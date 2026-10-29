"""Offline recovery for the Mac owner; password input is hidden and never echoed."""
import getpass
import sys
from pathlib import Path

root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'backend'))
from sqlalchemy import delete,select
from app.db import AuditLog,LiveTicket,SessionToken,User,database
from app.passwords import hash_password

username=input('Username to reset: ').strip().lower()
password=getpass.getpass('New temporary password (12+ characters): ')
if password!=getpass.getpass('Confirm: '):raise SystemExit('Passwords do not match')
encoded=hash_password(password)
engine,sessions=database('sqlite:///'+str(root/'.runtime/internal.db'))
with sessions.begin() as db:
    account=db.scalar(select(User).where(User.username==username))
    if not account:raise SystemExit('Account not found')
    account.password_hash=encoded;account.must_change_password=True;account.failed_attempts=0;account.locked_until=None
    tokens=select(SessionToken.token_hash).where(SessionToken.user_id==account.id)
    db.execute(delete(LiveTicket).where(LiveTicket.session_hash.in_(tokens)))
    db.execute(delete(SessionToken).where(SessionToken.user_id==account.id))
    db.add(AuditLog(role='Admin',action='offline_password_reset',resource=str(account.id)))
engine.dispose()
print('Password reset. Existing sessions revoked. The user must change it at sign-in.')
