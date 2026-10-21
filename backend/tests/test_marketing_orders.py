from datetime import datetime,timedelta,timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine,event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
import pytest
from app.main import app
from app.db import Base,get_db
from app.models import User,BusinessUnit,Membership,LoginSession,MarketingOrder,Company
from app.security import token_hash,COOKIE_NAME,hash_password

ORIGIN={'Origin':'http://localhost:5173'}
BASE='/api/units/1/orders'
DATA={'first_name':'Ana','last_name':'Anić','phone':'+381 60 1234567','email':'ana@example.com','source':'website'}
@pytest.fixture
def orders():
 engine=create_engine('sqlite://',connect_args={'check_same_thread':False},poolclass=StaticPool)
 @event.listens_for(engine,'connect')
 def fk(connection,_):connection.execute('PRAGMA foreign_keys=ON')
 Base.metadata.create_all(engine)
 with Session(engine) as db:
  digest=hash_password('test-marketing-password')
  db.add_all([BusinessUnit(id=1,code='LUU',name='LUU'),BusinessUnit(id=2,code='INVEKTA',name='INVEKTA')])
  db.add_all([User(id=i,username=str(i),name=f'User {i}',email=f'user{i}@example.com',password_hash=digest,is_platform_admin=i==5) for i in range(1,6)]);db.flush()
  for i,role in [(1,'marketing'),(2,'marketing'),(3,'sales'),(4,'manager'),(5,'admin')]:
   db.add(Membership(user_id=i,business_unit_id=1,role=role))
   db.add(LoginSession(token_hash=token_hash(str(i)),user_id=i,expires_at=datetime.now(timezone.utc)+timedelta(hours=1)))
  db.flush();db.add(Company(id=1,business_unit_id=1,owner_id=3,name='Private sales client',city='Beograd',sector='Test'))
  db.commit()
 def session():
  with Session(engine) as db:yield db
 app.dependency_overrides[get_db]=session
 try:
  with TestClient(app) as client:
   client.cookies.set(COOKIE_NAME,'1',path='/api');yield client,engine
 finally:app.dependency_overrides.clear();engine.dispose()

def test_order_fields_email_status_conflicts_and_owner_brand_boundaries(orders):
 client,engine=orders
 assert client.post(BASE,json=DATA).status_code==403
 result=client.post(BASE,json=DATA,headers=ORIGIN);assert result.status_code==201,result.text
 row=result.json();id=row['id'];assert row['email']=='ana@example.com' and row['status']=='new'
 for stage in ['proposal_sent','won','lost','new']:
  response=client.patch(f'{BASE}/{id}/status',json={'status':stage,'version':row['version']},headers=ORIGIN)
  assert response.status_code==200;row=response.json();assert row['status']==stage
 assert client.patch(f'{BASE}/{id}/status',json={'status':'won','version':1},headers=ORIGIN).status_code==409
 assert client.patch(f'{BASE}/{id}/status',json={'status':'Sastanak','version':row['version']},headers=ORIGIN).status_code==422
 assert client.patch(f'{BASE}/{id}',json={**DATA,'email':None,'version':row['version']},headers=ORIGIN).json()['email'] is None
 for invalid in [{'email':'bad'},{'source':'facebook'},{'phone':'abc123'},{'first_name':'   '},{'owner_id':2}]:
  assert client.post(BASE,json={**DATA,**invalid},headers=ORIGIN).status_code==422
 assert client.get(BASE,params={'search':'Ana'}).json()['total']==1
 assert client.get(BASE,params={'search':'%'}).json()['total']==0
 assert client.get('/api/units/2/orders').status_code==403
 client.cookies.set(COOKIE_NAME,'2',path='/api')
 assert client.get(BASE).json()['total']==0
 assert client.patch(f'{BASE}/{id}/status',json={'status':'won','version':row['version']},headers=ORIGIN).status_code==404
 assert client.post(f'{BASE}/{id}/draft',json={'instructions':'Mejl'},headers=ORIGIN).status_code==404
 client.cookies.set(COOKIE_NAME,'3',path='/api');assert client.get(BASE).status_code==403
 for token in ['4','5']:
  client.cookies.set(COOKIE_NAME,token,path='/api');assert client.get(BASE).json()['total']==1
 client.cookies.clear();assert client.get(BASE).status_code==401

def test_marketing_never_inherits_management_access_and_summary_is_own_orders(orders):
 client,engine=orders
 assert client.get('/api/units/1/companies').json()==[]
 assert client.get('/api/units/1/companies/1').status_code==404
 assert client.post('/api/units/1/companies',json={'name':'Forbidden','city':'Test','sector':'Test','contacts':[]},headers=ORIGIN).status_code==403
 assert client.get('/api/units/1/ai/knowledge').status_code==403
 assert client.get('/api/admin/users').status_code==403
 assert client.get('/api/units/1/ai/status').json()['can_view_knowledge'] is False
 with Session(engine) as db:
  db.add_all([MarketingOrder(**DATA,business_unit_id=1,owner_id=1,status='won'),MarketingOrder(**DATA,business_unit_id=1,owner_id=2,status='new')]);db.commit()
 summary=client.get(BASE+'/summary').json();assert summary['total']==1 and summary['stages']['won']==1 and summary['stages']['new']==0
 assert client.get(BASE+'/summary?date_from=2026-10-20&date_to=2026-10-19').status_code==422
 with Session(engine) as db:db.get(Membership,(1,1)).enabled=False;db.commit()
 assert client.get(BASE).status_code==403


def test_marketing_role_can_be_granted_and_draft_uses_only_selected_order(orders,monkeypatch):
 from app import ai_provider
 client,engine=orders
 client.cookies.set(COOKIE_NAME,'5',path='/api')
 user=client.post('/api/admin/users',headers=ORIGIN,json={'name':'New Marketing','email':'new-marketing@example.com','password':'test-marketing-password','units':[{'code':'LUU','role':'marketing'}]})
 assert user.status_code in (200,201),user.text
 client.cookies.set(COOKIE_NAME,'1',path='/api')
 row=client.post(BASE,json=DATA,headers=ORIGIN).json()
 # Templates are deterministic and must not use an external provider during this test.
 from app import config
 settings=config.get_settings().model_copy(update={'crm_ai_enabled':False})
 monkeypatch.setattr(config,'get_settings',lambda:settings)
 result=client.post(BASE+f'/{row["id"]}/draft',headers=ORIGIN,json={'instructions':'Predlog ponude'})
 assert result.status_code==200,result.text
 assert result.json()['recipient']=='ana@example.com' and result.json()['engine']=='templates'
 assert 'User 1' in result.json()['body'] and 'Private sales client' not in result.json()['body']
