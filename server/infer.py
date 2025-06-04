from typing import Optional, Union

from realesrgan import RealESRGANer
from util import model_params, get_model_path, get_dni_weights, make_model, make_face_enhancement_model, omit
from loguru import logger
import cv2
import numpy as np

import schemas

def infer(
    image_extension: str, # includes the dot
    image_bytes: bytes,
    model_name: schemas.TModelNames,
    denoise_strength: float = 0.5, # only used for realesr-general-x4v3
    outscale: int = 4,
    tile: int = 0,
    tile_pad:int = 10,
    pre_pad:int = 0,
    face_enhance:bool = False,
    fp_32: bool = True,
    gpu_id: Optional[int] = None
) -> bytes:
    logger.info(f"[Inference], params='{omit(locals(), ['image_bytes'])}'")

    params = model_params[model_name].root
    logger.info(f"Using model '{model_name}', params='{params.model_dump_json()}'")

    model_path = get_model_path(model_name)

    model = make_model(model_name)

    # Convert image to OpenCV buffer
    image_np = np.frombuffer(image_bytes, np.uint8)
    cv_image = cv2.imdecode(image_np, cv2.IMREAD_UNCHANGED)

    # restorer
    upsampler = RealESRGANer(
        scale=params.params.get_scale(),
        model_path=model_path,
        dni_weight=get_dni_weights(model_name, denoise_strength),
        model=model,
        tile=tile,
        tile_pad=tile_pad,
        pre_pad=pre_pad,
        half=(fp_32 == False),
        gpu_id=gpu_id
    )

    # Infer
    cv_output: Union[None | np.ndarray] = None
    if face_enhance:
        logger.debug(f"Upscaling using face-enhancer, outscale='{outscale}'")
        face_enhancer = make_face_enhancement_model(upsampler, outscale)
        _,_, cv_output =face_enhancer.enhance(cv_image, has_aligned=False, only_center_face=False, paste_back=True)
    else:
        logger.debug(f"Upscaling without face-enhancer, outscale='{outscale}'")
        cv_output, _ = upsampler.enhance(cv_image, outscale=outscale)

    logger.debug(f"Decoding cv image back to bytes")
    # Convert back to bytes
    image_bytes: bytes = cv2.imencode(image_extension, cv_output)[1].tobytes()
    return image_bytes