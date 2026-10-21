"""Marketing orders, isolated by brand and owner."""
import re
from decimal import Decimal
from datetime import date, datetime, time, timedelta, timezone
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from sqlalchemy import select, func, delete
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import MarketingOrder, User
from ..security import current_user, membership, require_origin

router = APIRouter(prefix='/api/units/{unit_id}/orders', tags=['Porudžbine'])
Status = Literal['new','proposal_sent','won','lost']

class Fields(BaseModel):
    model_config = ConfigDict(extra='forbid',str_strip_whitespace=True)
    first_name: str = Field(min_length=1,max_length=100)
    last_name: str = Field(min_length=1,max_length=100)
    phone: str = Field(min_length=6,max_length=40)
    email: EmailStr | None = Field(default=None,max_length=254)
    amount: Decimal = Field(gt=0,max_digits=14,decimal_places=2)
    business_type: Literal["sale","contracted","leasing","rental"] | None = None
    source: Literal['website','phone']
    @field_validator('phone')
    @classmethod
    def telephone(cls,value):
        if not re.fullmatch(r'\+?[0-9 ()/.-]+',value) or not 6<=len(re.sub(r'\D','',value))<=15:
            raise ValueError('Proverite broj telefona.')
        return value

class Edit(Fields):
    version: int = Field(ge=1)

class Move(BaseModel):
    model_config = ConfigDict(extra='forbid')
    status: Status
    version: int = Field(ge=1)


def visible(db,user,unit):
    member=membership(db,user,unit)
    if member.role not in ('marketing','manager','admin') and not user.is_platform_admin:
        raise HTTPException(403,'Porudžbine su dostupne marketingu, menadžerima i administratorima.')
    query=select(MarketingOrder).where(MarketingOrder.business_unit_id==unit)
    if member.role=='marketing' and not user.is_platform_admin:
        query=query.where(MarketingOrder.owner_id==user.id)
    return query


def output(row):
    result = {key:getattr(row,key) for key in ('id','first_name','last_name','phone','email','amount','business_type','realized_at','source','status','version','created_at','updated_at')}
    result['amount'] = format(row.amount, '.2f') if row.amount is not None else None
    return result


def period(query, date_from, date_to):
    if date_from and date_to and (date_from>date_to or (date_to-date_from).days>366):
        raise HTTPException(422,'Izaberite period do godinu dana.')
    # User-facing report dates use the same local timezone as the CRM.
    from zoneinfo import ZoneInfo
    zone=ZoneInfo('Europe/Belgrade')
    if date_from: query=query.where(MarketingOrder.created_at>=datetime.combine(date_from,time.min,zone))
    if date_to: query=query.where(MarketingOrder.created_at<datetime.combine(date_to+timedelta(days=1),time.min,zone))
    return query

@router.get('/summary')
def summary(unit_id:int,date_from:date|None=None,date_to:date|None=None,user:User=Depends(current_user),db:Session=Depends(get_db)):
    rows=period(visible(db,user,unit_id),date_from,date_to).subquery()
    counts=dict(db.execute(select(rows.c.status,func.count()).group_by(rows.c.status)).all())
    return {'total':sum(counts.values()),'stages':{key:counts.get(key,0) for key in ('new','proposal_sent','won','lost')}}

@router.get('')
def listing(unit_id:int,search:str=Query('',max_length=200),limit:int=Query(100,ge=1,le=200),offset:int=Query(0,ge=0),status:Status|None=None,user:User=Depends(current_user),db:Session=Depends(get_db)):
    query=visible(db,user,unit_id)
    if search.strip():
        from sqlalchemy import or_
        text='%'+search.strip().replace('\\','\\\\').replace('%','\\%').replace('_','\\_')+'%'
        query=query.where(or_(*[column.ilike(text,escape='\\') for column in (MarketingOrder.first_name,MarketingOrder.last_name,MarketingOrder.phone,MarketingOrder.email)]))
    if status:query=query.where(MarketingOrder.status==status)
    total=db.scalar(select(func.count()).select_from(query.subquery()))
    rows=db.scalars(query.order_by(MarketingOrder.created_at.desc(),MarketingOrder.id.desc()).limit(limit).offset(offset)).all()
    return {'total':total,'items':[output(row) for row in rows]}

