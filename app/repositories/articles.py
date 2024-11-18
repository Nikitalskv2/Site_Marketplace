from abc import ABC, abstractmethod
from typing import List, Optional

from sqlalchemy.dialects.postgresql import to_tsvector
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import func

from app.database.models import ArticleModel, CategoriesModel
from app.schemas.schemas import Article


class IArticleRepository(ABC):
    @abstractmethod
    async def get_all_articles(self) -> List[ArticleModel]:
        pass

    @abstractmethod
    async def get_article_by_id(self, article_id: int) -> Optional[ArticleModel]:
        pass

    @abstractmethod
    async def create_article(self, article_data: Article) -> ArticleModel:
        pass

    @abstractmethod
    async def update_article(
        self, article_id: int, article_data: Article
    ) -> ArticleModel:
        pass

    @abstractmethod
    async def delete_article(self, article_id: int) -> None:
        pass

    @abstractmethod
    async def search_articles(self, query: str) -> List[ArticleModel]:
        pass


class ArticleRepository(IArticleRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_articles(self) -> List[ArticleModel]:
        result = await self.session.execute(
            select(ArticleModel).options(joinedload(CategoriesModel.categories))
        )
        return result.scalars().all()

    async def get_article_by_id(self, article_id: int) -> Optional[ArticleModel]:
        try:
            result = await self.session.execute(
                select(ArticleModel)
                .options(joinedload(ArticleModel.categories))
                .where(ArticleModel.id == article_id)
            )
            return result.scalar_one()
        except NoResultFound:
            return None

    async def create_article(self, article_data: Article) -> ArticleModel:
        new_article = ArticleModel(**article_data.dict())
        self.session.add(new_article)
        await self.session.commit()
        await self.session.refresh(new_article)
        return new_article

    async def update_article(
        self, article_id: int, article_data: Article
    ) -> ArticleModel:
        article = await self.get_article_by_id(self.session, article_id)
        if not article:
            raise NoResultFound()

        for key, value in article_data.dict(exclude_unset=True).items():
            setattr(article, key, value)

        await self.session.commit()
        await self.session.refresh(article)
        return article

    async def delete_article(self, article_id: int) -> None:
        article = await self.get_article_by_id(self.session, article_id)
        if not article:
            raise NoResultFound()

        await self.session.delete(article)
        await self.session.commit()

    async def search_articles(self, query: str) -> List[ArticleModel]:
        search_query = to_tsvector("russian", query)
        result = await self.session.execute(
            select(ArticleModel)
            .where(ArticleModel.search_vector.op("@@")(search_query))
            .order_by(func.ts_rank(ArticleModel.search_vector, search_query).desc())
        )
        return result.scalars().all()
