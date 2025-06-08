from typing import Optional, List
from fastapi import FastAPI
from nicegui import ui, events
from nicegui.binding import bindable_dataclass
from dataclasses import dataclass
from loguru import logger
from time import perf_counter

from frontend.services import post_image
from frontend.schemas import SingleImageUpscaleRequest
from frontend.util import get_pil_image


model_list: List[str] = [
    "RealESRGAN_x4plus",
    "RealESRNet_x4plus",
    "RealESRGAN_x4plus_anime_6B",
    "RealESRGAN_x2plus",
    "realesr-general-x4v3"
]

@dataclass
class Image:
    data: bytes
    name: str
    type: str

@bindable_dataclass
class UpscaleRequest:
    image: Optional[Image] = None
    outscale: str = "4x"
    model: str = "RealESRGAN_x4plus"
    face_enhance: bool = False
    denoise_strength: float = 0.5

    def outscale_to_int(self) -> int:
        mapping = {
            "4x": 4,
            "2x": 2,
            "1x": 1
        }
        return mapping[self.outscale]

@dataclass
class UpscaledImage:
    params: UpscaleRequest
    time_taken: Optional[float] = None
    result: Optional[Image] = None
    error: Optional[str] = None

state = UpscaleRequest()
results: List[UpscaledImage] = []

def handle_upload(e: events.UploadEventArguments) -> None:
    image_bytes =  e.content.read()
    state.image = Image(image_bytes, e.name, e.type)

async def handle_upscale_image(e: events.ClickEventArguments) -> None:
    logger.debug("Starting event handler")
    params = SingleImageUpscaleRequest(
        model_name=state.model,
        denoise_strength=state.denoise_strength,
        outscale=state.outscale_to_int(),
        face_enhance=state.face_enhance
    )
    upscaled_image = UpscaledImage(
        UpscaleRequest(state.image, state.outscale, state.model, state.face_enhance, state.denoise_strength)
    )
    results.append(upscaled_image)
    done_list.refresh()

    ui.notify(f"'{state.image.name}' started")
    start = perf_counter()
    logger.debug("Start of upload")
    try:
        upscaled_image_bytes = await post_image(state.image.data, state.image.name, state.image.type, params)
        logger.debug("End of upload")
        upscaled_image.result = Image(upscaled_image_bytes, state.image.name, state.image.type)
        end = perf_counter()
        ui.notify(f"'{state.image.name}' upscaled")
        upscaled_image.time_taken = end - start
    except Exception as e:
        upscaled_image.error = str(e)
        ui.notify(f"{state.image.name} failed, details = {e}")
    finally:
        done_list.refresh()

def delete_upscaled_image(to_delete: UpscaledImage) -> None:
    results.remove(to_delete)
    done_list.refresh()

def delete_all_upscaled_images() -> None:
    results.clear()
    done_list.refresh()

def output_image(upscaled: UpscaledImage) -> None:
    if(upscaled.result):
        pil_image = get_pil_image(upscaled.result.data)
        ui.image(pil_image)
        ui.label(f"{upscaled.result.name}, {upscaled.time_taken}s")
        ui.button(upscaled.result.name, on_click=lambda : ui.download.content(upscaled.result.data, upscaled.result.name, upscaled.result.type))
        ui.button("Delete", on_click=lambda x: delete_upscaled_image(upscaled))
    elif(upscaled.error):
        ui.label("Error:")
        ui.label(upscaled.error)
        ui.button("Delete", on_click=lambda x: delete_upscaled_image(upscaled))
    else:
        ui.label(f"{upscaled.params.image.name}")
        ui.spinner()

@ui.refreshable
def done_list() -> None:
    for item in results:
        output_image(item)

@ui.page("/")
def main_page() -> None:
    ui.select(model_list, label="Upscaling Model").bind_value(state, "model")
    ui.select(["4x", "2x", "1x"], label="Outscale", value="4x").bind_value(state, "outscale")
    ui.label().bind_text_from(state, "denoise_strength", lambda val: f"Denoise Strength ({val:.2f})")
    ui.slider(min=0, max=1.0, step=0.05).bind_value(state, "denoise_strength")
    ui.checkbox(text="Face Enhancement", value=False).bind_value(state, "face_enhance")
    ui.upload(on_upload=handle_upload, label="Source Images", auto_upload=True, max_files=1).props('accept=.jpg,.jpeg,.png')
    ui.button("Upscale", on_click=handle_upscale_image).bind_enabled_from(state, "image",  lambda img : print(img) or img is not None)

    ui.button("Delete all", on_click=lambda x: delete_all_upscaled_images())
    done_list()


def init_frontend(app: FastAPI) -> None:
    logger.info("Attaching UI")
    ui.run_with(
        app=app,
        title="Real-ESRGANs UI",
    )