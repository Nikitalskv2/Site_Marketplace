from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql.expression import func

from src.app.database.models import ArticleModel


class ArticleRepository:
    def __init__(self, minio_client, bucket_name: str):
        self.minio_client = minio_client
        self.bucket_name = bucket_name

    async def upload_article(
        self, session: AsyncSession, title: str, description: str, content: str
    ):
        s3_key = f"{title.replace(' ', '_')}.txt"
        self.minio_client.put_object(
            Bucket=self.bucket_name,
            Key=s3_key,
            Body=content.encode("utf-8"),
            ContentType="text/plain",
        )

        article = ArticleModel(
            title=title,
            short_description=description,
            s3_key=s3_key,
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

    async def get_article_content(self, s3_key: str):
        response = self.minio_client.get_object(Bucket=self.bucket_name, Key=s3_key)
        return response["Body"].read().decode("utf-8")
