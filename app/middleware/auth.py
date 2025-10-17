from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from jose import JWTError, ExpiredSignatureError

from app.auth.utils import validate_access_token

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.user_id = None
        request.state.is_authenticated = False

        protected_prefixes = [
            "/users/me"
        ]
        public_prefixes = [
            "/docs",
            "/openapi.json",
            "/redoc"
        ]
        public_exact_paths = [
            ...
        ]

        path = request.url.path
        is_public_prefix = any(path.startswith(p) for p in public_prefixes)
        is_public_exact = path in public_exact_paths
        is_public = is_public_prefix or is_public_exact

        is_protected = any(path.startswith(p) for p in protected_prefixes)

        if is_protected and not is_public:
            access_token = request.cookies.get("access_token")

            if not access_token:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content = {"detail": "Не авторизован"}
                )

            try:
                payload = validate_access_token(access_token)
                user_id = int(payload["user_id"])

                request.state.user_id = user_id
                request.state.is_authenticated = True
            except HTTPException as e:
                return JSONResponse(
                    status_code=e.status_code,
                    content={"detail": e.detail}
                )
            except ExpiredSignatureError:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Токен истек"}
                )
            except JWTError as e:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content = {"detail": f"Невалидный токен: {str(e)}"}
                )
            except ValueError:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content = {"detail": "Некорректный формат токена"}
                )

        response = await call_next(request)
        return response