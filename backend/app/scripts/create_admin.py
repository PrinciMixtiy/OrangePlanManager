import argparse

from sqlalchemy import select
from sqlmodel import Session

from app.db.session import engine
from app.models.user_models import User

from app.models.user_models import RoleType
from app.utilities.encoders import hash_password


def create_admin_user(username: str, email: str, password: str):
    """Creates an admin user if one does not already exist."""
    with Session(engine) as session:
        # Check if the admin user already exists
        admin_user = session.exec(select(User).where(
            User.username == username)).first()
        if admin_user:
            print(f"Admin user '{username}' already exists.")
            return

        # Create the admin user
        hashed_password = hash_password(password)
        admin_user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            role=RoleType.ADMIN,
            is_active=True
        )
        session.add(admin_user)
        session.commit()
        print(f"Admin user '{username}' created successfully.")


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Create an admin user.")
    parser.add_argument("--username", required=True, help="Admin username")
    parser.add_argument("--email", required=True, help="Admin email")
    parser.add_argument("--password", required=True, help="Admin password")

    args = parser.parse_args()

    # Call the function with the provided arguments
    create_admin_user(username=args.username,
                      email=args.email, password=args.password)
