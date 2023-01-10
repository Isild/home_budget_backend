from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import date, datetime
from sqlalchemy import func

from ..models import expendituresDayStatModel
from ..schemas import expendituresDayStatSchemas
from . import limitService

model = expendituresDayStatModel.ExpendituresDayStat

def get_expenditures_day_stats(db: Session, user_id: int = None, page: int = 0, limit: int = 100, search: str = None, date_from: date = None, date_to: date = None, group_by: str = None):
    if group_by:
        query = db.query(expendituresDayStatModel.ExpendituresDayStat.date, func.sum(expendituresDayStatModel.ExpendituresDayStat.total_cost).label('total_cost')).filter(expendituresDayStatModel.ExpendituresDayStat.owner_id== user_id)
    else:
        query = db.query(expendituresDayStatModel.ExpendituresDayStat).filter(expendituresDayStatModel.ExpendituresDayStat.owner_id== user_id)

    query = query.order_by(expendituresDayStatModel.ExpendituresDayStat.date)

    if user_id:
        query = query.filter(expendituresDayStatModel.ExpendituresDayStat.owner_id == user_id)

    # if search:
    #     query = query.filter(expendituresDayStatModel.ExpendituresDayStat.total_cost.match(search))

    if date_from:
        query = query.filter(expendituresDayStatModel.ExpendituresDayStat.date >= date_from)

    if date_to:
        query = query.filter(expendituresDayStatModel.ExpendituresDayStat.date <= date_to)

    if group_by:
        if group_by == "day":
            query = query.group_by(expendituresDayStatModel.ExpendituresDayStat.date)
        elif group_by == "month" or group_by == "year":
            query = query.group_by(expendituresDayStatModel.ExpendituresDayStat.date)
            result = query.order_by(expendituresDayStatModel.ExpendituresDayStat.date).all()

            grouped_expenditures = {}
            for day in result:
                year = grouped_expenditures.get(day.date.year)

                if not year:
                    year = grouped_expenditures[day.date.year] = {}

                el = year.get(day.date.month)
                if not el:
                    year[day.date.month] = day.total_cost
                else:
                    year[day.date.month] += day.total_cost


            return grouped_expenditures

    return query.offset((page-1) * limit).limit(limit).all()

def get_expenditure_day_stat(db: Session, uuid: str):
    return db.query(expendituresDayStatModel.ExpendituresDayStat).filter(expendituresDayStatModel.ExpendituresDayStat.uuid == uuid).first()

def update_expenditure_day_stat(db: Session, expenditureDayStatDb: expendituresDayStatModel.ExpendituresDayStat, expenditureDayStat: expendituresDayStatSchemas.ExpendituresDayStat) -> bool:
    db.query(expendituresDayStatModel.ExpendituresDayStat).filter(expendituresDayStatModel.ExpendituresDayStat.id == expenditureDayStatDb.id).update(expenditureDayStat.dict())
    db.commit()
    db.refresh(expenditureDayStatDb)

    return expenditureDayStatDb

def create_expenditure_day_stat(db: Session, expenditureDayStat: expendituresDayStatSchemas.ExpendituresDayStat, user_id: int):
    uuid = str(uuid4())

    db_expenditure = expendituresDayStatModel.ExpendituresDayStat(**expenditureDayStat.dict(), owner_id=user_id, uuid=uuid)

    db.add(db_expenditure)
    db.commit()
    db.refresh(db_expenditure)

    return db_expenditure

def remove_expenditure_day_stat(db: Session, uuid: str) -> bool:
    expenditure = db.query(expendituresDayStatModel.ExpendituresDayStat).filter(expendituresDayStatModel.ExpendituresDayStat.uuid == uuid).first()

    if expenditure == None:
        return None

    db.delete(expenditure)
    db.commit()

    return uuid

def get_expenditure_day_stats_amount(db: Session, user_id: int = None) -> int:
    return db.query(expendituresDayStatModel.ExpendituresDayStat.date, func.sum(expendituresDayStatModel.ExpendituresDayStat.total_cost)\
        .label('total_cost')).filter(expendituresDayStatModel.ExpendituresDayStat.owner_id== user_id).with_entities(func.count()).scalar()

def get_month_limit_data(db: Session, year: int = None, user_id: int = None):
    if year is None:
        year = datetime.now().year

    date_from = str(year).zfill(4) + "-" + str(1).zfill(2) + "-01"
    date_to = str(year).zfill(4) + "-" + str(12).zfill(2) + "-31"
    expendiures_day_stats = get_expenditures_day_stats(db=db, user_id=user_id, page=1, limit=100, date_from=date_from, date_to=date_to, group_by="month")

    month_list_limit = []
    total_cost = 0
    total_limit = 0
    if year in expendiures_day_stats:
        limitsDb = limitService.get_limits(db=db, year=year, user_id=user_id)

        for month in expendiures_day_stats[year]:
            total_cost += expendiures_day_stats[year][month]
            limit = 0

            for limitDb in limitsDb:
                if month == limitDb.month:
                    limit = limitDb.limit

            month_list_limit.append({
                month: round(expendiures_day_stats[year][month], 2),
                "limit": limit
            })

        for limitDb in limitsDb:
            total_limit += limitDb.limit

    return {
        "year": year,
        "total_cost": round(total_cost, 2),
        "total_limit": round(total_limit, 2),
        "month_costs": month_list_limit
    }
