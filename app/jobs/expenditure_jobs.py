from datetime import date

from ..database import SessionLocal
from ..models import expenditure_model, expenditures_day_stat_model
from ..services import expenditures_day_stat_service, exposure_service
from ..schemas import expenditure_schemas, expenditures_day_stat_schemas

def recalculateDayExpenditures(db: SessionLocal, user_id: int, expenditure: expenditure_model.ExpenditureModel):
    expenditureDayStats = expenditures_day_stat_service.get_expenditures_day_stats(db=db, user_id=user_id, date_from=expenditure.date, date_to=expenditure.date)

    if not expenditureDayStats:
        expenditureDayStatsData = expenditures_day_stat_schemas.ExpendituresDayStatBase(total_cost=0, date=expenditure.date, owner_id=user_id)

        expenditureDayStats = expenditures_day_stat_service.create_expenditure_day_stat(db=db, expenditureDayStat=expenditureDayStatsData, user_id=user_id)
    else:
        expenditureDayStats = expenditureDayStats[0]

    expenditures = exposure_service.get_expenditures_filter_by_owner_id(db=db, user_id=user_id, date_from=expenditure.date, date_to=expenditure.date)

    totalCost = 0
    for expenditure in expenditures:
        totalCost += expenditure.cost

    expenditureNewData = expenditures_day_stat_schemas.ExpendituresDayStatBase(total_cost = totalCost, date=expenditure.date, owner_id=user_id)

    expenditures_day_stat_service.update_expenditure_day_stat(db=db, expenditureDayStatDb=expenditureDayStats, expenditureDayStat=expenditureNewData)

    return True