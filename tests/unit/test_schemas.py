import pytest
from pydantic import ValidationError
from app.pictures.schemas import PictureCreate

pytestmark = pytest.mark.unit

def test_picture_create_validation():
    PictureCreate(prompt="ok", num_inference_steps=15, guidance_scale=8.0)
    with pytest.raises(ValidationError):
        PictureCreate(prompt="", num_inference_steps=15, guidance_scale=8.0)
    with pytest.raises(ValidationError):
        PictureCreate(prompt="x", num_inference_steps=5, guidance_scale=8.0)
    with pytest.raises(ValidationError):
        PictureCreate(prompt="x", num_inference_steps=15, guidance_scale=50.0)