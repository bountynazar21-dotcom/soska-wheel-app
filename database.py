from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
import datetime

engine = create_engine("sqlite:///wheel.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Spin(Base):
    __tablename__ = "spins"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    user_id = Column(String, index=True)
    check_number = Column(String, index=True)
    prize = Column(String)
    datetime = Column(DateTime, default=datetime.datetime.utcnow)
