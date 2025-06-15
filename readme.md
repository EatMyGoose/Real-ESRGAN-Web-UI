## About

A simple browser-based UI for [Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN) (an AI image upscaling tool),
packaged as a dockerized project to simplify installation.

![image](./docs/preview.png)

## Installation

### Prerequisites
- Ensure *Docker Desktop* is installed

### Launching the application
- Clone the project
- Navigate into the project directory
- Start the application via `docker compose up`
  - This launches the application on http://localhost
- `Ctrl+C` or `docker compose down` to stop the application

## Misc
- A REST endpoint for the upscaling backend is exposed at `[POST] /upscale`, refer to the *Swagger* page at `/docs` for more details

## Remarks:
* Video upscaling is not supported
* GPU acceleration is not enabled

## Disclaimer
This project is unaffiliated with [Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN) (license file titled *REALESRGAN-LICENSE*)


