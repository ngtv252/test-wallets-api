import uuid

from sqlalchemy import Column, Integer, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Wallet(Base):
    __tablename__ = "wallets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    balance = Column(Integer, nullable=False, default=0)
    
    __table_args__ = (
        CheckConstraint('balance >= 0', name='check_balance_non_negative'),
    )
