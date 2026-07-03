from typing import Optional
from typing_extensions import Annotated
from pydantic import BaseModel
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from apps.db_models import User as DBUser

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/custom-auth/login/")


class TokenData(BaseModel):
    user_id: Optional[str] = None


def get_user(user_id: int):
    from main import settings
    session = settings.db.SessionLocal()
    try:
        return session.query(DBUser).filter(DBUser.id == user_id).first()
    finally:
        session.close()


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)]
):
    from main import settings
    SECRET_KEY = settings.SECRET_KEY
    ALGORITHM = settings.ALGORITHM

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception

        token_data = TokenData(user_id=user_id)

    except JWTError:
        raise credentials_exception

    user = get_user(int(token_data.user_id))

    if user is None:
        raise credentials_exception

    return user