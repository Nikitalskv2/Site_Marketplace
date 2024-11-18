from fastapi import Depends
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db_helper import db_helper
from app.database.models import ArticleModel, CategoriesModel, CategoryArticleModel


async def setup_execute(
    session: AsyncSession = Depends(db_helper.session_dependency),  # noqa: B008
):
    category = insert(CategoriesModel).values(
        [
            {"category_name": "category 1"},
            {"category_name": "category 2"},
            {"category_name": "category 3"},
            {"category_name": "category 4"},
            {"category_name": "category 5"},
            {"category_name": "category 6"},
        ]
    )
    await session.execute(category)
    await session.commit()

    article = insert(ArticleModel).values(
        [
            {
                "article_name": "name article 1",
                "short_description": "short_description 1",
                "link_main_image": "https://",
                "link_body": "https://",
            },
            {
                "article_name": "name article 2",
                "short_description": "short_description 2",
                "link_main_image": "https://",
                "link_body": "https://",
            },
            {
                "article_name": "name article 3",
                "short_description": "short_description 3",
                "link_main_image": "https://",
                "link_body": "https://",
            },
            {
                "article_name": "name article 4",
                "short_description": "short_description 4",
                "link_main_image": "https://",
                "link_body": "https://",
            },
            {
                "article_name": "name article 5",
                "short_description": "short_description 5",
                "link_main_image": "https://",
                "link_body": "https://",
            },
            {
                "article_name": "name article 6",
                "short_description": "short_description 6",
                "link_main_image": "https://",
                "link_body": "https://",
            },
            {
                "article_name": "name article 7",
                "short_description": "short_description 7",
                "link_main_image": "https://",
                "link_body": "https://",
            },
        ]
    )
    await session.execute(article)
    await session.commit()

    category_article = insert(CategoryArticleModel).values(
        [
            {"category_id": 0, "article_id": 0},
            {"category_id": 1, "article_id": 1},
            {"category_id": 2, "article_id": 2},
            {"category_id": 3, "article_id": 3},
            {"category_id": 4, "article_id": 4},
            {"category_id": 5, "article_id": 5},
            {"category_id": 0, "article_id": 6},
            {"category_id": 1, "article_id": 0},
            {"category_id": 2, "article_id": 1},
        ]
    )
    await session.execute(category_article)
    await session.commit()
