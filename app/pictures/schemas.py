from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class PictureCreate(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=500, description="Описание изображения")
    num_inference_steps: int = Field(default=15, ge=10, le=50,
                                     description="Количество шагов генерации (больше = качественнее, но дольше)")
    guidance_scale: float = Field(default=8.0, ge=1.0, le=20.0, description="Сила следования промпту")


class PictureCreateResponse(BaseModel):
    success: bool
    message: str
    task_id: str
    status: TaskStatus

class PictureStatusResponse(BaseModel):
    task_id: str
    status: TaskStatus
    message: str
    download_url: Optional[str] = None
    error: Optional[str] = None
    created_at: Optional[int] = None

class TaskInfo(BaseModel):
    task_id: str
    user_id: int
    prompt: str
    status: TaskStatus
    filename: Optional[str] = None
    filepath: Optional[str] = None
    error: Optional[str] = None
    created_at: int
    num_inference_steps: int = 15
    guidance_scale: float = 8.0