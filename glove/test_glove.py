from fastapi.testclient import TestClient
from .glove import glove_app

client = TestClient(glove_app)

MAGIC_NAME = "ez"
MAGIC_WORD = "go"
JOURNAL = {"title": "test", "date": "test", "body": "test"}
ANOTHER_JOURNAL = {"title": "test2", "date": "test", "body": "test"}
UPDATE_JOURNAL = {"title": "test", "date": "new", "body": "new"}


def test_related_go():
    response = client.get('/related/' + 'hong')
    assert response.json()['words'][0] == 'kong'

def test_related_hong():
    response = client.get('/related/' + MAGIC_WORD)
    assert response.json()['words'][0] == 'going'
