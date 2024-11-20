import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from src.app.core.config import settings


class Base(DeclarativeBase):
    __abstract__ = True
    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)


class UserModel(Base):
    __tablename__ = "users"
    user_id = mapped_column(UUID(as_uuid=True), default=uuid.uuid4)
    username: Mapped[str] = mapped_column(nullable=False)
    password: Mapped[bytes] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(nullable=False)
    active: Mapped[bool] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=settings.timezone), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=settings.timezone), onupdate=func.now(), nullable=True
    )


class CategoryArticleModel(Base):
    __tablename__ = "categories_articles"
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True
    )
    article_id: Mapped[int] = mapped_column(
        ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True
    )


class CategoriesModel(Base):
    __tablename__ = "categories"
    category_name: Mapped[str] = mapped_column(nullable=False)
    articles = relationship(
        "ArticleModel", secondary="categories_articles", back_populates="categories"
    )


class ArticleModel(Base):
    __tablename__ = "articles"
    title: Mapped[str] = mapped_column(nullable=False)
    short_description: Mapped[str] = mapped_column(nullable=False)
    link_body: Mapped[str] = mapped_column(nullable=False)
    s3_key: Mapped[str] = mapped_column(nullable=False)
    author: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=settings.timezone), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=settings.timezone), onupdate=func.now(), nullable=True
    )
    search_vector = mapped_column(TSVECTOR, nullable=True)
    categories = relationship(
        "CategoriesModel", secondary="categories_articles", back_populates="articles"
    )