@router.post('',status_code=201,dependencies=[Depends(require_origin)])
def create(unit_id:int,data:Fields,user:User=Depends(current_user),db:Session=Depends(get_db)):
    visible(db,user,unit_id)
    values=order_values(db,unit_id,data)
    row=MarketingOrder(**values,business_unit_id=unit_id,owner_id=user.id,status='new')
    db.add(row);db.commit();db.refresh(row)
    return output(row)


def order_values(db,unit,data):
    from ..business_types import resolve_business_type
    values=data.model_dump(exclude={'version'})
    values['business_type']=resolve_business_type(db,unit,values.get('business_type'))
    if values['business_type'] is None:
        raise HTTPException(422,'Izaberite vrstu posla: prodaja, lizing ili najam.')
    return values


def record(db,user,unit,id):
    row=db.scalar(visible(db,user,unit).where(MarketingOrder.id==id).with_for_update())
    if row is None:raise HTTPException(404,'Porudžbina nije pronađena.')
    return row


def save(db,row,version,values):
    if row.version!=version:raise HTTPException(409,'Porudžbina je izmenjena. Osvežite prikaz.')
    for key,value in values.items():setattr(row,key,value)
    row.version+=1;db.commit();db.refresh(row)
    return output(row)

@router.patch('/{order_id}',dependencies=[Depends(require_origin)])
def edit(unit_id:int,order_id:int,data:Edit,user:User=Depends(current_user),db:Session=Depends(get_db)):
    return save(db,record(db,user,unit_id,order_id),data.version,order_values(db,unit_id,data))

@router.patch('/{order_id}/status',dependencies=[Depends(require_origin)])
def move(unit_id:int,order_id:int,data:Move,user:User=Depends(current_user),db:Session=Depends(get_db)):
    row=record(db,user,unit_id,order_id)
    values={'status':data.status}
    if data.status=='won':
        if row.amount is None or row.amount<=0 or not row.business_type:
            raise HTTPException(422,'Pre realizacije dopunite iznos i vrstu posla porudžbine.')
        if row.status!='won' or row.realized_at is None:
            values['realized_at']=datetime.now(timezone.utc)
    return save(db,row,data.version,values)


class DraftInput(BaseModel):
    model_config = ConfigDict(extra='forbid',str_strip_whitespace=True)
    instructions: str = Field(min_length=1,max_length=4000)

@router.post('/{order_id}/draft',dependencies=[Depends(require_origin)])
def draft(unit_id:int,order_id:int,data:DraftInput,request:Request,user:User=Depends(current_user),db:Session=Depends(get_db)):
    from ..models import BusinessUnit, AiBrandKnowledge, AiAttempt
    from ..brand_knowledge import content_for
    from ..brand_sources import website_reference
    from ..config import get_settings
    from ..ai_provider import generate
    from ..message_templates import generate as template
    row=record(db,user,unit_id,order_id)
    unit=db.get(BusinessUnit,unit_id)
    settings=get_settings()
    now=datetime.now(timezone.utc)
    db.scalar(select(User).where(User.id==user.id).with_for_update())
    count=db.scalar(select(func.count()).select_from(AiAttempt).where(AiAttempt.actor_id==user.id,AiAttempt.created_at>now-timedelta(minutes=15))) or 0
    if count>=20:raise HTTPException(429,'Najviše 20 generisanja za 15 minuta.')
    db.execute(delete(AiAttempt).where(AiAttempt.created_at<now-timedelta(days=1)))
    db.add(AiAttempt(actor_id=user.id));db.commit()
    reference=website_reference(unit.code) if settings.crm_ai_enabled else None
    context={'sender':{'name':user.name,'phone':user.phone,'organization':unit.name,'organization_code':unit.code},
             'company':{'name':f'{row.first_name} {row.last_name}','sector':'Porudžbina'},
             'contacts':[{'name':f'{row.first_name} {row.last_name}','position':None}],
             'instructions':data.instructions,'mode':'email','goal':'proposal','tone':'professional','language':'sr',
             'brand_knowledge':{'content':content_for(unit,db.get(AiBrandKnowledge,unit_id))},'website_reference':reference}
    result=generate(context) if settings.crm_ai_enabled else template(context)
    db.expire_all();verified=current_user(request,db);row=record(db,verified,unit_id,order_id)
    return {'subject':result.subject,'body':result.body,'recipient':row.email,'engine':'gemini' if settings.crm_ai_enabled else 'templates'}
