from fastapi.testclient import TestClient
from .main import app

client = TestClient(app)

MAGIC_NAME = "ez"
MAGIC_WORD = "go"
JOURNAL = {"title": "test", "date": "test", "body": "test"}
ANOTHER_JOURNAL = {"title": "test2", "date": "test", "body": "test"}
UPDATE_JOURNAL = {"title": "test", "date": "new", "body": "new"}


def test_create_user():
    response = client.post(
        '/users/',
        json={"username": MAGIC_NAME, 'password': MAGIC_WORD},
    )
    assert response.json()['username'] == MAGIC_NAME


def test_jwt_login() -> str:
    response = client.post(
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        url="/users/token/",
        data=f"grant_type=&username={MAGIC_NAME}&password={MAGIC_WORD}&scope=&client_id=&client_secret="
    )
    assert response.json()['token_type'] == 'bearer'
    assert response.status_code == 200
    return f"Bearer {response.json()['access_token']}"


def test_me_access():
    token = test_jwt_login()
    response = client.get(
        "/users/read/me/",
        headers={"Authorization": token},
    )
    assert response.json()['username'] == MAGIC_NAME


def test_add_new_journal_for_user():
    token = test_jwt_login()
    response = client.post(
        "/users/write/journals/",
        json=JOURNAL,
        headers={"Authorization": token},
    )
    assert response.json()['title'] == JOURNAL['title']


def test_another_new_journal_for_user():
    token = test_jwt_login()
    response = client.post(
        "/users/write/journals/",
        json=ANOTHER_JOURNAL,
        headers={"Authorization": token},
    )
    assert response.json()['title'] == ANOTHER_JOURNAL['title']


# get journal must be between add new and delete
def test_get_journals():
    token = test_jwt_login()
    response = client.get(
        "/users/read/journals/",
        headers={"Authorization": token},
    )
    assert response.status_code == 200
    for each in response.json():
        assert len(each) == 5


def test_update_journal():
    token = test_jwt_login()
    response = client.put(
        "/users/write/journals/",
        json=UPDATE_JOURNAL,
        headers={"Authorization": token},
    )
    assert response.status_code == 200
    assert response.json()['body'] == 'new'


def test_remove_journal_by_title():
    token = test_jwt_login()
    response = client.delete(
        "/users/write/journals/",
        json=JOURNAL,
        headers={"Authorization": token},
    )
    assert response.status_code == 200
    assert response.json()['title'] == JOURNAL['title']


def test_remove_another_journal_by_title():
    token = test_jwt_login()
    response = client.delete(
        "/users/write/journals/",
        json=ANOTHER_JOURNAL,
        headers={"Authorization": token},
    )
    assert response.status_code == 200
    assert response.json()['title'] == ANOTHER_JOURNAL['title']


def test_delete_user():
    token = test_jwt_login()
    response = client.delete(
        '/users/write/',
        json={"username": MAGIC_NAME},
        headers={"Authorization": token},
    )
    assert response.json()['username'] == MAGIC_NAME


def test_read_all_journals():
    response = client.get("/users/read/alljournals/")
    assert response.status_code == 200
    for journal in response.json():
        assert len(journal) == 4


def test_():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"msg": "Hello World"}
