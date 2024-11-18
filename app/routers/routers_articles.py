from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer, OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db_helper import db_helper
from app.database.minio_helper import S3Repository
from app.repositories.articles import ArticleRepository

http_bearer = HTTPBearer(auto_error=False)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/jwt/login/")

router = APIRouter(
    prefix="/articles", tags=["articles"], dependencies=[Depends(http_bearer)]
)
s3_repo = S3Repository(
    endpoint_url="http://localhost:9000",
    access_key="admin",
    secret_key="password",
    bucket_name="articles",
)
article_repo = ArticleRepository(s3_repo)


@router.get("/search/")
async def search_articles(
    query: str, session: AsyncSession = Depends(db_helper.session_dependency)
):
    article_repo = ArticleRepository(session)
    articles = await article_repo.search_articles(session, query)
    return articles
