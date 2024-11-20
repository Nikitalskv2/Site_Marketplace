from typing import Annotated

from annotated_types import MaxLen, MinLen
from pydantic import BaseModel, ConfigDict, EmailStr


class CreateUser(BaseModel):
    username: Annotated[str, MinLen(3), MaxLen(25)]
    email: EmailStr


class UserSchema(BaseModel):
    model_config = ConfigDict(strict=True)

    username: str
    password: bytes
    email: EmailStr | None = None
    active: bool = False


class TokenInfo(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "Bearer"


class Categories(BaseModel):
    category_name: str


class CategoryArticle(BaseModel):
    category_id: int
    article_id: int


class Article(BaseModel):
    title: str
    short_description: str
    link_body: str
    s3_key: str
    created_data: str | None = None
    author: str
