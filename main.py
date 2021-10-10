import logging
from fastapi import FastAPI, Request

from src.routes import router
from starlette.routing import Match

logger = logging.getLogger(__name__)

app = FastAPI()


app.include_router(router)
