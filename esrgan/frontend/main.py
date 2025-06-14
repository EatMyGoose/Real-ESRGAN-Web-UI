from typing import Optional, List, Callable
from fastapi import FastAPI
from nicegui import ui, events, app
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

class State:
    @staticmethod
    def __storage_backend():
        return app.storage.tab

    @staticmethod
    def upscale_request() -> UpscaleRequest:
        if not "upscale_request" in State.__storage_backend():
            State.__storage_backend()["upscale_request"] = UpscaleRequest()

        return State.__storage_backend()["upscale_request"]

    @staticmethod
    def results() -> List[UpscaledImage]:
        if not "upscale_results" in State.__storage_backend():
            State.__storage_backend()["upscale_results"] = []

        return State.__storage_backend()["upscale_results"]

async def handle_upscale_image(e: events.ClickEventArguments) -> None:
    logger.debug("Starting event handler")
    settings = State.upscale_request()
    params = SingleImageUpscaleRequest(
        model_name=settings.model,
        denoise_strength=settings.denoise_strength,
        outscale=settings.outscale_to_int(),
        face_enhance=settings.face_enhance
    )
    upscaled_image = UpscaledImage(
        UpscaleRequest(settings.image, settings.outscale, settings.model, settings.face_enhance, settings.denoise_strength)
    )
    State.results().append(upscaled_image)
    done_list.refresh()

    ui.notify(f"'{settings.image.name}' started")
    start = perf_counter()
    logger.debug("Start of upload")
    try:
        upscaled_image_bytes = await post_image(settings.image.data, settings.image.name, settings.image.type, params)
        logger.debug("End of upload")
        upscaled_image.result = Image(upscaled_image_bytes, settings.image.name, settings.image.type)
        end = perf_counter()
        ui.notify(f"'{settings.image.name}' upscaled")
        upscaled_image.time_taken = end - start
    except Exception as e:
        upscaled_image.error = str(e)
        ui.notify(f"{settings.image.name} failed, details = {e}")
    finally:
        done_list.refresh()

def delete_upscaled_image(to_delete: UpscaledImage) -> None:
    State.results().remove(to_delete)
    done_list.refresh()

def delete_all_upscaled_images() -> None:
    State.results().clear()
    done_list.refresh()

def settings_tooltip(settings: UpscaleRequest) -> None:
    with ui.icon("settings", size="sm"):
        with ui.tooltip():
            with ui.grid(columns=2).classes("gap-0"):
                ui.label("Model:")
                ui.label(settings.model)

                ui.label("Outscale:")
                ui.label(settings.outscale)

                ui.label("Face Enhance:")
                ui.label(str(settings.face_enhance))

                ui.label("Denoise Strength:")
                ui.label(settings.denoise_strength)

def output_image(upscaled: UpscaledImage) -> None:
    with ui.card().tight().classes("w-full"):
        if(upscaled.result):
            pil_image = get_pil_image(upscaled.result.data)
            ui.image(pil_image)
            with ui.card_section():
                with ui.row(align_items="center").classes("flex content-between"):
                    ui.label(f"Filename: {upscaled.result.name}")
                    ui.label(f"Processing Time: {upscaled.time_taken:.1f}s")
                    ui.button("Download", on_click=lambda : ui.download.content(upscaled.result.data, upscaled.result.name, upscaled.result.type))
                    ui.button("Delete", on_click=lambda x: delete_upscaled_image(upscaled))
                    settings_tooltip(upscaled.params)
        elif(upscaled.error):
            with ui.card_section():
                with ui.row():
                    ui.label("Error:")
                    ui.label(upscaled.error)
                    ui.button("Delete", on_click=lambda x: delete_upscaled_image(upscaled))
                    settings_tooltip(upscaled.params)
        else:
            ui.skeleton().classes("w-full h-[30em]")
            with ui.card_section():
                with ui.row():
                    ui.label(f"{upscaled.params.image.name}")
                    settings_tooltip(upscaled.params)

def handle_upload(e: events.UploadEventArguments) -> None:
    image_bytes =  e.content.read()
    State.upscale_request().image = Image(image_bytes, e.name, e.type)
    image_upload.refresh(State.upscale_request().image)

@ui.refreshable
def image_upload(current_image: Optional[Image]) -> None:
    with ui.column().classes('w-full gap-2 h-full flex flex-col'):
        if current_image is not None:
            ui.image(get_pil_image(current_image.data)).classes("w-full grow")
        else:
            with ui.card().classes("w-full flex items-center justify-center grow"):
                ui.label('No Image Selected')
        with ui.row().classes('w-full h-[3.5em] overflow-hidden rounded-xl'):
            ui.upload(on_upload=handle_upload, label="Source Image", auto_upload=True, max_files=1).props('accept=.jpg,.jpeg,.png').classes("w-full")

@ui.refreshable
def done_list() -> None:
    for item in State.results():
        output_image(item)

@ui.page("/")
async def main_page() -> None:
    await ui.context.client.connected()
    with ui.header().classes("flex flex-row items-center py-[0.75em] px-[4em]"):
        with ui.row().classes("w-2xl"):
            ui.label("Real-ESRGAN Web UI").classes("text-xl")
            ui.icon("zoom_out_map", size="2em")

    settings = State.upscale_request()
    with ui.column(align_items="center").classes("w-full"):
        with ui.card().classes("min-w-[40em] w-[50vw]"):
            with ui.row().classes("w-full items-stretch"):
                with ui.column().classes("grow"):
                    image_upload(settings.image)

                with ui.column().classes("grow"):
                    ui.select(model_list, label="Upscaling Model").bind_value(settings, "model").classes("w-full")
                    ui.select(["4x", "2x", "1x"], label="Outscale", value="4x").bind_value(settings, "outscale").classes("w-full")
                    with ui.row(align_items="center").classes("w-full"):
                        ui.label().bind_text_from(State.upscale_request(), "denoise_strength", lambda val: f"Denoise Strength [{val:.2f}]:")
                        with ui.row().classes("grow"):
                            ui.slider(min=0, max=1.0, step=0.05).bind_value(settings, "denoise_strength")

                    ui.checkbox(text="Face Enhancement", value=False).bind_value(settings, "face_enhance").classes("w-full mx-0")

                    ui.button("Upscale", on_click=handle_upscale_image).bind_enabled_from(settings, "image",  lambda img : img is not None).classes("w-full")

        with ui.card().classes("min-w-[40em] w-[50vw]"):
            ui.button("Delete all", icon="delete", on_click=lambda x: delete_all_upscaled_images()).classes("w-full")
            done_list()

def init_frontend(app: FastAPI) -> None:
    logger.info("Attaching UI")
    ui.run_with(
        app=app,
        title="Real-ESRGANs UI",
    )
