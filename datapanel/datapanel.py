from re import split
from subprocess import Popen, PIPE

import redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse

from pyprocessor import Proc

app = FastAPI()

SAFE_LIST = ["pm2", "redis", "postgres", "uvicorn", "rabbit", "celery", "npm", "nginx"]
CELERY_TASK = "celery-task-meta"
FIVE_MINUTES = 300
origins = [
    "http://139.162.225.136",
    "http://langedev.net:80",
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


def get_proc_list():
    # return a list [] of proc objects representing the active process list
    proc_list = []
    sub_proc = Popen(['ps', 'aux'], shell=False, stdout=PIPE)
    # Discard the first line (ps aux header)
    sub_proc.stdout.readline()
    for line in sub_proc.stdout:
        # the separator for splitting is 'variable number of spaces'
        proc_info = split(" +", str(line), 10)
        proc_list.append(Proc(proc_info))
    return proc_list


def filter_proc(proc_list, key):
    return [proc for proc in proc_list if key in proc.cmd]


@app.get("/api/datapanel")
async def root():
    return {"message": "Hello World"}


@app.get("/api/datapanel/services/{name}")
async def query_service(name: str):
    if name not in SAFE_LIST:
        content = "you think too much"
        return HTMLResponse(content=content, status_code=404)
    services = filter_proc(get_proc_list(), name)
    # show the nominal proc list
    return {"name": name, "services": [service.to_str() for service in services]}


@app.get("/api/datapanel/rediskeys")
async def get_redis_keys():
    r = redis.Redis();
    keys = []
    ttls = []
    for key in r.scan_iter():
        ttl = r.ttl(key)
        if ttl == -1:
            r.delete(key)
            continue
        if CELERY_TASK in str(key):
            if ttl > FIVE_MINUTES:
                ttl = FIVE_MINUTES
                r.set(key, "foo", ex=FIVE_MINUTES)
        keys.append(key)
        ttls.append(ttl)
    return {'keys': keys, 'ttls': ttls}
