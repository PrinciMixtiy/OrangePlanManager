import re
from typing import Annotated, Type, Any

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from loguru import logger
from sqlmodel import SQLModel, select, Session

from app.db.session import SessionDep
from app.models.user_models import User
from app.schemas.auth_schemas import TokenData
from app.utilities.encoders import verify_password, decode_token
from app.utilities.exceptions import CREDENTIALS_EXCEPTION

# Load environment variables
load_dotenv()

ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_user(username: str, session: Session) -> User:
    """
    Retrieve a user by their username.

    Args:
        username (str): The username of the user to retrieve.
        session (Session): The database session.

    Returns:
        User: The retrieved user.

    Raises:
        HTTPException: If the user is not found.
    """
    user = session.exec(select(User).where(User.username == username)).first()

    if not user:
        logger.warning(f"User not found: {username}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


def get_user_by_email(session: Session, email: str) -> User:
    """
    Retrieve a user by their email.

    Args:
        session (Session): The database session.
        email (str): The email of the user to retrieve.

    Returns:
        User: The retrieved user.

    Raises:
        HTTPException: If the user is not found.
    """
    user = session.exec(select(User).where(User.email == email)).first()

    if not user:
        logger.warning(f"User not found with email: {email}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


def authenticate_user(username: str, password: str, session: Session) -> User:
    """
    Authenticate a user by username and password.

    Args:
        username (str): The username of the user.
        password (str): The password to verify.
        session (Session): The database session.

    Returns:
        User: The authenticated user.

    Raises:
        HTTPException: If the user is inactive or credentials are invalid.
    """
    user = get_user(username=username, session=session)

    if not user.is_active:
        logger.warning(f"Inactive user login attempt: {username}")
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Inactive user.",
        )

    if not verify_password(password, user.hashed_password):
        logger.warning(f"Invalid password attempt for user: {username}")
        raise CREDENTIALS_EXCEPTION

    logger.info(f"User authenticated successfully: {username}")
    return user


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: SessionDep,
) -> User:
    """
    Get the current authenticated user from the token.

    Args:
        token (str): The OAuth2 token.
        session (Session): The database session.

    Returns:
        User: The authenticated user.

    Raises:
        HTTPException: If the token is invalid or the user is not found.
    """
    payload = decode_token(token=token)
    username: str = payload.get("sub")

    if not username:
        logger.warning("Invalid token: Missing username")
        raise CREDENTIALS_EXCEPTION

    token_data = TokenData(username=username)
    user = get_user(username=token_data.username, session=session)

    return user


def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Get the current active user.

    Args:
        current_user (User): The current authenticated user.

    Returns:
        User: The active user.

    Raises:
        HTTPException: If the user is inactive.
    """
    if not current_user.is_active:
        logger.warning(f"Inactive user access attempt: {
                       current_user.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    return current_user


def validate_password(password: str) -> None:
    """
    Validate a password against predefined rules.

    Args:
        password (str): The password to validate.

    Raises:
        HTTPException: If the password does not meet the requirements.
    """
    validation_rules = [
        (lambda p: len(p) >= 6, "Password must be at least 6 characters long."),
        (lambda p: re.search(
            r'[A-Z]', p), "Password must contain at least one uppercase letter."),
        (lambda p: re.search(
            r'[a-z]', p), "Password must contain at least one lowercase letter."),
        (lambda p: re.search(r'[0-9]', p),
         "Password must contain at least one number."),
        (lambda p: re.search(
            r'[@$!%*?&#]', p), "Password must contain at least one special character."),
    ]

    for rule, error_message in validation_rules:
        if not rule(password):
            logger.warning(f"Password validation failed: {error_message}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message,
            )


def check_unique_constraint(
    session: Session,
    model: Type[SQLModel],
    field: str,
    value: Any,
    exclude_id: int | None = None,
) -> None:
    """
    Check if a value is unique for a given field in a model.

    Args:
        session (Session): The database session.
        model (Type[SQLModel]): The SQLModel class to check.
        field (str): The field to check for uniqueness.
        value (Any): The value to check.
        exclude_id (int | None): An ID to exclude from the check (e.g., for updates).

    Raises:
        HTTPException: If the value is not unique.
    """
    query = select(model).where(getattr(model, field) == value)
    if exclude_id is not None:
        query = query.where(model.id != exclude_id)

    if session.exec(query.exists()).scalar():
        logger.warning(f"Unique constraint violation: {
                       model.__name__}.{field} = {value}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{model.__name__} with {field} '{value}' already exists",
        )


class RoleChecker:
    """
    Role-based access control.

    Args:
        allowed_roles (list[str]): List of allowed roles or ["*"] for all roles.
    """

    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: Annotated[User, Depends(get_current_active_user)]) -> User:
        """
        Check if the user has the required role.

        Args:
            user (User): The current authenticated user.

        Returns:
            User: The user if authorized.

        Raises:
            HTTPException: If the user is not authorized.
        """
        if user.role in self.allowed_roles or "*" in self.allowed_roles:
            return user

        logger.warning(f"Unauthorized access attempt by user: {user.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have enough permissions",
        )
