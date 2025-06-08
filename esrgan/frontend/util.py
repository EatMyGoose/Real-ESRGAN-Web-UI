from functools import lru_cache
from PIL import Image
from io import BytesIO

@lru_cache(maxsize=64)
def get_pil_image(image_bytes: bytes) -> Image:
    pil_image = Image.open(BytesIO(image_bytes))
    return pil_image