from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, aliased  # AsyncSessionの代わりにSessionをインポート
from sqlalchemy import func, or_, and_, Integer
from sqlalchemy.sql import exists
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
    userId: str
    practiceDetails: List[PracticeDetailModel]

class RecordModel(BaseModel):
    id: int
    description: str
    date: datetime.date
    startTime: str
    startMinute: str
    endTime: str
    endMinute: str
    userId: str
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
        userId=record_data.userId,
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
def get_records_by_month(year: int, month: int, userId: str, db: Session = Depends(get_db)):
    start_date = datetime.date(year, month, 1)
    # 月の最終日を取得するために、翌月の1日から1日引く
    if month == 12:
        end_date = datetime.date(year + 1, 1, 1) - datetime.timedelta(days=1)
    else:
        end_date = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)

    records = db.query(Record).filter(Record.date >= start_date, Record.date <= end_date, Record.userId == userId).all()

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
            userId=record.userId,  # userIdをレスポンスモデルに含める
            practiceDetails=practice_details
        ))

    return result

@app.get("/records/{record_id}", response_model=RecordModel)
def get_record_by_id(record_id: int, userId: str, db: Session = Depends(get_db)):
    record = db.query(Record).filter(Record.id == record_id, Record.userId == userId).first()
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
        userId=record.userId,  # userIdをレスポンスモデルに含める
        practiceDetails=practice_details
    )

@app.delete("/records/{record_id}")
def delete_record_by_id(record_id: int, userId: str, db: Session = Depends(get_db)):
    # 指定されたIDのRecordを検索し、かつuserIdが一致するものを確認
    record = db.query(Record).filter(Record.id == record_id, Record.userId == userId).first()
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
    # 指定されたIDのRecordを検索し、かつuserIdが一致するものを確認
    record = db.query(Record).filter(Record.id == record_id, Record.userId == record_data.userId).first()
    if record is None:
        raise HTTPException(status_code=404, detail="Record not found")

    # Recordの情報を更新
    record.description = record_data.description
    record.date = record_data.date
    record.startTime = record_data.startTime
    record.startMinute = record_data.startMinute
    record.endTime = record_data.endTime
    record.endMinute = record_data.endMinute
    # userIdの更新は不要なので、ここでは触らない

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

@app.get("/analysis_tag")
def get_analysis(start_date: Optional[datetime.date] = None, end_date: Optional[datetime.date] = None, contents: List[str] = Query(None), tag_names: List[str] = Query(None), description: Optional[str] = None, db: Session = Depends(get_db)):
    # 基本となるクエリを構築
    query = db.query(PracticeDetail.content, Tag.name, func.count(Tag.name).label('count'))\
              .join(PracticeDetail.practiceTags)\
              .join(Record, Record.id == PracticeDetail.recordId)\
              .group_by(PracticeDetail.content, Tag.name)

    # 期間フィルタリング
    date_filters = []
    if start_date:
        date_filters.append(Record.date >= start_date)
    if end_date:
        date_filters.append(Record.date <= end_date)
    if date_filters:
        query = query.filter(and_(*date_filters))

    # contentフィルタリング
    if contents:
        query = query.filter(or_(*[PracticeDetail.content == content for content in contents]))

    # tag_namesフィルタリング
    if tag_names:
        query = query.filter(or_(*[Tag.name == tag_name for tag_name in tag_names]))

    # descriptionフィルタリング（部分一致）
    if description:
        query = query.filter(Record.description.like(f"%{description}%"))

    # 結果を取得
    raw_result = query.all()

    # 結果を整理
    organized_result = {}
    for content, tag, count in raw_result:
        if content not in organized_result:
            organized_result[content] = []
        organized_result[content].append({tag: count})

    # 最終的な形式に変換
    final_result = [{content: tags} for content, tags in organized_result.items()]

    return final_result


@app.get("/analysis_detail")
def get_detailed_analysis(
    start_date: Optional[datetime.date] = None, 
    end_date: Optional[datetime.date] = None, 
    contents: List[str] = Query(None), 
    tag_names: List[str] = Query(None), 
    description: Optional[str] = None, 
    condition: Optional[str] = "and",
    db: Session = Depends(get_db)
):
    # タグ名に基づくサブクエリを構築
    if tag_names:
        if condition == "or":
            tag_conditions = [Tag.name == tag_name for tag_name in tag_names]
            tag_subquery = db.query(PracticeDetail.id)\
                .join(PracticeDetail.practiceTags)\
                .filter(or_(*tag_conditions))\
                .subquery()
        else:  # デフォルトは "and" 条件
            tag_conditions = [func.sum((Tag.name == tag_name).cast(Integer)) >= 1 for tag_name in tag_names]
            tag_subquery = db.query(PracticeDetail.id)\
                .join(PracticeDetail.practiceTags)\
                .group_by(PracticeDetail.id)\
                .having(and_(*tag_conditions))\
                .subquery()

    # タグ名を集約するためのサブクエリ
    tags_subquery = db.query(
        PracticeDetail.id.label("pd_id"),
        func.array_agg(Tag.name).label("tags")
    ).join(
        PracticeDetail.practiceTags
    ).group_by(
        PracticeDetail.id
    ).subquery()

    # 基本となるクエリを構築
    query = db.query(
        PracticeDetail.id, 
        PracticeDetail.content, 
        Record.description, 
        Record.date,
        tags_subquery.c.tags
    ).distinct(PracticeDetail.id).join(
        Record, Record.id == PracticeDetail.recordId
    ).outerjoin(
        tags_subquery, tags_subquery.c.pd_id == PracticeDetail.id
    )

    if tag_names:
        query = query.join(tag_subquery, PracticeDetail.id == tag_subquery.c.id)

    # 期間フィルタリング
    if start_date:
        query = query.filter(Record.date >= start_date)
    if end_date:
        query = query.filter(Record.date <= end_date)

    # contentフィルタリング
    if contents:
        query = query.filter(or_(*[PracticeDetail.content == content for content in contents]))

    # descriptionフィルタリング（部分一致）
    if description:
        query = query.filter(Record.description.like(f"%{description}%"))

    # 結果を取得
    result = query.all()

    # 結果を整理
    final_result = [{
        "id": id_,
        "content": content, 
        "description": record_description, 
        "date": record_date.strftime("%Y-%m-%d"), 
        "tags": tags
    } for id_, content, record_description, record_date, tags in result]

    return final_result
