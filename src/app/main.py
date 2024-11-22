import asyncio
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager

from src.app.database.db_helper import db_helper
from src.app.database.models import Base
from src.app.routers.routers_articles import router as blog_router
from src.app.routers.routers_auth import router as auth_router


@asynccontextmanager
async def lifespan(apps: FastAPI):
    for _ in range(10):
        try:
            async with db_helper.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            break
        except Exception as e:
            print(f"Database not ready, retrying... {e}")
            await asyncio.sleep(2)
    else:
        raise RuntimeError("Database not ready after 10 retries")
    yield

    async with db_helper.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.commit()


app = FastAPI(title="Marketplace.com", lifespan=lifespan)

app.include_router(auth_router)
app.include_router(blog_router)

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
