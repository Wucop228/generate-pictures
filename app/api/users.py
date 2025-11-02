import logging

from fastapi import APIRouter, HTTPException, status, Request
from sqlalchemy import or_

from app.users.schemas import UserRegister, UserPassword
from app.users.dao import UsersDAO
from app.auth.utils import get_password_hash, verify_password

router = APIRouter(prefix="/users", tags=["users"])
logger = logging.getLogger("app.api.users")

@router.post('/register', status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserRegister) -> dict:
    logger.info("Создание пользователя: email=%s", user_data.email)

    username = user_data.username
    email = user_data.email.lower()

    try:
        user = await UsersDAO.find_one_or_none_by_filter(
            or_(UsersDAO.model.username == username, UsersDAO.model.email == email)
        )
    except Exception:
        logger.exception("Сбой чтения пользователя из БД: email=%s", email)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Не удалось получить пользователя")
    logger.debug("Проверка на существования пользователя: email=%s username=%s exists=%s",
                 email, username, user is not None)

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

        logger.info("Пользователь успешно создан: email=%s username=%s", email, username)
        return {
            "message": f"Пользователь '{username}' успешно зарегистрирован",
            "user_id": new_user.id,
        }
    except Exception:
        logger.exception("Сбой добавления пользователя в БД: email=%s username=%s", email, username)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при регистрации пользователя"
        )

@router.post('/change-password', status_code=status.HTTP_200_OK)
async def change_password(user_data: UserPassword) -> dict:
    logger.info("Изменение пароля: email=%s", user_data.email)

    try:
        user = await UsersDAO.find_one_or_none(email=user_data.email)
    except Exception:
        logger.exception("Сбой чтения пользователя из БД: email=%s", user_data.email)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Не удалось получить пользователя")

    is_valid = False
    if user:
        is_valid = verify_password(user_data.old_password, user.password)
    else:
        verify_password(
            user_data.old_password,
            "$2b$12$q6VtHKLMERC2AkoXOFJ1eubTxllYp/dxUsR3coNAhhQYg.121Fqbi"
        )
    logger.debug("Проверка совпадения паролей: email=%s status=%s", user_data.email, is_valid)

    if not is_valid:
        logger.warning("Пароль пользователя не совпадает: email=%s", user_data.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный текущий пароль"
        )

    try:
        await UsersDAO.update(
            filter_by={"email": user_data.email},
            password=get_password_hash(user_data.new_password1)
        )
    except Exception:
        logger.exception("Ошибка при изменении пароля пользователя: email=%s", user_data.email)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось изменить пароль пользователя"
        )

    logger.info("Пароль пользователя успешно изменен: email=%s", user_data.email)
    return {
        "message": "Пароль успешно изменён"
    }

@router.get('/me', status_code=status.HTTP_200_OK)
async def get_me(request: Request) -> dict:
    user_id = request.state.user_id
    logger.debug("Информация о пользователе: запрос user_id=%s", user_id)

    try:
        user = await UsersDAO.find_one_or_none(id=user_id)
    except Exception:
        logger.exception("Сбой чтения пользователя из БД: user_id=%s", user_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Не удалось получить пользователя")

    if not user:
        logger.warning("Пользователь не найден: user_id=%s", user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )

    logger.info("Информация успешно получена о пользователе: user_id=%s", user_id)
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "is_admin": user.is_admin
    }