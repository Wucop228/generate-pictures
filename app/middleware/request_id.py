import logging
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from fastapi import Request

class RequestIdMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, header_name: str = "X-Request-ID"):
        super().__init__(app)
        self.header_name = header_name

    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get(self.header_name) or str(uuid.uuid4())
        request.state.request_id = req_id

        user_id = getattr(request.state, "user_id", None)

        logger = logging.getLogger("app.request")
        adapter = logging.LoggerAdapter(logger, extra={
            "request_id": req_id,
            "user_id": user_id if user_id is not None else "-"
        })
        adapter.info(f"{request.method} {request.url.path} started")

        response = await call_next(request)
        response.headers[self.header_name] = req_id
        adapter.info(f"{request.method} {request.url.path} finished {response.status_code}")
        return response