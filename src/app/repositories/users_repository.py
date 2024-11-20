from abc import ABC, abstractmethod

from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.app.database.models import UserModel


class IUserRepository(ABC):
    @abstractmethod
    async def get(self, user_id: int):
        pass

    @abstractmethod
    async def add(self, user: UserModel):
        pass

    @abstractmethod
    async def update(self, user: UserModel):
        pass

    @abstractmethod
    async def delete(self, user_id: int):
        pass

    @abstractmethod
    async def commit(self):
        pass


class UserRepository(IUserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def check_user(self, username: str) -> bool:
        result = await self.session.execute(
            select(UserModel).where(UserModel.username == username)
        )
        return result.scalar() is not None

    async def get_user(self, username: str):
        async with self.session.begin():
            result = await self.session.execute(
                select(UserModel).where(UserModel.username == username)
            )
            return result.scalar_one_or_none()

    async def create_user(self, user: UserModel):
        self.session.add(user)
        await self.session.commit()

    async def update_active_user(self, username: str):
        result = await self.session.execute(
            select(UserModel).where(UserModel.username == username)
        )
        user = result.scalar_one_or_none()
        if user is None:
            raise NoResultFound()
        user.is_active = True
        await self.session.commit()

    async def delete(self, user_id: int):
        async with self.session.begin():
            user = await self.get(user_id)
            if user:
                await self.session.delete(user)
                await self.session.commit()

    async def commit(self):
        await self.session.commit()
