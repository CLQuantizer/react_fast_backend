import gensim.downloader
import pickle
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import redis
import json
import logging

glove_app = FastAPI()
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
    "http://langedev.net",
    "http://langedev.net:3000",
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:80",
]

glove_app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# glove_vectors = gensim.downloader.load('glove-wiki-gigaword-50')

# with open('glove50','wb') as f:
#     pickle.dump(glove_vectors,f)
with open('glove50', 'rb') as f:
    glove_vectors = pickle.load(f)


@glove_app.get("/related/{Word}")
async def related(Word):
    # read the word
    word = Word.lower().strip()
    # query redis
    redis_res = await r.get(word)
    if redis_res:
        logger.info("going through redis")
        return json.loads(redis_res)
    else:
        logger.info("going through memory")
        if word in glove_vectors.key_to_index:
            wordsnprobs = glove_vectors.most_similar(word, topn=15)
            words = [pair[0] for pair in wordsnprobs]
            probs = [round(pair[1], 2) for pair in wordsnprobs]
        else:
            words = ['Sorry 🥵', 'This input', 'is not a word']
            probs = ['', '\'' + Word + '\'', 'or is too rare for this little app']
            # set the redis entry
        await r.set(word, json.dumps({'words': words, 'probs': probs}))
        return {'words': words, 'probs': probs}


@glove_app.get("/related/")
async def related():
    words = ['Sorry 🥵', 'Please input']
    probs = ['', 'something']
    return {'words': words, 'probs': probs}
