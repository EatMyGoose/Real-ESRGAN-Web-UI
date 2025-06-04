from typing import Literal, List, Union
from pydantic import BaseModel, RootModel

TModelNames = Literal[
    "RealESRGAN_x4plus",
    "RealESRNet_x4plus",
    "RealESRGAN_x4plus_anime_6B",
    "RealESRGAN_x2plus",
    "realesr-general-x4v3",
]

TFaceEnhancementModel = Literal["GFPGANv1.3"]

TAlphaUpsampler = Literal["realesrgan", "bicubic"]
TImageExtension = Literal["auto", "jpg", "png"]


class RRDBNetParams(BaseModel):
    num_in_ch: int
    num_out_ch: int
    num_feat: int
    num_block: int
    num_grow_ch: int
    scale: int

    def get_scale(self) -> int:
        return self.scale

class SRVGGNetCompactParams(BaseModel):
    num_in_ch: int
    num_out_ch: int
    num_feat: int
    num_conv: int
    upscale: int
    act_type: str

    def get_scale(self) -> int:
        return self.upscale

class FaceEnhancementModel(BaseModel):
    name: str
    type: Literal["face-enhance"]
    urls: List[str]

class RRDBNetModel(BaseModel):
    name: str
    type: Literal["rrdbnet"]
    urls: List[str]
    params: RRDBNetParams

class SRVGGNetModel(BaseModel):
    name: str
    type: Literal["srvggnet"]
    urls: List[str]
    params: SRVGGNetCompactParams

class Model(RootModel):
    root: Union[RRDBNetModel, SRVGGNetModel, FaceEnhancementModel]

class ModelList(RootModel):
    root: List[Model]

