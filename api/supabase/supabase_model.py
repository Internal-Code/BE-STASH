from api.supabase.supabase_conection import database_connection
from sqlalchemy import (
    MetaData, 
    Table, 
    Column, 
    Integer,
    String,
    DateTime,
    Float
)

engine = database_connection()
meta = MetaData()

spending_money = Table(
    'spending_money', 
    meta, 
    Column('id', Integer, primary_key = True, autoincrement=True), 
    Column('createdAt', DateTime), 
    Column('category', String(255)),
    Column('describe', String(255)),
    Column('amount', String(255)),
)

Table(
    'spending_money_category', 
    meta, 
    Column('id', Integer, primary_key = True, autoincrement=True), 
    Column('createdAt', DateTime), 
    Column('class', String(255))
)

Table(
    'spending_money_total_per_month', 
    meta, 
    Column('id', Integer, primary_key = True, autoincrement=True), 
    Column('createdAt', DateTime), 
    Column('month', String(255)),
    Column('totalAmount', Float)
)

meta.create_all(engine)