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
DATA={'first_name':'Ana','last_name':'Anić','phone':'+381 60 1234567','email':'ana@example.com','source':'website','amount':'12000.50'}
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


def test_order_amount_validation_and_targets_follow_realization(orders):
 from decimal import Decimal
 from zoneinfo import ZoneInfo
 client,engine=orders
 month=datetime.now(ZoneInfo('Europe/Belgrade')).strftime('%Y-%m')
 def progress():
  response=client.get('/api/units/1/targets',params={'month':month})
  assert response.status_code==200,response.text
  return response.json()['salespeople'][0]['targets'][0]
 for value in ['0','-1','1.001','1000000000000','NaN']:
  assert client.post(BASE,json={**DATA,'amount':value},headers=ORIGIN).status_code==422
 missing={k:v for k,v in DATA.items() if k!='amount'}
 assert client.post(BASE,json=missing,headers=ORIGIN).status_code==422
 row=client.post(BASE,json=DATA,headers=ORIGIN).json()
 assert row['amount']=='12000.50' and row['business_type']=='sale'
 assert Decimal(progress()['achieved_amount'])==0
 def move(stage):
  nonlocal row
  response=client.patch(f'{BASE}/{row["id"]}/status',json={'status':stage,'version':row['version']},headers=ORIGIN)
  assert response.status_code==200,response.text
  row=response.json()
 move('won');first_date=row['realized_at']
 assert Decimal(progress()['achieved_amount'])==Decimal('12000.50')
 move('won');assert row['realized_at']==first_date and progress()['achieved_count']==1
 response=client.patch(f'{BASE}/{row["id"]}',json={**DATA,'amount':'15000.75','version':row['version']},headers=ORIGIN)
 assert response.status_code==200,response.text
 row=response.json();assert row['realized_at']==first_date
 assert Decimal(progress()['achieved_amount'])==Decimal('15000.75')
 with Session(engine) as db:
  db.add(MarketingOrder(**DATA,business_unit_id=1,owner_id=2,status='won',business_type='sale',realized_at=datetime.now(timezone.utc)));db.commit()
 team=client.get('/api/units/1/team-bonus',params={'month':month}).json()
 assert Decimal(team['achieved_amount'])==Decimal('27001.25')
 assert Decimal(team['my_achieved_amount'])==Decimal('15000.75') and team['achieved_count']==2
 assert len(client.get('/api/units/1/targets',params={'month':month}).json()['salespeople'])==1
 move('lost');assert Decimal(progress()['achieved_amount'])==0
 move('won');assert progress()['achieved_count']==1


def test_legacy_orders_require_explicit_realization_and_cenobots_category(orders):
 client,engine=orders
 with Session(engine) as db:
  row=MarketingOrder(first_name='Stara',last_name='Porudžbina',phone='0601234567',source='phone',business_unit_id=1,owner_id=1,status='won')
  db.add(row);db.flush();order_id=row.id;version=row.version
  db.add(BusinessUnit(id=3,code='CENOBOTS',name='Cenobots'));db.flush()
  db.add(Membership(user_id=1,business_unit_id=3,role='marketing'));db.commit()
 assert client.patch(f'{BASE}/{order_id}/status',json={'status':'won','version':version},headers=ORIGIN).status_code==422
 row=client.patch(f'{BASE}/{order_id}',json={**DATA,'version':version},headers=ORIGIN).json()
 assert row['realized_at'] is None
 row=client.patch(f'{BASE}/{order_id}/status',json={'status':'won','version':row['version']},headers=ORIGIN).json()
 assert row['realized_at'] is not None
 base='/api/units/3/orders'
 assert client.post(base,json=DATA,headers=ORIGIN).status_code==422
 assert client.post(base,json={**DATA,'business_type':'contracted'},headers=ORIGIN).status_code==422
 row=client.post(base,json={**DATA,'business_type':'leasing'},headers=ORIGIN).json()
 assert row['business_type']=='leasing'
 result=client.patch(f'{base}/{row["id"]}/status',json={'status':'won','version':row['version']},headers=ORIGIN)
 assert result.status_code==200,result.text
 month=datetime.now(timezone.utc).astimezone(__import__('zoneinfo').ZoneInfo('Europe/Belgrade')).strftime('%Y-%m')
 targets=client.get('/api/units/3/targets',params={'month':month}).json()['salespeople'][0]['targets']
 assert {t['category']:t['achieved_count'] for t in targets}=={'sale':0,'leasing':1,'rental':0}


def test_order_target_month_uses_belgrade_boundaries(orders):
 from app.target_progress import achievement_totals,month_bounds
 from decimal import Decimal
 client,engine=orders
 with Session(engine) as db:
  # October starts at 22:00 UTC; after the DST change November starts at 23:00 UTC.
  for stamp,amount in [('2026-09-30T21:59:59+00:00','1'),('2026-09-30T22:00:00+00:00','2'),('2026-10-31T22:59:59+00:00','4'),('2026-10-31T23:00:00+00:00','8')]:
   db.add(MarketingOrder(**{**DATA,'amount':amount},business_unit_id=1,owner_id=1,status='won',business_type='sale',realized_at=datetime.fromisoformat(stamp)))
  db.commit()
  first,after=month_bounds('2026-10')
  assert achievement_totals(db,1,first,after,[1])=={(1,'sale'):(Decimal('6.00'),2)}
