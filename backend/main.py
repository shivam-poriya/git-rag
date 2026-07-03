from fastapi import FastAPI, Request
import uvicorn

from importlib import import_module
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Add the origin of your frontend application
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

SETTINGS_MODULES = {
    "development": "config.settings.development",
    "production": "config.settings.production",
}
environment = "development"

settings_module = SETTINGS_MODULES.get(environment, "config.settings.development")

settings = import_module(settings_module)
from config.urls import urls_router

app.include_router(urls_router)


def main():
    print(
        f"-----------------You are running with {environment} environment-------------------------"
    )
    uvicorn.run(app, host=settings.host, port=int(settings.port))


if __name__ == "__main__":
    main()
