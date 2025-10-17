from idlelib.debugobj_r import remote_object_tree_item

from fastapi import FastAPI
from app.middleware.auth import AuthMiddleware

from app.api.users import router as users_router
from app.api.auth import router as auth_router

app = FastAPI()

app.add_middleware(AuthMiddleware)

app.include_router(users_router)
app.include_router(auth_router)