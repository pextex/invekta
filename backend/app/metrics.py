"""Authorized, shared current-state metrics; never reconstruct missing history."""
from datetime import date, datetime, time
from decimal import Decimal
from zoneinfo import ZoneInfo
from fastapi import HTTPException, Query
from sqlalchemy import func, select, or_
from .access import visible_query
from .constants import OPPORTUNITY_STAGES, CLOSED_STAGES
from .models import Company, Contact, Opportunity, OpportunityStageChange, User


class MetricFilters:
    def __init__(self, start_date: date | None = Query(None),
                 end_date: date | None = Query(None), owner_id: int | None = Query(None, gt=0)):
        if start_date and end_date and start_date > end_date:
            raise HTTPException(422, 'Početni datum mora biti pre završnog datuma.')
        self.start_date, self.end_date, self.owner_id = start_date, end_date, owner_id

    def period(self, query, column):
        zone = ZoneInfo('Europe/Belgrade')
        if self.start_date:
            query = query.where(column >= datetime.combine(self.start_date, time.min, zone))
        if self.end_date:
            query = query.where(column <= datetime.combine(self.end_date, time.max, zone))
        return query


def scoped_companies(db, user, unit_id, filters):
    query = visible_query(db, user, unit_id)
    if filters.owner_id is not None:
        query = query.where(Company.owner_id == filters.owner_id)
        if db.scalar(query.with_only_columns(Company.id).limit(1)) is None:
            raise HTTPException(404, 'Komercijalista nije pronađen u dostupnim kompanijama.')
    return query


def scoped_opportunities(db, user, unit_id, filters):
    ids = scoped_companies(db, user, unit_id, filters).with_only_columns(Company.id)
    return filters.period(select(Opportunity).where(
        Opportunity.business_unit_id == unit_id, Opportunity.company_id.in_(ids)), Opportunity.created_at)


def totals(counts, values):
    return {
        'opportunity_count': sum(counts.values()),
        'open_count': sum(counts[s] for s in OPPORTUNITY_STAGES if s not in CLOSED_STAGES),
        'open_value': sum((values[s] for s in OPPORTUNITY_STAGES if s not in CLOSED_STAGES), Decimal('0')),
        'won_count': counts['Dobijeno'], 'won_value': values['Dobijeno'],
        'lost_count': counts['Izgubljeno'], 'lost_value': values['Izgubljeno'],
        'stages': counts, 'stage_values': values,
    }


def buckets(rows):
    counts = dict.fromkeys(OPPORTUNITY_STAGES, 0)
    values = dict.fromkeys(OPPORTUNITY_STAGES, Decimal('0'))
    for stage, count, value in rows:
        counts[stage], values[stage] = count, value or Decimal('0')
    return totals(counts, values)


def unit_metrics(db, user, unit_id, filters):
    company_ids = scoped_companies(db, user, unit_id, filters).with_only_columns(Company.id)
    opp_ids = scoped_opportunities(db, user, unit_id, filters).with_only_columns(Opportunity.id)
    scope = Opportunity.id.in_(opp_ids)
    rows = db.execute(select(Opportunity.stage, func.count(), func.sum(Opportunity.amount))
                      .where(scope).group_by(Opportunity.stage)).all()
    result = buckets(rows)
    result['company_count'] = db.scalar(select(func.count()).select_from(Company).where(Company.id.in_(company_ids)))
    result['contact_count'] = db.scalar(select(func.count()).select_from(Contact).where(
        Contact.business_unit_id == unit_id, Contact.company_id.in_(company_ids)))
    visible_ids = visible_query(db, user, unit_id).with_only_columns(Company.id)
    result['owners'] = [dict(id=i, name=n) for i, n in db.execute(
        select(User.id, User.name).join(Company, Company.owner_id == User.id)
        .where(Company.id.in_(visible_ids)).distinct().order_by(User.name, User.id))]
    for label, column, names in (
        ('sales_results', Company.owner_id, User.name),
        ('company_results', Company.id, Company.name),
    ):
        grouped = db.execute(select(column, names, Opportunity.stage, func.count(), func.sum(Opportunity.amount))
                             .select_from(Opportunity).join(Company, Company.id == Opportunity.company_id)
                             .join(User, User.id == Company.owner_id).where(scope)
                             .group_by(column, names, Opportunity.stage).order_by(names, column)).all()
        groups = {}
        for identifier, name, stage, count, value in grouped:
            entry = groups.setdefault(identifier, {'name': name, 'rows': []})
            entry['rows'].append((stage, count, value))
        key = 'owner_id' if label == 'sales_results' else 'company_id'
        result[label] = [{key: identifier, 'name': v['name'], **buckets(v['rows'])} for identifier, v in groups.items()]
    history_scope = filters.period(select(OpportunityStageChange).where(
        OpportunityStageChange.business_unit_id == unit_id,
        OpportunityStageChange.opportunity_id.in_(opp_ids)), OpportunityStageChange.changed_at)
    history_ids = history_scope.with_only_columns(OpportunityStageChange.id)
    event_scope = OpportunityStageChange.id.in_(history_ids)
    transitions = db.execute(select(OpportunityStageChange.from_stage, OpportunityStageChange.to_stage,
                                   func.count(func.distinct(OpportunityStageChange.opportunity_id)))
                             .where(event_scope, OpportunityStageChange.from_stage.is_not(None))
                             .group_by(OpportunityStageChange.from_stage, OpportunityStageChange.to_stage)
                             .order_by(OpportunityStageChange.from_stage, OpportunityStageChange.to_stage)).all()
    source_counts = {}
    for source, _, _ in transitions:
        if source not in source_counts:
            source_counts[source] = db.scalar(select(func.count(func.distinct(OpportunityStageChange.opportunity_id)))
                .where(event_scope, or_(OpportunityStageChange.from_stage == source, OpportunityStageChange.to_stage == source)))
    result['transitions'] = [dict(from_stage=s, to_stage=t, count=n, source_count=source_counts[s],
                                 rate=round(n / source_counts[s] * 100, 2)) for s, t, n in transitions]
    month = func.to_char(func.timezone('Europe/Belgrade', OpportunityStageChange.changed_at), 'YYYY-MM')
    result['timeline'] = [dict(month=m, stage=s, count=n) for m, s, n in db.execute(
        select(month, OpportunityStageChange.to_stage, func.count()).where(event_scope)
        .group_by(month, OpportunityStageChange.to_stage).order_by(month, OpportunityStageChange.to_stage))]
    return result
