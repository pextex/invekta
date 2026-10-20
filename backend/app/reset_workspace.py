"""Explicit, transactional cleanup; never called by migrations or application startup."""
import argparse
import json
from sqlalchemy import delete, func, select, update
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from .db import Base, SessionLocal
from .config import get_settings
from .models import AiBrandKnowledge, BusinessUnit, Membership, User

PRESERVE = {'users', 'memberships', 'business_units', 'ai_brand_knowledge'}


def administrator(db: Session, email: str):
    user = db.scalar(select(User).where(func.lower(User.email) == email.strip().lower()).with_for_update())
    if user is None or not user.active or not user.is_platform_admin or user.bootstrap_pending:
        raise ValueError('Izabrani nalog mora biti postojeći, aktivan i aktiviran administrator platforme.')
    grants = list(db.execute(select(BusinessUnit.code, Membership.role, Membership.enabled)
        .join(Membership, Membership.business_unit_id == BusinessUnit.id).where(Membership.user_id == user.id)))
    codes = {code for code, role, enabled in grants if role == 'admin' and enabled}
    if not {'LUU', 'INVEKTA', 'CENOBOTS'}.issubset(codes):
        raise ValueError('Administrator mora imati aktivan administratorski pristup svim trima brendovima.')
    return user


def plan(db: Session, email: str) -> dict:
    admin = administrator(db, email)
    counts = {table.name: db.scalar(select(func.count()).select_from(table)) or 0
              for table in Base.metadata.sorted_tables}
    return {'administrator': {'id': admin.id, 'email': admin.email},
            'delete': {name: count for name, count in counts.items() if name not in PRESERVE},
            'other_users': counts['users'] - 1,
            'preserve': ['izabrani administrator i njegova lozinka i telefon', 'pristup administratora brendovima',
                         'konfiguracija brendova', 'odobreno znanje brendova'],
            'uploaded_files': 'Otpremljeni fajlovi su u sales_documents.data i brišu se sa zapisima.',
            'all_sessions_revoked': True}


def reset(db: Session, email: str) -> dict:
    """Caller supplies an explicit transaction and must stop CRM writers first."""
    result = plan(db, email)
    admin_id = result['administrator']['id']
    # Knowledge is configuration. Remove ownership references to deleted accounts.
    db.execute(update(AiBrandKnowledge).values(updated_by_id=admin_id))
    for table in reversed(Base.metadata.sorted_tables):
        if table.name not in PRESERVE:
            db.execute(delete(table))
    db.execute(delete(Membership).where(Membership.user_id != admin_id))
    db.execute(delete(User).where(User.id != admin_id))
    db.flush()
    if db.scalar(select(func.count()).select_from(User)) != 1:
        raise RuntimeError('Provera resetovanja nije uspela; transakcija se poništava.')
    for table in Base.metadata.sorted_tables:
        if table.name not in PRESERVE and db.scalar(select(func.count()).select_from(table)):
            raise RuntimeError('Poslovni podaci nisu prazni; transakcija se poništava.')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--admin-email', required=True)
    parser.add_argument('--apply', action='store_true', help='Bez ove opcije izvršava se samo pregled.')
    parser.add_argument('--database-host', help='Za brisanje mora odgovarati konfigurisanom hostu baze.')
    parser.add_argument('--database-name', help='Za brisanje mora odgovarati konfigurisanom imenu baze.')
    args = parser.parse_args()
    target = make_url(get_settings().database_url)
    if args.apply and (not args.database_host or not args.database_name or
                       args.database_host != target.host or args.database_name != target.database):
        raise SystemExit('Brisanje nije pokrenuto: navedite tačan host i ime ciljne baze. Lozinka se nikada ne ispisuje.')
    try:
        with SessionLocal.begin() as db:
            report = reset(db, args.admin_email) if args.apply else plan(db, args.admin_email)
            report.update({'applied': args.apply, 'database': {'host': target.host, 'name': target.database}})
        print(json.dumps(report, ensure_ascii=False, indent=2))
    except ValueError as error:
        raise SystemExit(str(error)) from None


if __name__ == '__main__':
    main()
