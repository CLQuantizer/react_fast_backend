from celery import Celery
import requests

app = Celery("tasks", backend="redis://localhost", broker="pyamqp://localhost")


@app.task
def get_definition(word):
    print(word)
    url = "https://api.dictionaryapi.dev/api/v2/entries/en/"+word
    definition = requests.get(url).json()
    return definition
