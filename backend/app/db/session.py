import os
from urllib.parse import quote_plus

from datetime import datetime, timezone
from typing import Annotated

from dotenv import load_dotenv
from fastapi import Depends
from sqlmodel import Session, create_engine
from sqlalchemy import event

from app.models.user_models import User

load_dotenv()


# Hook pour mettre à jour `updated_at`
def update_timestamp(session, flush_context, instances):
    for instance in session.dirty:
        if hasattr(instance, "updated_at"):
            instance.updated_at = datetime.now(timezone.utc)


# Configuration de la base de données
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")

# URL-encode the password
encoded_password = quote_plus(DB_PASSWORD)

DATABASE_URL = f"postgresql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)

# Enregistrer le hook au niveau global
event.listen(Session, "before_flush", update_timestamp)


# Fonction pour obtenir une session
def get_session():
    with Session(engine) as session:
        yield session


# Dépendance pour les endpoints FastAPI
SessionDep = Annotated[Session, Depends(get_session)]
