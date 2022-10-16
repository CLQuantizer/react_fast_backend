from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from users.router import userRouter
import redis
import logging

app = FastAPI()
app.include_router(userRouter, tags=["User"], prefix="/users")

r = redis.Redis(host="localhost")

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler_format = logging.Formatter("%(levelname)s:\t  %(name)s -  %(message)s")
console_handler.setFormatter(console_handler_format)
logger.addHandler(console_handler)

origins = [
    "http://139.162.225.136",
    "http://langedev.net",
    "http://langedev.net:3000",
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:80",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def read_main():
    return {"msg": "Hello World\n"}
