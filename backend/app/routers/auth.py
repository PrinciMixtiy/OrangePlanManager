from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from loguru import logger
from sqlmodel import select

from app.db.session import SessionDep
from app.models.user_models import RoleType
from app.utilities.dependencies import (ACCESS_TOKEN_EXPIRE_MINUTES,
                                        REFRESH_TOKEN_EXPIRE_DAYS, authenticate_user, decode_token,
                                        get_current_active_user,
                                        validate_password, RoleChecker, get_user)
from app.models.user_models import User, UserCreate, UserPublic
from app.schemas.auth_schemas import RefreshToken, Token
from app.utilities.encoders import hash_password, encode_token

logger.remove()
# Configure loguru to write logs to a file
logger.add("logs/authentications.log", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}:{function}:{line} - {message} | {extra}", rotation="500 MB", retention="10 days", colorize=True)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate, session: SessionDep,
    current_user: Annotated[bool, Depends(RoleChecker(allowed_roles=[RoleType.ADMIN]))]
):
    user_data = user.model_dump()

    if session.exec(select(User).where(User.username == user_data["username"])).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="L'utilisateur existe dejas."
        )

    if session.exec(select(User).where(User.email == user_data["email"])).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="l'Email est deja utilise."
        )

    validate_password(user_data["password"])
    hashed_password = hash_password(user_data["password"])
    user_db = User(**user_data, hashed_password=hashed_password)

    session.add(user_db)
    session.commit()
    session.refresh(user_db)

    with logger.contextualize(username=user_db.username, role=user_db.role, by=current_user.username):
        logger.info(f"User created.")
    return user_db


@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: SessionDep
) -> Token:
    user = authenticate_user(form_data.username, form_data.password, session)
    sign_in_logger = logger.bind(username=form_data.username)
    if not user:
        sign_in_logger.warning(f"Login failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Informations utilisateurs invalides."
        )

    access_data = {"sub": user.username, "role": user.role}
    refresh_data = {"sub": user.username}

    access_token = encode_token(
        data=access_data, expires_delta=timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = encode_token(
        data=refresh_data, expires_delta=timedelta(
            days=REFRESH_TOKEN_EXPIRE_DAYS)
    )

    sign_in_logger.info(f"User logged in.")
    return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh: RefreshToken, session: SessionDep):
    payload = decode_token(refresh.refresh_token)
    
    user = get_user(payload.get("sub"), session)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token.",
        )

    access_token = encode_token(
        {"sub": user.username, "role": user.role}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = encode_token(
        {"sub": user.username}, timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )

    return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")


@router.get("/me", response_model=UserPublic, status_code=status.HTTP_200_OK)
async def read_users_me(
    current_user: Annotated[UserPublic, Depends(get_current_active_user)],
):
    return current_user
