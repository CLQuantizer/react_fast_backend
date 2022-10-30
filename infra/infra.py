import json
import logging

import redis
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from tasks import get_definition

ERROR_MESSAGE = {'title': 'No Definitions Found',
                 'message': 'Sorry pal, we couldn\'t find definitions for the word you were looking for.',
                 'resolution': 'You can try the search again at later time or head to the web instead.'}

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


@infra.get("/synonyms/{word}")
async def synonyms(word):
    redis_key = "def:" + word
    redis_res = r.get(redis_key)
    if redis_res:
        logger.info("going through definition redis")
        return json.loads(redis_res)

    celery_async_res = get_definition.delay(word)
    celery_res = celery_async_res.get()
    if celery_res == ERROR_MESSAGE:
        r.set(redis_key, json.dumps(ERROR_MESSAGE['title']), ex=300)
        return ERROR_MESSAGE['title']

    logger.info(celery_res[0]['meanings'][0]['synonyms'])
    syns = []
    for meaning in celery_res[0]['meanings']:
        for each in meaning['synonyms']:
            syns.append(each)
    syns = syns[:15]
    r.set(redis_key, json.dumps(syns), ex=300)
    return sorted(syns, key=len)
