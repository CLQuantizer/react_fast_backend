from fastapi import FastAPI
import redis
import json

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


@app.get("/rediskeys")
async def get_redis_keys():
    r = redis.Redis();
    keys = {}
    for key in r.scan_iter():
        ttl = r.ttl(key)
        keys[key] = ttl
    return keys
