from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import UserModel


async def check_user(session: AsyncSession, username: str):
    user = await session.scalar(select(UserModel).where(UserModel.username == username))
    return user


async def create_user(
    session: AsyncSession,
    new_user: UserModel,
):
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return new_user.user_id


async def update_active_user(session: AsyncSession, username: str):
    result = await session.execute(
        select(UserModel).where(UserModel.username == username)
    )
    user = result.scalar_one()

    user.active = True
    await session.commit()
    return user
