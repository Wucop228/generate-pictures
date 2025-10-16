

from pydantic import BaseModel, EmailStr, Field, model_validator, field_validator

class UserRegister(BaseModel):
    email: EmailStr = Field(..., description="Электронная почта")
    password: str = Field(..., min_length=6, max_length=32, description="Пароль от 6 до 32 символов")
    username: str = Field(..., min_length=5, max_length=25, description="Юзернейм от 5 до 25 символов")

class UserPassword(BaseModel):
    email: EmailStr = Field(..., description="Электронная почта")
    old_password: str = Field(..., description="Старый пароль")
    new_password1: str = Field(..., description="Новый пароль первый")
    new_password2: str = Field(..., description="Новый пароль второй")

    @model_validator(mode="after")
    def passwords_match(self):
        if self.new_password1 != self.new_password2:
            raise ValueError("Новые пароли должны совпадать")
        return self

    @field_validator("new_password1")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) > 32:
            raise ValueError("Пароль должен содержать мксимум 32 символа")
        if len(value) < 6:
            raise ValueError("Пароль должен содержать минимум 6 символов")
        return value