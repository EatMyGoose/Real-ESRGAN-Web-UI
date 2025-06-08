from fastapi import FastAPI
from typing_extensions import Annotated
from typing import Optional
from fastapi import FastAPI, File, Form, UploadFile, Response
from pathlib import Path
from urllib.parse import quote
from concurrent.futures import ProcessPoolExecutor
import asyncio

from server import schemas
from server.infer import infer
from frontend.main import init_frontend

pool = ProcessPoolExecutor(max_workers=2)

app = FastAPI()

@app.get("/health")
async def heatlh_check():
    return {"status": "healthy"}

@app.post("/upscale")
async def root(
    file: Annotated[UploadFile, File()],
    model_name: Annotated[schemas.TModelNames, Form()] = 0.5,
    denoise_strength: Annotated[float, Form()] = 4,
    outscale: Annotated[int, Form()] = 4,
    tile: Annotated[int, Form()] = 0,
    tile_pad: Annotated[int, Form()] = 10,
    pre_pad: Annotated[int, Form()] = 0,
    face_enhance: Annotated[bool, Form()] = False,
    fp_32: Annotated[bool, Form()] = True,
    gpu_id: Annotated[Optional[int], Form()] = None
):
    file_ext: str = Path(file.filename).suffix.lower()
    file_bytes: bytes = await file.read()

    loop = asyncio.get_running_loop()
    result_bytes = await loop.run_in_executor(pool,
        infer,
        file_ext,
        file_bytes,
        model_name,
        denoise_strength,
        outscale,
        tile,
        tile_pad,
        pre_pad,
        face_enhance,
        fp_32,
        gpu_id
    )

    return Response(
        result_bytes,
        media_type="application/octet",
        headers={
            "Content-Disposition": f"attachment; filename=\"{'upscaled' + file_ext}\";filename*=UTF-8''{quote(file.filename)}"
        }
    )

init_frontend(app)