import sqlalchemy as db
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLALCHEMY_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5435"
SQLALCHEMY_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@postgres:5432"

engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


class Document(Base):
    __tablename__ = "documents"

    id = db.Column(db.Integer, primary_key=True, index=True)
    rubrics = db.Column(db.ARRAY(db.String))
    text = db.Column(db.String)
    created_date = db.Column(db.DateTime)
