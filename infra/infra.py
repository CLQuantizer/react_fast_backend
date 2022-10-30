import logging

import redis
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from tasks import get_definition

infra = FastAPI()
r = redis.Redis()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler_format = logging.Formatter("%(levelname)s:\t  %(name)s -  %(message)s")
console_handler.setFormatter(console_handler_format)
logger.addHandler(console_handler)

origins = [
    "http://139.162.225.136",
    "http://langedev.net:80",
    "http://langedev.net",
    "http://langedev.net:3000",
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:80",
]

infra.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@infra.get("/definition/{word}")
async def definition(word):
    celery_async_result = get_definition.delay(word)
    res = celery_async_result.get()
    logger.info(res[0]['meanings'][1]['synonyms'])
    syns = []
    for meaning in res[0]['meanings']:
        for each in meaning['synonyms']:
            syns.append(each)
    return sorted(syns, key=len)
