from sqlalchemy.ext.asyncio import AsyncSession

from src.app.database.minio_helper import S3Repository
from src.app.repositories.article_repository import ArticleRepository


class ArticleService:
    def __init__(self, db_repo: ArticleRepository, s3_repo: S3Repository):
        self.db_repo = db_repo
        self.s3_repo = s3_repo

    async def upload_article(
        self,
        session: AsyncSession,
        title: str,
        description: str,
        content: str,
        author: str,
    ):
        article_id = hash(title)
        s3_key = self.s3_repo.upload_article(article_id, content)
        return await self.db_repo.add_article(
            session=session,
            title=title,
            description=description,
            s3_key=s3_key,
            author=author,
        )

    async def search_articles(self, session: AsyncSession, query: str):
        return await self.db_repo.search_articles(session, query)

    async def get_article_content(self, session: AsyncSession, article_id: int):
        metadata = await self.db_repo.get_article_metadata(
            session=session, article_id=article_id
        )
        if not metadata:
            raise RuntimeError("Article not found")
        return self.s3_repo.get_article(metadata.s3_key)
