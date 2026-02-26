from .user_entity import User  # Importer le modèle User pour que SQLModel puisse créer la table correspondante dans la base de données
from core.config import settings
from typing import Annotated
from fastapi import Depends
from sqlmodel import create_engine, Session, SQLModel

database_url = settings.database_url

if database_url:
    engine = create_engine(database_url, echo=True) #A SQLModel engine (underneath it's actually a SQLAlchemy engine) is what holds the connections to the database
else:
    raise ValueError("DATABASE_URL environment variable is not set.")


def initialize_database():
    """Initialise la base de données en créant les tables si elles n'existent pas."""
    SQLModel.metadata.create_all(engine)

"""
A Session is what stores the objects in memory and keeps track of any changes needed in the data, then it uses the engine to communicate with the database.  
Here we define a function that will create a new session for us whenever we need it.The 'with' statement ensures that the session is properly closed after we're done using it.
"""
def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)] #This is a type alias that can be used in FastAPI path operations to automatically get a database session injected into them.

if __name__ == "__main__":
    initialize_database()