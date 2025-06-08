from pydantic import BaseModel

class SingleImageUpscaleRequest(BaseModel):
    model_name: str
    denoise_strength: float
    outscale: int
    face_enhance: bool