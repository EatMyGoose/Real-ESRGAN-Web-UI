from pathlib import Path
from schemas import Model, ModelList, TModelNames, TFaceEnhancementModel
from typing import Dict, List, Union, Set, Any
from loguru import logger
from torch.hub import download_url_to_file

from basicsr.archs.rrdbnet_arch import RRDBNet
from realesrgan.archs.srvgg_arch import SRVGGNetCompact
from gfpgan import GFPGANer
from realesrgan import RealESRGANer
from pathlib import Path

def omit(values : Dict[str, Any], omitted: List[str]) -> Dict[str, Any]:
    copy = values.copy()
    for key_to_remove in omitted:
        copy.pop(key_to_remove, None)
    return copy

def __load_model_params() -> Dict[str, Model]:

    data_file_path: str = f"{Path(__file__).parent.parent}/config/params.json"
    logger.info(f"Loading params from '{data_file_path}'")
    with open(data_file_path, "r") as hFile:
        models = ModelList.model_validate_json(hFile.read())
        return {
            model.root.name : model for model in models.root
        }

model_params: Dict[str, Model] = __load_model_params()

def get_model_path(name: Union[TModelNames, TFaceEnhancementModel]) -> Union[str, List[str]]:
    urls: List[str] = model_params[name].root.urls
    # Get last slug of each URL
    filenames: List[str] = [url.split("/")[-1] for url in urls]
    filepaths: List[str] = [f"{Path(__file__).parent.parent}/weights/{filename}" for filename in filenames]

    for url, filepath in zip(urls, filepaths):
        if not Path(filepath).is_file():
            #download file
            logger.info(f"Downloading '{url}' to '{filepath}'")
            download_url_to_file(url, filepath)

    if len(filepaths) == 1:
        return filepaths[0]
    else:
        return filepaths

def get_dni_weights(model_name: TModelNames, denoise_strength: float) -> Union[None, List[float]]:
    if model_name == 'realesr-general-x4v3':
        return [denoise_strength, 1 - denoise_strength]
    else:
        return None

def make_face_enhancement_model(upsampler: RealESRGANer, upscale: int) -> GFPGANer:
    model_path = get_model_path("GFPGANv1.3")
    return GFPGANer(
        model_path=model_path,
        upscale=upscale,
        arch='clean',
        channel_multiplier=2,
        bg_upsampler=upsampler
    )

def make_model(model_name: TModelNames) -> Union[SRVGGNetCompact, RRDBNet]:
    params = model_params[model_name].root
    if params.type == "rrdbnet":
        return RRDBNet(**params.params.model_dump())
    elif params.type == "srvggnet":
        return SRVGGNetCompact(**params.params.model_dump())
    else:
        raise ValueError(f"{params.type} is an unrecognized model type")
