from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session  # AsyncSessionの代わりにSessionをインポート
from models import Base, SessionLocal, engine, Record, PracticeDetail, Tag
from pydantic import BaseModel, Field
from typing import List, Optional
import datetime

app = FastAPI()

# CORSを許可するオリジンのリスト
origins = [
    "http://localhost:3000",  # Reactアプリケーションのオリジン
    "https://practice-record.vercel.app",  # FastAPIアプリケーション自身のオリジン（必要に応じて）
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # すべてのオリジンを許可する場合は ["*"] を使用
    allow_credentials=True,
    allow_methods=["*"],  # すべてのHTTPメソッドを許可
    allow_headers=["*"],  # すべてのHTTPヘッダーを許可
)

# データベース接続の依存関係
def get_db():  # 非同期関数から同期関数に変更
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

class PracticeTag(BaseModel):
    name: str

class PracticeDetailModel(BaseModel):
    content: str
    tags: List[PracticeTag]

class CreateRecordModel(BaseModel):
    description: str
    date: datetime.date
    startTime: str
    startMinute: str
    endTime: str
    endMinute: str
    practiceDetails: List[PracticeDetailModel]

class RecordModel(BaseModel):
    id: int
    description: str
    date: datetime.date
    startTime: str
    startMinute: str
    endTime: str
    endMinute: str
    practiceDetails: List[PracticeDetailModel]

@app.post("/records/")
def create_record(record_data: CreateRecordModel, db: Session = Depends(get_db)):
    new_record = Record(
        description=record_data.description,
        date=record_data.date,
        startTime=record_data.startTime,
        startMinute=record_data.startMinute,
        endTime=record_data.endTime,
        endMinute=record_data.endMinute,
    )
    db.add(new_record)
    db.flush()  # RecordインスタンスをフラッシュしてIDを取得

    for detail in record_data.practiceDetails:
        new_detail = PracticeDetail(
            content=detail.content,
            recordId=new_record.id  # ここでRecordのIDを使用
        )
        db.add(new_detail)
        # 各PracticeDetailに対して、タグを処理
        for tag in detail.tags:
            # 既存のタグを検索
            existing_tag = db.query(Tag).filter(Tag.name == tag.name).first()
            if existing_tag is None:
                # タグが存在しない場合は新しいタグを作成
                new_tag = Tag(name=tag.name)
                db.add(new_tag)
                db.flush()  # 新しいタグのIDを確実に取得するためにflush
                new_detail.practiceTags.append(new_tag)
            else:
                # タグが既に存在する場合は、そのタグを使用
                new_detail.practiceTags.append(existing_tag)

    db.commit()  # すべてのデータが追加された後に一度だけcommit

    return {"message": "Record created successfully"}

@app.get("/records/{year}/{month}", response_model=List[RecordModel])
def get_records_by_month(year: int, month: int, db: Session = Depends(get_db)):
    start_date = datetime.date(year, month, 1)
    # 月の最終日を取得するために、翌月の1日から1日引く
    if month == 12:
        end_date = datetime.date(year + 1, 1, 1) - datetime.timedelta(days=1)
    else:
        end_date = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)

    records = db.query(Record).filter(Record.date >= start_date, Record.date <= end_date).all()

    result = []
    for record in records:
        practice_details = []
        for detail in record.practiceDetails:
            tags = [PracticeTag(name=tag.name) for tag in detail.practiceTags]
            practice_details.append(PracticeDetailModel(content=detail.content, tags=tags))
        result.append(RecordModel(
            id=record.id,
            description=record.description,
            date=record.date,
            startTime=record.startTime,
            startMinute=record.startMinute,
            endTime=record.endTime,
            endMinute=record.endMinute,
            practiceDetails=practice_details
        ))

    return result

@app.get("/records/{record_id}", response_model=RecordModel)
def get_record_by_id(record_id: int, db: Session = Depends(get_db)):
    record = db.query(Record).filter(Record.id == record_id).first()
    if record is None:
        raise HTTPException(status_code=404, detail="Record not found")

    practice_details = []
    for detail in record.practiceDetails:
        tags = [PracticeTag(name=tag.name) for tag in detail.practiceTags]
        practice_details.append(PracticeDetailModel(content=detail.content, tags=tags))

    return RecordModel(
        id=record.id,
        description=record.description,
        date=record.date,
        startTime=record.startTime,
        startMinute=record.startMinute,
        endTime=record.endTime,
        endMinute=record.endMinute,
        practiceDetails=practice_details
    )

@app.delete("/records/{record_id}")
def delete_record_by_id(record_id: int, db: Session = Depends(get_db)):
    # 指定されたIDのRecordを検索
    record = db.query(Record).filter(Record.id == record_id).first()
    if record is None:
        raise HTTPException(status_code=404, detail="Record not found")

    # Recordに関連するPracticeDetailを検索し、それぞれに関連するTagの関連付けを削除
    for detail in record.practiceDetails:
        # SQLAlchemyの多対多の関連を削除するには、関連するオブジェクトを直接削除する
        detail.practiceTags = []
        db.delete(detail)

    # 最後にRecord自体を削除
    db.delete(record)
    db.commit()

    return {"message": "Record deleted successfully"}

@app.put("/records/{record_id}")
def update_record_by_id(record_id: int, record_data: CreateRecordModel, db: Session = Depends(get_db)):
    # 指定されたIDのRecordを検索
    record = db.query(Record).filter(Record.id == record_id).first()
    if record is None:
        raise HTTPException(status_code=404, detail="Record not found")

    # Recordの情報を更新
    record.description = record_data.description
    record.date = record_data.date
    record.startTime = record_data.startTime
    record.startMinute = record_data.startMinute
    record.endTime = record_data.endTime
    record.endMinute = record_data.endMinute

    # 既存のPracticeDetailを削除
    for detail in record.practiceDetails:
        db.delete(detail)
    db.commit()  # 変更をコミット

    # 新しいPracticeDetailとTagを追加
    for detail_data in record_data.practiceDetails:
        new_detail = PracticeDetail(content=detail_data.content, recordId=record.id)
        db.add(new_detail)
        db.flush()  # IDを確実に取得するためにflush

        for tag_data in detail_data.tags:
            # 既存のタグを検索、なければ新規作成
            tag = db.query(Tag).filter(Tag.name == tag_data.name).first()
            if tag is None:
                tag = Tag(name=tag_data.name)
                db.add(tag)
                db.flush()  # 新しいタグのIDを確実に取得するためにflush
            new_detail.practiceTags.append(tag)

    db.commit()  # 最終的な変更をコミット

    return {"message": "Record updated successfully"}
