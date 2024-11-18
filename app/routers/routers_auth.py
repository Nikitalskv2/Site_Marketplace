from datetime import datetime

import redis
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, OAuth2PasswordBearer
from pydantic import EmailStr
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import utils as auth_utils
from app.auth.send_mail import send_email
from app.auth.tokens import (
    create_access_token,
    create_refresh_token,
    get_current_auth_user_for_refresh,
    get_current_token_payload,
    validate_auth_user,
)
from app.database.db_helper import db_helper
from app.database.models import UserModel
from app.repositories.users import UserRepository
from app.schemas.schemas import TokenInfo, UserSchema

http_bearer = HTTPBearer(auto_error=False)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/jwt/login/")
redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

router = APIRouter(prefix="/jwt", tags=["JWT"], dependencies=[Depends(http_bearer)])


@router.post("/register/", response_model=UserSchema)
async def auth_user_register(
    username: str,
    password: str,
    email: EmailStr,
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    user_repo = UserRepository(session)
    if not await user_repo.check_user(username):
        user = UserSchema(
            username=username, password=auth_utils.hash_password(password), email=email
        )
        await user_repo.create_user(UserModel(**user.model_dump()))
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
    user_repo = UserRepository(session)
    try:
        await user_repo.update_active_user(username=payload["username"])
        return status.HTTP_200_OK
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
