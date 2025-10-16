from fastapi import APIRouter, status, HTTPException, Response

from app.users.dao import UsersDAO
from app.auth.schemas import AuthUser
from app.auth.utils import verify_password, create_access_token, validate_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post('/login', status_code=status.HTTP_200_OK)
async def auth_user(authUser: AuthUser, response: Response):
    user = await UsersDAO.find_one_or_none(email=authUser.email)

    is_valid = False
    if user:
        is_valid = verify_password(authUser.password, user.password)
    else:
        verify_password(
            authUser.password,
            "$2b$12$q6VtHKLMERC2AkoXOFJ1eubTxllYp/dxUsR3coNAhhQYg.121Fqbi"
        )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверная почта или пароль"
        )

    access_token = create_access_token({
        "sub": str(user.id),
        "is_admin": user.is_admin
    })
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=3600,
        samesite="lax",
    )

    return {
        "message": "Успешная авторизация",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_admin": user.is_admin
        }
    }

@router.post('/logout', status_code=status.HTTP_200_OK)
async def logout(response: Response):
    response.delete_cookie(key="access_token")
    return {"message": "Успешный выход"}

# @router.get('/validate-access-token', status_code=status.HTTP_200_OK)
# async def check_token(token: str):
#     user_id = validate_access_token(token)
#     return user_id