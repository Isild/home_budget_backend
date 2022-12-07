from datetime import date

from ..database import SessionLocal
from ..models import expenditureModel, expendituresDayStatModel
from ..services import exposureService, expendituresDayStatService
from ..schemas import expenditureSchemas, expendituresDayStatSchemas

def recalculateDayExpenditures(db: SessionLocal, user_id: int, expenditure: expenditureModel.ExpenditureModel):
    expenditureDayStats = expendituresDayStatService.get_expenditures_day_stats(db=db, user_id=user_id, date_from=expenditure.date, date_to=expenditure.date)

    if not expenditureDayStats:
        expenditureDayStatsData = expendituresDayStatSchemas.ExpendituresDayStatBase(total_cost=0, date=expenditure.date, owner_id=user_id)

        expenditureDayStats = expendituresDayStatService.create_expenditure_day_stat(db=db, expenditureDayStat=expenditureDayStatsData, user_id=user_id)
    else:
        expenditureDayStats = expenditureDayStats[0]

    expenditures = exposureService.get_expenditures_filter_by_owner_id(db=db, user_id=user_id, date_from=expenditure.date, date_to=expenditure.date)

    totalCost = 0
    for expenditure in expenditures:
        totalCost += expenditure.cost

    expenditureNewData = expendituresDayStatSchemas.ExpendituresDayStatBase(total_cost = totalCost, date=expenditure.date, owner_id=user_id)

    expendituresDayStatService.update_expenditure_day_stat(db=db, expenditureDayStatDb=expenditureDayStats, expenditureDayStat=expenditureNewData)

    return True