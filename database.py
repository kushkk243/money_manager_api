from sqlmodel import Field, SQLModel, DateTime
from datetime import datetime
from typing import Optional
import uuid

class Payment_Database(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.now, nullable=False)
    name: str = Field(default=None, nullable=False, index=True)
    amount: float = Field(default=None, nullable=False)
    description: str = Field(default=None, nullable=True)
    category: str = Field(default="unknown", nullable=True, index=True)