import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_session
from models import User


load_dotenv(Path(__file__).with_name('.env'))

DEMO_USER_ID = 1
DEMO_USER_NAME = 'Demo User'
DEMO_USER_EMAIL = 'demo@example.com'
DEMO_USER_PASSWORD = 'demo123'
ACCESS_TOKEN_EXPIRE_HOURS = 24
JWT_ALGORITHM = 'HS256'

password_hash = PasswordHash.recommended()
bearer_scheme = HTTPBearer(auto_error=False)


def create_demo_user(session: Session) -> None:
    user = session.get(User, DEMO_USER_ID)

    if user is None:
        user = User(
            user_id=DEMO_USER_ID,
            name=DEMO_USER_NAME,
            email=DEMO_USER_EMAIL,
            password_hash=password_hash.hash(DEMO_USER_PASSWORD),
        )
        session.add(user)
        session.commit()
        return

    user.name = DEMO_USER_NAME
    user.email = DEMO_USER_EMAIL

    try:
        password_is_valid = password_hash.verify(
            DEMO_USER_PASSWORD,
            user.password_hash,
        )
    except Exception:
        password_is_valid = False

    if not password_is_valid:
        user.password_hash = password_hash.hash(DEMO_USER_PASSWORD)

    session.commit()


def authenticate_user(email: str, password: str, session: Session) -> User | None:
    user = session.scalar(select(User).where(User.email == email))

    if user is None:
        return None

    try:
        password_is_valid = password_hash.verify(password, user.password_hash)
    except Exception:
        password_is_valid = False

    if not password_is_valid:
        return None

    return user


def create_access_token(user: User) -> str:
    secret_key = os.getenv('JWT_SECRET_KEY')

    if not secret_key:
        raise HTTPException(
            status_code=500,
            detail='JWT secret key is not configured',
        )

    expires_at = datetime.now(timezone.utc) + timedelta(
        hours=ACCESS_TOKEN_EXPIRE_HOURS,
    )

    return jwt.encode(
        {
            'sub': str(user.user_id),
            'exp': expires_at,
        },
        secret_key,
        algorithm=JWT_ALGORITHM,
    )


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
    session: Annotated[Session, Depends(get_session)],
) -> User:
    authentication_error = HTTPException(
        status_code=401,
        detail='Invalid or expired access token',
        headers={'WWW-Authenticate': 'Bearer'},
    )

    if credentials is None:
        raise authentication_error

    secret_key = os.getenv('JWT_SECRET_KEY')

    if not secret_key:
        raise HTTPException(
            status_code=500,
            detail='JWT secret key is not configured',
        )

    try:
        payload = jwt.decode(
            credentials.credentials,
            secret_key,
            algorithms=[JWT_ALGORITHM],
        )
        user_id = int(payload.get('sub'))
    except (InvalidTokenError, TypeError, ValueError):
        raise authentication_error

    user = session.get(User, user_id)

    if user is None:
        raise authentication_error

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
