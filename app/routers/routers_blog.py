from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer, OAuth2PasswordBearer

http_bearer = HTTPBearer(auto_error=False)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/jwt/login/")

router = APIRouter(
    prefix="/blog", tags=["articles"], dependencies=[Depends(http_bearer)]
)


@router.get("/")
def output_articles(
    page_size: int,
    page: int,
):
    pass
