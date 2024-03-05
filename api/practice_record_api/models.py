import os
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Table, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.orm import sessionmaker

DB_HOST = os.getenv("DB_HOST")
DB_USER_NAME = os.getenv("DB_USER_NAME")
DB_USER_PASS = os.getenv("DB_USER_PASS")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
print(f"{DB_HOST} {DB_USER_NAME} {DB_USER_PASS} {DB_PORT} {DB_NAME}")

SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER_NAME}:{DB_USER_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# PracticeTagとTagの多対多の関係を定義するための補助テーブル
practice_tag_association_table = Table(
    'practice_tag_association',
    Base.metadata,
    Column('practice_detail_id', ForeignKey('practice_details.id'), primary_key=True),
    Column('tag_id', ForeignKey('tags.id'), primary_key=True)
)

class Record(Base):
    __tablename__ = 'records'
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, index=True)
    date = Column(DateTime, index=True)
    startTime = Column(String)
    startMinute = Column(String)
    endTime = Column(String)
    endMinute = Column(String)
    userId = Column(String)
    practiceDetails = relationship("PracticeDetail", back_populates="record")

class PracticeDetail(Base):
    __tablename__ = 'practice_details'
    id = Column(Integer, primary_key=True, index=True)
    recordId = Column(Integer, ForeignKey('records.id'))
    content = Column(String, index=True)
    record = relationship("Record", back_populates="practiceDetails")
    practiceTags = relationship("Tag", secondary=practice_tag_association_table, back_populates="practiceDetails")

class Tag(Base):
    __tablename__ = 'tags'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    practiceDetails = relationship("PracticeDetail", secondary=practice_tag_association_table, back_populates="practiceTags")