from datetime import datetime

import redis
from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.security import HTTPBearer, OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import EmailStr
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import utils as auth_utils
from app.auth.send_mail import send_email
from app.auth.tokens import (
    ACCESS_TOKEN_TYPE,
    REFRESH_TOKEN_TYPE,
    TOKEN_TYPE,
    create_access_token,
    create_refresh_token,
)
from app.database import crud
from app.database.db_helper import db_helper
from app.database.models import UserModel
from app.schemas.schemas import TokenInfo, UserSchema

http_bearer = HTTPBearer(auto_error=False)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/jwt/login/")
redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

router = APIRouter(prefix="/jwt", tags=["JWT"], dependencies=[Depends(http_bearer)])


# декодирует токен, отдает payload
def get_current_token_payload(token: str = Depends(oauth2_scheme)) -> UserSchema:
    try:
        payload = auth_utils.decode_jwt(token=token)
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=f"invalid token error: {e}"
        )
    return payload


# проверка типа токена
def validate_token_type(
    payload: dict,
    token_type: str,
) -> bool:
    current_token_type = payload.get(TOKEN_TYPE)
    if current_token_type == token_type:
        return True
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=f"invalid token type {current_token_type!r} expected {token_type!r}",
    )


# отдает из токена user из БД
async def get_user_by_token_sub(
    payload: dict, session: AsyncSession = Depends(db_helper.session_dependency)
) -> UserSchema:
    username: str | None = payload.get("username")
    user = await crud.check_user(session=session, username=username)
    if user:
        return user
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="token invalid (user not found)",
    )


# берет payload, отдает user из БД если токен ACCESS
async def get_current_auth_user(
    payload: dict = Depends(get_current_token_payload),
) -> UserSchema:
    validate_token_type(payload, ACCESS_TOKEN_TYPE)
    return await get_user_by_token_sub(payload)


# берет payload, отдает user из БД если токен REFRESH
async def get_current_auth_user_for_refresh(
    payload: dict = Depends(get_current_token_payload),
) -> UserSchema:
    validate_token_type(payload, REFRESH_TOKEN_TYPE)
    return await get_user_by_token_sub(payload)


# берет user из БД если токен ACCESS, и отдает user если он active
def get_current_active_auth_user(user: UserSchema = Depends(get_current_auth_user)):
    if user.active:
        return user
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="user inactive")


# принимает name, pass , отдает user
async def validate_auth_user(
    username: str = Form(),
    password: str = Form(),
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    unauthorized_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid username or password"
    )
    user = await crud.check_user(session=session, username=username)
    if not user:  # проверка есть ли user по username в БД
        raise unauthorized_exc

    if not auth_utils.validate_password(  # проверка введеного и записанного в БД password
        password=password,
        hashed_password=user.password,
    ):
        raise unauthorized_exc
    return user


# запись нового user отправка письма
@router.post("/register/", response_model=UserSchema)
async def auth_user_register(
    username: str,
    password: str,
    email: EmailStr,
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    check_user = await crud.check_user(session=session, username=username)
    if not check_user:

        user = UserSchema(
            username=username, password=auth_utils.hash_password(password), email=email
        )
        await crud.create_user(session=session, new_user=UserModel(**user.model_dump()))
        token = create_access_token(user)
        send_email(token, address=email)
        return user
    else:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User already exists"
        )


@router.post("/login/", response_model=TokenInfo)
def auth_user_issue_jwt(user: UserSchema = Depends(validate_auth_user)):
    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)
    return TokenInfo(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh/", response_model=TokenInfo, response_model_exclude_none=True)
def auth_refresh_jwt(user: UserSchema = Depends(get_current_auth_user_for_refresh)):
    access_token = create_access_token(user)
    return TokenInfo(access_token=access_token)


@router.post("/confirm/{token}")
async def confirmation_email_user(
    session: AsyncSession = Depends(db_helper.session_dependency),
    payload: dict = Depends(get_current_token_payload),
):
    try:
        await crud.update_active_user(session=session, username=payload["username"])
        return status.HTTP_200_OK  # ok
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with username {payload['username']} not found",
        )


@router.post("/logout")
def logout(token: str = Depends(oauth2_scheme)):
    payload = auth_utils.decode_jwt(token)
    exp_time = payload["exp"] - int(datetime.utcnow().timestamp())
    redis_client.setex(token, exp_time, "revoked")
    return {"message": "Successfully logged out"}
