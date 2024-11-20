from fastapi import APIRouter, Depends, HTTPException
from fastapi.params import Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.auth.tokens import (
    get_current_active_auth_user,
    get_current_token_payload,
    http_bearer,
)
from src.app.database.db_helper import db_helper
from src.app.repositories import s3_repository
from src.app.repositories import article_repository
from src.app.schemas.schemas import UserSchema
from src.app.services.article_service import ArticleService

article_service = ArticleService(article_repository, s3_repository)

router = APIRouter(
    prefix="/articles", tags=["articles"], dependencies=[Depends(http_bearer)]
)


@router.get("/random/")
async def get_random_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    session: AsyncSession = Depends(db_helper.session_dependency),
    article_repo: article_repository.ArticleRepository = Depends(),
    category_id: int = Query(None),
):
    try:
        total_articles_result = await article_repo.get_article_count(
            session=session, category_id=category_id
        )

        if total_articles_result == 0:
            return {"page": page, "page_size": page_size, "total": 0, "articles": []}
        else:
            article_ids = await article_repo.get_id_articles(
                session=session, page=page, page_size=page_size, category_id=category_id
            )

            articles = []
            for article_id in article_ids:
                metadata = await article_repo.get_article_metadata(session, article_id)
                if metadata:
                    articles.append(metadata)

            return {
                "page": page,
                "page_size": page_size,
                "total": total_articles_result,
                "articles": articles,
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.post("/upload/")
async def upload_article(
    title: str,
    description: str,
    content: str,
    session: AsyncSession = Depends(db_helper.session_dependency),
    payload: dict = Depends(get_current_token_payload),
    user: UserSchema = Depends(get_current_active_auth_user),
):
    try:
        if not user:
            raise HTTPException(status_code=401, detail="Unauthorized: user not found")
        author = payload.get("username")
        if not author:
            raise HTTPException(
                status_code=400, detail="Invalid token: username not found"
            )
        article = await article_service.upload_article(
            session=session,
            title=title,
            description=description,
            content=content,
            author=author,
        )
        return {
            "message": "Article uploaded successfully",
            "article": article,
            "author": user.username,
        }
    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.get("/search/")
async def search_articles(
    query: str, session: AsyncSession = Depends(db_helper.session_dependency)
):
    return await article_service.search_articles(session=session, query=query)


@router.get("/{article_id}/content")
async def get_article_content(
    article_id: int, session: AsyncSession = Depends(db_helper.session_dependency)
):
    return await article_service.get_article_content(
        session=session, article_id=article_id
    )
