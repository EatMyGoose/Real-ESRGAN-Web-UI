from fastapi import FastAPI
from infer import infer
from typing_extensions import Annotated
from typing import Optional
from fastapi import FastAPI, File, Form, UploadFile, Response
import schemas
from pathlib import Path
from urllib.parse import quote

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

    result_bytes = infer(
        image_extension=file_ext,
        image_bytes=file_bytes,
        model_name=model_name,
        denoise_strength=denoise_strength,
        outscale=outscale,
        tile=tile,
        tile_pad=tile_pad,
        pre_pad=pre_pad,
        face_enhance=face_enhance,
        fp_32=fp_32,
        gpu_id=gpu_id
    )

    return Response(
        result_bytes,
        media_type="application/octet",
        headers={
            "Content-Disposition": f"attachment; filename=\"{'upscaled' + file_ext}\";filename*=UTF-8''{quote(file.filename)}"
        }
    )
