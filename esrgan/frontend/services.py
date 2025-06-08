import httpx
from httpx import Response
from loguru import logger
from frontend.schemas import SingleImageUpscaleRequest

def get_upscaler_url(path: str) -> str:
    return f"http://localhost:8000{path}"

async def post_image(
    file_contents: bytes,
    filename: str,
    filetype: str,
    params: SingleImageUpscaleRequest
) -> bytes:
    assert filename is not None
    logger.info(f"Submitting upscale request, params=<{params.model_dump_json()}>")

    async with httpx.AsyncClient(timeout=None) as client:
        resp: Response = await client.post(
            get_upscaler_url("/upscale"),
            data=params.model_dump(),
            files=[('file', (filename, file_contents, filetype))]
        )
        logger.info(f"After response, code={resp.status_code}")
        resp.raise_for_status()
        return resp.content
