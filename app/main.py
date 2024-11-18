from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from app.core.setup_test_data import setup_execute
from app.database.db_helper import db_helper
from app.database.models import Base
from app.routers.routers_articles import router as blog_router
from app.routers.routers_auth import router as auth_router


@asynccontextmanager
async def lifespan(apps: FastAPI):
    async with db_helper.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await setup_execute(conn)
    yield
    async with db_helper.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.commit()


app = FastAPI(title="Marketplace.com", lifespan=lifespan)

app.include_router(auth_router)
app.include_router(blog_router)

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
