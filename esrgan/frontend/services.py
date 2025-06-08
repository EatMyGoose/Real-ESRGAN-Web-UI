import httpx
from httpx import Response
from loguru import logger
from frontend.schemas import SingleImageUpscaleRequest

def get_upscaler_url(path: str) -> str:
    return f"http://localhost:8000{path}"

def post_image(
    file_contents: bytes,
    filename: str,
    filetype: str,
    params: SingleImageUpscaleRequest
) -> bytes:
    assert filename is not None
    logger.info("Entering post_image")

    logger.info("Before post")
    with httpx.Client() as client:
        resp: Response = client.post(
            get_upscaler_url("/upscale"),
            data=params.model_dump(),
            files=[('file', (filename, file_contents, filetype))],
            timeout=None
        )
        logger.info(f"After response, code={resp.status_code}")
        resp.raise_for_status()
        return resp.content
