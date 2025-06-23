from datetime import timedelta, datetime, timezone
from os import environ

import jwt
from dotenv import load_dotenv
from jwt import ExpiredSignatureError, InvalidTokenError

from passlib.context import CryptContext

from app.utilities.exceptions import TOKEN_EXPIRE_EXCEPTION, CREDENTIALS_EXCEPTION

load_dotenv()

SECRET_KEY = environ["SECRET_KEY"]
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def encode_token(data: dict, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload

    except ExpiredSignatureError:
        raise TOKEN_EXPIRE_EXCEPTION

    except InvalidTokenError:
        raise CREDENTIALS_EXCEPTION
