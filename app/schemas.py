from typing import List
import datetime
import json

from pydantic import BaseModel, validator


class DocumentCreateSchema(BaseModel):
    rubrics: List[str]
    text: str
    created_date: datetime.datetime

    @validator("rubrics", pre=True)
    def parse_rubrics(cls, value):
        return json.loads(value.replace("'", '"'))

    @validator("created_date", pre=True)
    def parse_created_date(cls, value):
        return datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S')


class DocumentSchema(BaseModel):
    id: int
    rubrics: List[str]
    text: str
    created_date: datetime.datetime

    class Config:
        orm_mode = True
