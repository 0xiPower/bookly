import uuid
from datetime import datetime
from sqlmodel import SQLModel, Field, Column
import sqlalchemy.dialects.postgresql as pg

"""
class User:
    uid: uuid.UUID
    username: str
    email: str
    first_name: str
    last_name: str
    is_verufied: bool = False
    created_at: datetime
    updated_at: datetime
"""


class User(SQLModel, table=True):
    __tablename__ = "users"

    uid: uuid.UUID = Field(
        sa_column=Column(pg.UUID, nullable=False, primary_key=True, default=uuid.uuid4)
    )
    username: str
    email: str
    first_name: str
    last_name: str
    is_verufied: bool = Field(default=False)
    password_hash: str = Field(exclude=True)
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))
    updated_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))

    def __repr__(self) -> str:
        return f"<User {self.username}>"