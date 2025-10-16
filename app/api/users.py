
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import or_

from app.users.schemas import UserRegister, UserPassword
from app.users.dao import UsersDAO
from app.auth.utils import get_password_hash, verify_password, validate_access_token

router = APIRouter(prefix="/users", tags=["users"])

@router.post('/register', status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserRegister) -> dict:
    username = user_data.username
    email = user_data.email.lower()

    user = await UsersDAO.find_one_or_none_by_filter(
        or_(UsersDAO.model.username == username, UsersDAO.model.email == email)
    )
    if user:
        if user.username == username:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Пользователь с именем '{username}' уже существует"
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Пользователь с email '{email}' уже существует"
        )

    try:
        user_dict = user_data.model_dump(exclude=['password'])
        user_dict["password"] = get_password_hash(user_data.password)
        new_user = await UsersDAO.add(**user_dict)

        return {
            "message": f"Пользователь '{username}' успешно зарегистрированы",
            "user_id": new_user.id,
        }
    except Exception as e:
        print(f"Ошибка при регистрации пользователя {username}:{str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при регистрации пользователя"
        )

@router.post('/change-password', status_code=status.HTTP_200_OK)
async def change_password(user_data: UserPassword) -> dict:
    user = await UsersDAO.find_one_or_none(email=user_data.email)

    is_valid = False
    if user:
        is_valid = verify_password(user_data.old_password, user.password)
    else:
        verify_password(
            user_data.old_password,
            "$2b$12$q6VtHKLMERC2AkoXOFJ1eubTxllYp/dxUsR3coNAhhQYg.121Fqbi"
        )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный текущий пароль"
        )

    await UsersDAO.update(
        filter_by={"email": user_data.email},
        password=get_password_hash(user_data.new_password1)
    )
    return {
        "message": "Пароль успешно изменён"
    }

@router.get('/me', status_code=status.HTTP_200_OK)
async def get_me(token: str) -> dict:
    user_id = int(validate_access_token(token)['user_id'])

    user = await UsersDAO.find_one_or_none(id=user_id)
    return user