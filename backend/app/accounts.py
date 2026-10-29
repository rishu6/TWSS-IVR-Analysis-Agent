from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select

from .auth import require, session_db
from .db import AuditLog, LiveTicket, SessionToken, User
from .passwords import hash_password

router=APIRouter(prefix='/api/v1/admin/users')


def public_user(user):
    return {'id':user.id,'username':user.username,'display_name':user.display_name,'role':user.role,
            'active':user.active,'must_change_password':user.must_change_password}


@router.get('')
def list_users(user=Depends(require('Admin')),db=Depends(session_db)):
    return {'items':[public_user(row) for row in db.scalars(select(User).order_by(User.username))]}


class CreateUser(BaseModel):
    username:str=Field(pattern=r'^[a-zA-Z0-9_.@-]{3,120}$')
    display_name:str=Field(min_length=1,max_length=120)
    role:Literal['Admin','Manager','Viewer']
    password:str=Field(min_length=12,max_length=256)


@router.post('')
def create_user(body:CreateUser,user=Depends(require('Admin')),db=Depends(session_db)):
    username=body.username.lower()
    if db.scalar(select(User).where(User.username==username)):
        raise HTTPException(409,'Username already exists')
    row=User(username=username,display_name=body.display_name,role=body.role,password_hash=hash_password(body.password),
             active=True,must_change_password=True,failed_attempts=0)
    db.add(row);db.flush()
    db.add(AuditLog(role=user.role,user_id=user.user_id,action='account_created',resource=str(row.id)))
    db.commit()
    return public_user(row)


class UpdateUser(BaseModel):
    role:Literal['Admin','Manager','Viewer']|None=None
    active:bool|None=None
    password:str|None=Field(default=None,min_length=12,max_length=256)


@router.patch('/{id}')
def update_user(id:int,body:UpdateUser,user=Depends(require('Admin')),db=Depends(session_db)):
    # Lock all admins in a stable order before evaluating the last-admin invariant.
    admins=db.scalars(select(User).where(User.role=='Admin',User.active==True).order_by(User.id).with_for_update()).all()
    row=db.get(User,id)
    if not row:raise HTTPException(404,'Account not found')
    if row.active and row.role=='Admin' and len(admins)<=1 and (body.active is False or (body.role and body.role!='Admin')):
        raise HTTPException(409,'Keep at least one active administrator')
    if body.role:row.role=body.role
    if body.active is not None:row.active=body.active
    if body.password:
        row.password_hash=hash_password(body.password);row.must_change_password=True
    row.failed_attempts=0;row.locked_until=None
    tokens=select(SessionToken.token_hash).where(SessionToken.user_id==row.id)
    db.execute(delete(LiveTicket).where(LiveTicket.session_hash.in_(tokens)))
    db.execute(delete(SessionToken).where(SessionToken.user_id==row.id))
    db.add(AuditLog(role=user.role,user_id=user.user_id,action='account_updated_sessions_revoked',resource=str(row.id)))
    db.commit()
    return public_user(row)
