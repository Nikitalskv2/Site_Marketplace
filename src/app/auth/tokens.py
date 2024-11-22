from datetime import timedelta

from fastapi import Depends, Form, HTTPException
from fastapi.security import HTTPBearer, OAuth2PasswordBearer
from jwt import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.app.auth import utils as auth_utils
from src.app.core.config import settings
from src.app.database.db_helper import db_helper
from src.app.repositories.users_repository import UserRepository
from src.app.schemas.schemas import UserSchema

TOKEN_TYPE = "type"
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"

http_bearer = HTTPBearer(auto_error=False)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/jwt/login/")


def create_jwt(
    token_type: str,
    token_data: dict,
    expire_minutes: int = settings.auth_jwt.access_token_expire_minutes,
    expire_timedelta: timedelta | None = None,
) -> str:
    jwt_payload = {TOKEN_TYPE: token_type}
    jwt_payload.update(token_data)
    return auth_utils.encode_jwt(
        payload=jwt_payload,
        expire_minutes=expire_minutes,
        expire_timedelta=expire_timedelta,
    )


def create_access_token(user: UserSchema) -> str:
    jwt_payload = {
        "sub": user.username,
        "username": user.username,
        "email": user.email,
        "active": user.active,
    }
    return create_jwt(
        token_type=ACCESS_TOKEN_TYPE,
        token_data=jwt_payload,
        expire_minutes=settings.auth_jwt.access_token_expire_minutes,
    )


def create_refresh_token(user: UserSchema) -> str:
    jwt_payload = {"sub": user.username}
    return create_jwt(
        token_type=REFRESH_TOKEN_TYPE,
        token_data=jwt_payload,
        expire_timedelta=timedelta(days=settings.auth_jwt.refresh_token_expire_days),
    )


def get_current_token_payload(token: str = Depends(oauth2_scheme)) -> UserSchema:
    try:
        payload = auth_utils.decode_jwt(token=token)
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=f"invalid token: {e}"
        )
    return payload


def validate_token_type(payload: dict, token_type: str) -> bool:
    current_token_type = payload.get(TOKEN_TYPE)
    if current_token_type == token_type:
        return True
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=f"invalid token type {current_token_type!r} expected {token_type!r}",
    )


async def get_user_by_token_sub(
    payload: dict, session: AsyncSession = Depends(db_helper.session_dependency)
) -> UserSchema:
    username: str | None = payload.get("username")
    user_repo = UserRepository(session)
    user = await user_repo.get_user(username=username)
    if user:
        return user
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="token invalid (user not found)",
    )


async def get_current_auth_user(
    payload: dict = Depends(get_current_token_payload),
) -> UserSchema:
    validate_token_type(payload, ACCESS_TOKEN_TYPE)
    return await get_user_by_token_sub(payload)


async def get_current_auth_user_for_refresh(
    payload: dict = Depends(get_current_token_payload),
) -> UserSchema:
    validate_token_type(payload, REFRESH_TOKEN_TYPE)
    return await get_user_by_token_sub(payload)


def get_current_active_auth_user(user: UserSchema = Depends(get_current_auth_user)):
    if user.active:
        return user
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="user inactive")


async def validate_auth_user(
    username: str = Form(),
    password: str = Form(),
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    unauthorized_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid username or password"
    )
    user_repo = UserRepository(session)
    user = await user_repo.get(username=username)

    if not user:
        raise unauthorized_exc

    if not auth_utils.validate_password(
        password=password,
        hashed_password=user.password,
    ):
        raise unauthorized_exc
    return user
