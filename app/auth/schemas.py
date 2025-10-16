from pydantic import BaseModel, EmailStr, Field

class AuthUser(BaseModel):
    email: EmailStr = Field(..., description="Почта пользователя")
    password: str = Field(..., description="Пароль пользователя")