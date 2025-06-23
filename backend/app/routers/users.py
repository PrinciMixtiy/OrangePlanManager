from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select, Session
from loguru import logger

from app.db.session import SessionDep
from app.models.user_models import RoleType
from app.models.user_models import User, UserPublic, UserUpdate
from app.utilities.dependencies import RoleChecker
from app.utilities.encoders import hash_password, verify_password
from app.utilities.exceptions import CREDENTIALS_EXCEPTION
from loguru import logger

logger.remove()
# Configure loguru to write logs to a file
logger.add("logs/users.log", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}:{function}:{line} - {message} | {extra}",
           rotation="500 MB", retention="10 days", colorize=True)

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


def get_user_by_id(session: Session, user_id: int) -> User:
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )
    return user


@router.get("/", response_model=list[UserPublic], status_code=status.HTTP_200_OK)
def list_users(
    session: SessionDep,
    _: Annotated[bool, Depends(RoleChecker(allowed_roles=[RoleType.ADMIN]))]
):
    users = session.exec(select(User)).all()
    return users


@router.get("/{user_id}", response_model=UserPublic, status_code=status.HTTP_200_OK)
def get_user(
    user_id: int,
    session: SessionDep,
    _: Annotated[bool, Depends(RoleChecker(allowed_roles=[RoleType.ADMIN]))]
):
    user = get_user_by_id(session, user_id)
    logger.info(f"Retrieved user with ID {user_id}.")
    return user


@router.patch("/{user_id}", response_model=UserPublic, status_code=status.HTTP_200_OK)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    session: SessionDep,
    current_user: Annotated[bool, Depends(RoleChecker(allowed_roles=[RoleType.ADMIN]))]
):
    user = get_user_by_id(session, user_id)
    
    user_update_data = user_update.model_dump(exclude_unset=True)

    if user_update_data.get("old_password") and user_update_data.get("new_password"):
        if verify_password(user_update_data["old_password"], user.hashed_password):
            user_update_data["hashed_password"] = hash_password(
                user_update_data["new_password"])

        else:
            raise CREDENTIALS_EXCEPTION

    user.sqlmodel_update(user_update_data)
    
    session.add(user)
    session.commit()
    session.refresh(user)
    with logger.contextualize(user_modified=user.username, user_modifier=current_user.username):
        logger.info(f"Updated user with ID {user_id}.")
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    session: SessionDep,
    current_user: Annotated[bool, Depends(RoleChecker(allowed_roles=[RoleType.ADMIN]))]
):
    user = get_user_by_id(session, user_id)
    session.delete(user)
    session.commit()
    
    with logger.contextualize(user=user.username, by=current_user.username):
        logger.info('User Deleted.')
