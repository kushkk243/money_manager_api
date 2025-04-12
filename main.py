from fastapi import FastAPI, Depends, HTTPException, Query
from database import Payment_Database
from sqlmodel import create_engine, select, Session, SQLModel
from typing import Annotated
from datetime import datetime, timedelta
import uuid
# Database connection
database_file_name = "payment_db.db"
sqlite_url = f"sqlite:///{database_file_name}"
connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, echo=True, connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
# Starting FastAPI
def on_startup():
    create_db_and_tables()

app = FastAPI( on_startup=on_startup())
monthly_budget = 10000
# Create the database and tables


# Create a test payment entry
@app.get("/")
async def root():
    return({"message": "Hello World"})

@app.get("/settings/budget")
async def get_budget():
    return {"monthly_budget": monthly_budget}

@app.post("/settings/budget")
async def set_budget(budget: int):
    global monthly_budget
    monthly_budget = budget
    return {"message": "Budget updated", "monthly_budget": monthly_budget}

@app.get("/payments/list/{time_period}")
async def get_payments(time_period: str, session: SessionDep ):
    if time_period == "all":
        payments = session.exec(select(Payment_Database)).all()
    elif time_period == "month":
        start_date = datetime(datetime.now().year, datetime.now().month, 1)
        end_date = datetime(datetime.now().year, datetime.now().month + 1, 1) if datetime.now().month < 12 else datetime(datetime.now().year + 1, 1, 1)
        payments = session.exec(select(Payment_Database).where(Payment_Database.timestamp >= start_date, Payment_Database.timestamp<end_date )).all()
    elif time_period == "week":
        payments = session.exec(select(Payment_Database).where(Payment_Database.timestamp > datetime.now() - timedelta(days=7))).all()
    elif time_period == "day":
        payments = session.exec(select(Payment_Database).where(Payment_Database.timestamp > datetime.now() - timedelta(days=1))).all()
    else:
        raise HTTPException(status_code=400, detail="Invalid time period")
    return payments

@app.post("/payments/add")
async def add_payment(session: SessionDep, name: str, amount: float, desc: str = "", category: str = "unknown", time: datetime = datetime.now()):
    payment = Payment_Database(timestamp=time, amount=amount, category=category, name=name, description=desc)
    session.add(payment)
    session.commit()
    session.refresh(payment)
    return payment

@app.delete("/payments/delete/{payment_id}")
async def delete_payment(payment_id: uuid.UUID, session: SessionDep):
    payment = session.get(Payment_Database, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    session.delete(payment)
    session.commit()
    return {"message": "Payment deleted"}


@app.get("/payments/total/{time_period}")
async def get_totals(time_period : str, session: SessionDep):
    if time_period == "all":
        total = session.exec(select(Payment_Database)).all()
    elif time_period == "month":
        start_date = datetime(datetime.now().year, datetime.now().month, 1)
        end_date = datetime(datetime.now().year, datetime.now().month + 1, 1) if datetime.now().month < 12 else datetime(datetime.now().year + 1, 1, 1)
        total = session.exec(select(Payment_Database).where(Payment_Database.timestamp >= start_date, Payment_Database.timestamp<end_date )).all()
    elif time_period == "week":
        total = session.exec(select(Payment_Database).where(Payment_Database.timestamp > datetime.now() - timedelta(days=7))).all()
    elif time_period == "day":
        total = session.exec(select(Payment_Database).where(Payment_Database.timestamp > datetime.now() - timedelta(days=1))).all()
    else:
        raise HTTPException(status_code=400, detail="Invalid time period")
    return {"number_of_payments": len(total), "total_amount": sum([payment.amount for payment in total])}

@app.get("/payments/total/category/{category}")
async def get_totals_by_category(category: str, session: SessionDep):
    total = session.exec(select(Payment_Database).where(Payment_Database.category == category)).all()
    return {"number_of_payments": len(total), "total_amount": sum([payment.amount for payment in total])}

@app.get("/payments/total/category/{category}/{time_period}")
async def get_totals_by_category_and_time_period(category: str, time_period: str, session: SessionDep):
    if time_period == "all":
        total = session.exec(select(Payment_Database).where(Payment_Database.category == category)).all()
    elif time_period == "month":
        start_date = datetime(datetime.now().year, datetime.now().month, 1)
        end_date = datetime(datetime.now().year, datetime.now().month + 1, 1) if datetime.now().month < 12 else datetime(datetime.now().year + 1, 1, 1)
        total = session.exec(select(Payment_Database).where(Payment_Database.category == category, Payment_Database.timestamp >= start_date, Payment_Database.timestamp<end_date )).all()
    elif time_period == "week":
        total = session.exec(select(Payment_Database).where(Payment_Database.category == category, Payment_Database.timestamp > datetime.now() - timedelta(days=7))).all()
    elif time_period == "day":
        total = session.exec(select(Payment_Database).where(Payment_Database.category == category, Payment_Database.timestamp > datetime.now() - timedelta(days=1))).all()
    else:
        raise HTTPException(status_code=400, detail="Invalid time period")
    return {"number_of_payments": len(total), "total_amount": sum([payment.amount for payment in total])}

@app.get("/payments/{year}/{month}")
async def get_payments_by_month(year: int, month: int, session: SessionDep):
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    payments = session.exec(select(Payment_Database).where(Payment_Database.timestamp >= start_date, Payment_Database.timestamp < end_date)).all()
    return payments

@app.get("/payments/pie_data")
async def get_pie_data(session: SessionDep, month: int = datetime.now().month, year: int = datetime.now().year):
    start_date = datetime(year, month, 1)
    end_date = datetime(year, month + 1, 1) if month < 12 else datetime(year + 1, 1, 1)
    payments = session.exec(select(Payment_Database).where(Payment_Database.timestamp >= month, Payment_Database.timestamp<end_date)).all()
    categories = {}
    for payment in payments:
        if payment.category not in categories:
            categories[payment.category] = 0
        categories[payment.category] += payment.amount
    return categories
