FROM python:3.8-bookworm AS dev

RUN apt-get update && apt-get install ffmpeg libsm6 libxext6 -y

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    pip install uv && uv sync

COPY . .

EXPOSE 8000

WORKDIR /app/esrgan

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port",  "8000", "--reload"]

FROM dev AS prod

CMD ["uv", "run", "fastapi", "run", "main.py"]