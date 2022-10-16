from typing import Union
from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
    SecurityScopes,
)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from pydantic import ValidationError
from datetime import datetime, timedelta
from passlib.context import CryptContext

from . import models, schemas
from .database import (
    create_user,
    create_user_journal,
    delete_journal_by_title,
    delete_user_by_username,
    engine,
    get_journals,
    get_journal_by_title,
    get_user_journals,
    get_user_by_username,
    update_journal,
    SessionLocal,
)

# router config
userRouter = APIRouter()

# db config 
models.Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Auth config
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/users/token/",
    scopes={"read": "Read access", "write": "Write access", 'me': 'Me access'},
)

# jwt settings
# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def authenticate_user(username: str, password: str, db: Session = Depends(get_db)):
    user = get_user_by_username(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(security_scopes: SecurityScopes, token: str = Depends(oauth2_scheme),
                           db: Session = Depends(get_db)):
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope = {security_scopes.scope_str}'
    else:
        authenticate_value = f'Bearer'
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_scopes = payload.get("scopes", [])
        token_data = schemas.TokenData(scopes=token_scopes, username=username)
    except (JWTError, ValidationError):
        raise credentials_exception
    user = get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": authenticate_value},
            )
    return schemas.UserBase(username=user.username)


# user routes
@userRouter.post("/token/", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "scopes": form_data.scopes}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@userRouter.post("/", response_model=schemas.User)
async def add_a_new_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    new_user = get_user_by_username(db, username=user.username)
    if new_user:
        raise HTTPException(status_code=400, detail="username already registered")
    return create_user(db=db, user=user)


@userRouter.get("/read/me/")
async def read_users_me(current_user: schemas.UserBase = Depends(get_current_user)):
    return current_user


@userRouter.get("/read/alljournals/", response_model=list[schemas.JournalWithAuthor],
                response_description="get all journals")
async def read_all_journals(db: Session = Depends(get_db)):
    journals = get_journals(db, skip=0, limit=100)
    journal_with_author_list = []
    for journal in journals:
        new_journal = schemas.JournalWithAuthor(
            title=journal.title,
            body=journal.body,
            date=journal.date,
            author=journal.author.username
        )
        journal_with_author_list.append(new_journal)
    return journal_with_author_list


@userRouter.get("/read/journals/", response_model=list[schemas.Journal],
                response_description="All journals data for a user")
async def read_journals_of_a_user(user: schemas.UserBase = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_user_journals(db=db, username=user.username)


@userRouter.delete("/write/", response_model=schemas.User, response_description="Single user data deleted")
async def delete_a_user_data(user: schemas.UserBase = Depends(get_current_user), db: Session = Depends(get_db)):
    old_user = get_user_by_username(db, username=user.username)
    if old_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    journals_of_old_user = get_user_journals(db, username=user.username)
    if len(journals_of_old_user) > 0:
        raise HTTPException(status_code=400, detail="You have journals, delete those first")
    return delete_user_by_username(db=db, user=user)


@userRouter.post("/write/journals/", response_model=schemas.Journal, response_description="create a journal for a user")
async def add_new_journal_for_a_user(journal: schemas.JournalCreate, user: schemas.UserBase = Depends(get_current_user),
                                     db: Session = Depends(get_db)):
    return create_user_journal(db=db, journal=journal, user=user)


@userRouter.put("/write/journals/", response_model=schemas.JournalUpdate,
                response_description="One journal data updated")
async def update_a_journal_of_a_user(journal: schemas.JournalUpdate, user: schemas.UserBase = Depends(get_current_user),
                                     db: Session = Depends(get_db)):
    user = get_user_by_username(db=db, username=user.username)
    old_journal = get_journal_by_title(db=db, title=journal.title)
    if old_journal is None:
        raise HTTPException(status_code=404, detail="Journal not found")
    if old_journal.author_id != user.id:
        raise HTTPException(status_code=400, detail="You can't change journal of other user")
    return update_journal(db=db, journal=journal)


@userRouter.delete("/write/journals/", response_model=schemas.Journal,
                   response_description="delete a journal for a user")
async def remove_a_journal_by_its_title(journal: schemas.JournalBase,
                                        user: schemas.UserBase = Depends(get_current_user),
                                        db: Session = Depends(get_db)):
    user_in_db = get_user_by_username(db=db, username=user.username)
    old_journal = get_journal_by_title(db=db, title=journal.title)
    if old_journal is None:
        raise HTTPException(status_code=404, detail="Journal not found")
    if old_journal.author_id != user_in_db.id:
        raise HTTPException(status_code=400, detail="You can't delete journal of other user")
    return delete_journal_by_title(db=db, title=journal.title)
