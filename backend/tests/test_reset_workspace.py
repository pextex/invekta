"""A destructive command must preserve the chosen admin and roll back as one unit."""
from datetime import date, datetime, timedelta, timezone
import pytest
from sqlalchemy import create_engine, event, select, func
from sqlalchemy.orm import Session
from app.db import Base
from app.models import (User, BusinessUnit, Membership, Company, Contact, Opportunity, OpportunityStageChange,
    Task, AiDraft, AiAttempt, AiBrandKnowledge, SalesDocument, MonthlyTarget, TeamBonus, LoginSession, LoginAttempt)
from app.reset_workspace import plan, reset, PRESERVE
from app.security import hash_password, verify_password

@pytest.fixture
def store():
    engine=create_engine('sqlite://')
    @event.listens_for(engine,'connect')
    def foreign_keys(connection,_): connection.execute('PRAGMA foreign_keys=ON')
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        digest=hash_password('keep-admin-password-123')
        db.add_all([User(id=1,username='owner',email='owner@example.com',name='Owner',phone='+381601234567',password_hash=digest,is_platform_admin=True),
                    User(id=2,username='sales',email='sales@example.com',name='Sales',password_hash=digest)])
        db.add_all([BusinessUnit(id=i,code=code,name=code) for i,code in enumerate(['LUU','INVEKTA','CENOBOTS'],1)])
        db.flush()
        db.add_all([Membership(user_id=1,business_unit_id=i,role='admin') for i in (1,2,3)])
        db.add(Membership(user_id=2,business_unit_id=1,role='sales'));db.flush()
        db.add(Company(id=1,business_unit_id=1,owner_id=2,name='Delete me',city='Beograd',sector='Hotel'));db.flush()
        db.add(Contact(id=1,company_id=1,business_unit_id=1,name='Contact'))
        db.add(Opportunity(id=1,company_id=1,business_unit_id=1,title='Deal',amount=100,stage='Ponuda'));db.flush()
        db.add(OpportunityStageChange(id=1,opportunity_id=1,business_unit_id=1,actor_id=2,to_stage='Ponuda'))
        db.add(Task(business_unit_id=1,owner_id=2,company_id=1,title='Task',due_date=date.today()))
        db.add(AiDraft(business_unit_id=1,company_id=1,actor_id=2,mode='email',subject='Subject',body='Private draft',model='test'))
        db.add(AiAttempt(actor_id=2))
        db.add(AiBrandKnowledge(business_unit_id=1,content='Keep brand configuration',updated_by_id=2))
        db.add(SalesDocument(business_unit_id=1,uploaded_by_id=2,title='File',filename='file.pdf',content_type='application/pdf',size_bytes=4,data=b'test'))
        db.add(MonthlyTarget(business_unit_id=1,user_id=2,period=date(2026,10,1),category='sale',target_amount=100))
        db.add(TeamBonus(business_unit_id=1,period=date(2026,10,1),target_amount=100))
        db.add(LoginSession(token_hash='abc',user_id=1,expires_at=datetime.now(timezone.utc)+timedelta(hours=1)))
        db.add(LoginAttempt(username='sales'))
        db.commit()
    yield engine
    engine.dispose()


def test_plan_is_read_only_and_apply_cleans_records_but_keeps_admin_configuration(store):
    with Session(store) as db:
        result=plan(db,'owner@example.com')
        assert result['other_users']==1 and result['delete']['sales_documents']==1
        assert db.get(User,2) is not None and db.get(SalesDocument,1).data==b'test'
        db.rollback()
    with Session(store) as db, db.begin(): reset(db,'OWNER@example.com')
    with Session(store) as db:
        admin=db.get(User,1)
        assert admin.active and admin.is_platform_admin and admin.phone=='+381601234567'
        assert verify_password('keep-admin-password-123',admin.password_hash)
        assert db.get(User,2) is None
        assert db.scalar(select(func.count()).select_from(Membership))==3
        assert db.scalar(select(func.count()).select_from(BusinessUnit))==3
        knowledge=db.get(AiBrandKnowledge,1)
        assert knowledge.content=='Keep brand configuration' and knowledge.updated_by_id==1
        for table in Base.metadata.sorted_tables:
            if table.name not in PRESERVE: assert db.scalar(select(func.count()).select_from(table))==0


def test_entire_cleanup_rolls_back_on_failure(store):
    with pytest.raises(RuntimeError),Session(store) as db,db.begin():
        reset(db,'owner@example.com')
        raise RuntimeError('Simulated failure before commit')
    with Session(store) as db:
        assert db.get(User,2) is not None and db.get(Company,1) is not None
        assert db.get(SalesDocument,1).data==b'test'
        assert db.get(AiBrandKnowledge,1).updated_by_id==2


@pytest.mark.parametrize('email,change',[('missing@example.com',None),('sales@example.com',None),('owner@example.com','inactive'),('owner@example.com','membership'),('owner@example.com','pending')])
def test_refuses_missing_or_unusable_admin_without_deleting_data(store,email,change):
    with Session(store) as db:
        if change=='inactive': db.get(User,1).active=False
        if change=='pending': db.get(User,1).bootstrap_pending=True
        if change=='membership': db.get(Membership,(1,1)).enabled=False
        db.commit()
        with pytest.raises(ValueError): reset(db,email)
        assert db.get(User,2) is not None and db.get(SalesDocument,1).data==b'test'


@pytest.mark.parametrize('host,name',[('wrong-host','hosting_check_test'),('test-db','wrong-database')])
def test_apply_rejects_wrong_target_before_opening_database(monkeypatch,host,name):
    from types import SimpleNamespace
    from app import reset_workspace as command
    monkeypatch.setattr(command,'get_settings',lambda:SimpleNamespace(database_url='postgresql://test-user:test-password@test-db/hosting_check_test'))
    monkeypatch.setattr('sys.argv',['reset','--admin-email','owner@example.com','--database-host',host,'--database-name',name,'--apply'])
    def connect():raise AssertionError('Must not connect before matching the target')
    monkeypatch.setattr(command,'SessionLocal',connect)
    with pytest.raises(SystemExit,match='Brisanje nije pokrenuto'):command.main()
