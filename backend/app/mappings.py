from datetime import UTC,datetime
from typing import Literal

from fastapi import APIRouter,Depends,HTTPException
from pydantic import AwareDatetime,BaseModel,Field
from sqlalchemy import or_,select

from .auth import require,session_db,utc
from .crm import normalize_phone
from .db import AuditLog,Call,DepartmentMapping,now
from .domain import timestamp

router=APIRouter(prefix='/api/v1/admin/department-mappings')


def apply_mappings(db):
    mappings=db.scalars(select(DepartmentMapping).order_by(DepartmentMapping.effective_from.desc(),DepartmentMapping.id.desc())).all()
    for call in db.scalars(select(Call).where(Call.provider=='acefone')):
        p=call.projection
        if not p.get('started_at'):continue
        at=timestamp(p['started_at'])
        source=p.get('provider_department')
        department=source
        chosen=None
        for kind,value in (('DEPARTMENT',source),('DID',call.dialed_did)):
            chosen=next((m for m in mappings if value and m.source_type==kind and m.source_value==value
                         and utc(m.effective_from)<=at and (not m.effective_to or at<utc(m.effective_to))),None)
            if chosen:department=chosen.department;break
        involved=[]
        for original in p.get('provider_departments',[]) or ([source] if source else []):
            mapping=next((m for m in mappings if m.source_type=='DEPARTMENT' and m.source_value==original and
                          utc(m.effective_from)<=at and (not m.effective_to or at<utc(m.effective_to))),None)
            name=mapping.department if mapping else department if chosen and chosen.source_type=='DID' and original==source else original
            if name not in involved:involved.append(name)
        if department and department not in involved:involved.insert(0,department)
        call.projection={**p,'primary_department':department,'departments':involved,
                         'department_mapping_id':chosen.id if chosen else None}


def public(row):
    return {'id':row.id,'source_type':row.source_type,'source_value':row.source_value,'department':row.department,
            'effective_from':row.effective_from,'effective_to':row.effective_to}


@router.get('')
def list_mappings(user=Depends(require('Admin')),db=Depends(session_db)):
    return {'items':[public(m) for m in db.scalars(select(DepartmentMapping).order_by(DepartmentMapping.effective_from.desc()))]}


class NewMapping(BaseModel):
    source_type:Literal['DID','DEPARTMENT']
    source_value:str=Field(min_length=1,max_length=120)
    department:str=Field(min_length=1,max_length=120)
    effective_from:AwareDatetime


@router.post('')
def create_mapping(body:NewMapping,user=Depends(require('Admin')),db=Depends(session_db)):
    try:value=normalize_phone(body.source_value) if body.source_type=='DID' else body.source_value.strip()
    except ValueError:raise HTTPException(422,'Invalid DID') from None
    overlap=db.scalar(select(DepartmentMapping).where(DepartmentMapping.source_type==body.source_type,
        DepartmentMapping.source_value==value,or_(DepartmentMapping.effective_to==None,DepartmentMapping.effective_to>body.effective_from)))
    if overlap:raise HTTPException(409,'An overlapping mapping exists; end it before adding a replacement')
    row=DepartmentMapping(source_type=body.source_type,source_value=value,department=body.department.strip(),effective_from=body.effective_from)
    db.add(row);db.flush();apply_mappings(db)
    db.add(AuditLog(role=user.role,user_id=user.user_id,action='department_mapping_created',resource=str(row.id)));db.commit()
    return public(row)


@router.post('/{id}/end')
def end_mapping(id:int,user=Depends(require('Admin')),db=Depends(session_db)):
    row=db.get(DepartmentMapping,id)
    if not row:raise HTTPException(404,'Mapping not found')
    if utc(row.effective_from)>now():raise HTTPException(409,'Future mappings cannot be ended before they start')
    if row.effective_to:raise HTTPException(409,'Mapping already ended')
    row.effective_to=now();apply_mappings(db)
    db.add(AuditLog(role=user.role,user_id=user.user_id,action='department_mapping_ended',resource=str(row.id)));db.commit()
    return public(row)
