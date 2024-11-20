from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql.expression import func

from src.app.database.models import ArticleModel, CategoryArticleModel


class ArticleRepository:
    async def add_article(
        self,
        session: AsyncSession,
        title: str,
        description: str,
        s3_key: str,
        author: str,
    ):
        search_vector = func.to_tsvector("russian", f"{title} {description}")
        article = ArticleModel(
            title=title,
            short_description=description,
            s3_key=s3_key,
            search_vector=search_vector,
            author=author,
        )
        session.add(article)
        await session.commit()
        await session.refresh(article)
        return article

    async def search_articles(self, session: AsyncSession, query: str):
        search_query = func.to_tsquery("russian", query)
        result = await session.execute(
            select(ArticleModel)
            .where(ArticleModel.search_vector.op("@@")(search_query))
            .order_by(func.ts_rank(ArticleModel.search_vector, search_query).desc())
        )
        return result.scalars().all()

    async def get_article_metadata(self, session: AsyncSession, article_id: int):
        try:
            result = await session.execute(
                select(ArticleModel).where(ArticleModel.id == article_id)
            )
            return result.scalar_one()
        except NoResultFound:
            return None

    async def get_article_count(self, session: AsyncSession, category_id: int) -> int:
        query = select(func.count(ArticleModel.id))
        if category_id:
            query = query.join(CategoryArticleModel).where(
                CategoryArticleModel.category_id == category_id
            )
        res = await session.execute(query)
        return res.scalar()

    async def get_id_articles(
        self, session: AsyncSession, page: int, page_size: int, category_id: int
    ):
        offset = (page - 1) * page_size
        query = (
            select(ArticleModel.id)
            .order_by(func.random())
            .offset(offset)
            .limit(page_size)
        )
        if category_id:
            query = query.join(CategoryArticleModel).where(
                CategoryArticleModel.category_id == category_id
            )

        result = await session.execute(query)
        return [row[0] for row in result.fetchall()]
