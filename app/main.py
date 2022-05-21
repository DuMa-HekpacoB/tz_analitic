import csv
import datetime
import os
from asyncio import sleep
from collections import OrderedDict
from typing import List, Optional
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import FastAPI, Query
from models import Base, engine, Document
from schemas import DocumentCreateSchema, DocumentSchema
from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk, async_scan
import time


app = FastAPI()
time.sleep(5) # ждём пока запустится эластик
es = AsyncElasticsearch(["elasticsearch:9200"])


async def gendata(docs: list):
    for i_doc in docs:
        yield {
            "_index": "my_documents",
            "doc": {"id": i_doc.id, "text": i_doc.text}
        }

@app.on_event("shutdown")
async def app_shutdown():
    await es.close()


@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSession(engine) as session:
        row = await session.execute(select(Document))
        if not list(row):
            path = os.path.abspath("posts.csv")
            document_pd_object = []
            with open(path, mode="r", encoding="UTF-8") as csvf:
                for i_row in csv.DictReader(csvf, delimiter=","):
                    document_pd_object.append(DocumentCreateSchema.parse_obj(i_row))

            session.add_all([Document(**i_row.dict()) for i_row in document_pd_object])
            await session.commit()
            stmt = select(Document)
            result = await session.execute(stmt)
            await async_bulk(es, gendata(result.scalars().all()))

@app.get("/", response_model=List[DocumentSchema])
async def presentation(text: Optional[str] = Query(default="")):
    documents_ids = []
    async for doc in async_scan(
            client=es,
            query={"query": {"query_string": {"query": text}}},
            index="my_documents"
        ):
        documents_ids.append(doc.get("_source", {}).get("doc", {}).get("id"))
    async with AsyncSession(engine) as session:
        stmt = select(Document).filter(Document.id.in_(documents_ids)).order_by(Document.created_date).limit(20)

        result = await session.execute(stmt)
    return [DocumentSchema.from_orm(i_doc) for i_doc in result.scalars().all()]


@app.delete("/{item_id}", response_model=str)
async def delete_doc(item_id: int):
    async with AsyncSession(engine) as session:
        stmt = select(Document).filter(Document.id == item_id)
        result = await session.execute(stmt)
        document = result.scalars().first()
        if document is None:
            return "Документ не найден"
        await session.delete(document)
        await session.commit()
        stmt = select(Document)
        result = await session.execute(stmt)
        await async_bulk(es, gendata(result.scalars().all()))
    return "Объект удалён"

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)