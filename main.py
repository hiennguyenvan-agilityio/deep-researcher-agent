import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import load_env_file
from app.api.v1.main import api_router

load_env_file()

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Chat-Session-Id"],
)

api_v1_str = os.getenv("API_V1_STR", "/api/v1")

app.include_router(api_router, prefix=api_v1_str, tags=["v1"])
