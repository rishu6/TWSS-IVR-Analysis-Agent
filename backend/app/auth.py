import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel

from .db import AuditLog, SessionToken, User
from .passwords import hash_password, verify_password

router = APIRouter(prefix='/api/v1/auth')


def digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


def utc(value):
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def session_db(request: Request):
    with request.app.state.sessions() as db:
        db.info['mode'] = request.app.state.settings.mode
        yield db


def principal(request: Request, db=Depends(session_db)):
    token = request.cookies.get('session', '')
    row = db.get(SessionToken, digest(token))
    if not row or utc(row.expires_at) <= datetime.now(UTC):
        raise HTTPException(401, 'Session missing or expired')
    if request.app.state.settings.mode == 'internal':
        account = db.get(User, row.user_id) if row.user_id else None
        if not account or not account.active:
            raise HTTPException(401, 'Account unavailable')
        row.role = account.role
        if account.must_change_password and request.url.path not in {
                '/api/v1/auth/me', '/api/v1/auth/change-password', '/api/v1/auth/logout'}:
            raise HTTPException(403, 'Change your temporary password before accessing the workspace')
    return row


def require(*roles):
    def authorize(request:Request,user=Depends(principal),db=Depends(session_db)):
        if user.role not in roles:
            db.add(AuditLog(role=user.role,user_id=user.user_id,action='access_denied',resource=request.url.path[:120]))
            db.commit()
            raise HTTPException(403, 'Role not permitted')
        return user
    return authorize


class Login(BaseModel):
    role: Literal['Admin', 'Manager', 'Viewer'] | None = None
    username: str | None = None
    password: str


@router.post('/login')
def login(body: Login, request: Request, response: Response, db=Depends(session_db)):
    account = None
    role = body.role
    if request.app.state.settings.mode == 'internal':
        from sqlalchemy import select
        account = db.scalar(select(User).where(User.username == (body.username or '').strip().lower()).with_for_update())
        locked = account and account.locked_until and utc(account.locked_until) > datetime.now(UTC)
        if not account or not account.active or locked or not verify_password(body.password, account.password_hash):
            if account and not locked:
                account.failed_attempts += 1
                if account.failed_attempts >= 5:
                    account.locked_until = datetime.now(UTC) + timedelta(minutes=15)
                db.add(AuditLog(role='Unknown', user_id=account.id, action='login_failed', resource='account'))
                db.commit()
            raise HTTPException(401, 'Invalid credentials or temporarily locked account')
        account.failed_attempts, account.locked_until = 0, None
        role = account.role  # A client-supplied role never grants privileges.
    elif not role or not secrets.compare_digest(body.password, request.app.state.settings.demo_password):
        raise HTTPException(401, 'Invalid demo credentials')
    token = secrets.token_urlsafe(40)
    db.add(SessionToken(token_hash=digest(token), role=role, user_id=account.id if account else None,
                        expires_at=datetime.now(UTC) + timedelta(hours=1)))
    db.add(AuditLog(role=role, user_id=account.id if account else None, action='login', resource='session'))
    db.commit()
    response.set_cookie('session', token, httponly=True, secure=request.app.state.settings.secure_cookies,
                        samesite='strict', max_age=3600, path='/')
    return {'role': role, 'demo': request.app.state.settings.mode == 'demo',
            'must_change_password': bool(account and account.must_change_password)}


@router.get('/configuration')
def configuration(request: Request):
    return {'demo': request.app.state.settings.mode == 'demo', 'login_method': 'password'}


@router.get('/me')
def me(request: Request, user=Depends(principal), db=Depends(session_db)):
    account = db.get(User, user.user_id) if user.user_id else None
    return {'role': user.role, 'demo': request.app.state.settings.mode == 'demo',
            'display_name': account.display_name if account else f'Demo {user.role}',
            'must_change_password': bool(account and account.must_change_password)}


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


@router.post('/change-password')
def change_password(body: PasswordChange, user=Depends(principal), db=Depends(session_db)):
    from sqlalchemy import delete, select
    from .db import LiveTicket
    account = db.get(User, user.user_id) if user.user_id else None
    if not account or not verify_password(body.current_password, account.password_hash):
        raise HTTPException(400, 'Current password is incorrect')
    if body.new_password == body.current_password:
        raise HTTPException(400, 'Choose a different password')
    try:
        account.password_hash = hash_password(body.new_password)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from None
    account.must_change_password = False
    other_sessions = select(SessionToken.token_hash).where(SessionToken.user_id == account.id,
                                                          SessionToken.token_hash != user.token_hash)
    db.execute(delete(LiveTicket).where(LiveTicket.session_hash.in_(other_sessions)))
    db.execute(delete(SessionToken).where(SessionToken.user_id == account.id, SessionToken.token_hash != user.token_hash))
    db.add(AuditLog(role=user.role,user_id=user.user_id, action='password_changed', resource=str(account.id)))
    db.commit()
    return {'ok': True}


@router.post('/logout')
def logout(response: Response, user=Depends(principal), db=Depends(session_db)):
    # Tickets are short lived and also require an extant parent session.
    from sqlalchemy import delete
    from .db import LiveTicket
    db.execute(delete(LiveTicket).where(LiveTicket.session_hash == user.token_hash))
    db.delete(user)
    db.commit()
    response.delete_cookie('session', path='/')
    return {'ok': True}
