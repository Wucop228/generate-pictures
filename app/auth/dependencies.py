from typing import Optional

from fastapi import Cookie, HTTPException, status

async def get_token(access_token: Optional[str] = Cookie(None)) -> str:
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не авторизован"
        )
    return access_token