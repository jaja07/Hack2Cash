from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from sqlmodel import Session, select

from core.config import settings
from database.session import SessionDep

logger = logging.getLogger(__name__)

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/token")


class AuthService:
    """Service d'authentification : hachage, vérification de mot de passe et JWT."""

    def __init__(self, session: Session):
        self.session = session

    def get_password_hash(self, password: str) -> str:
        """Retourne le hash Argon2 du mot de passe."""
        return password_hash.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Vérifie un mot de passe en clair contre son hash."""
        return password_hash.verify(plain_password, hashed_password)

    def create_access_token(
        self, data: dict, expires_delta: timedelta | None = None
    ) -> str:
        """Crée un JWT signé avec le sub = email de l'utilisateur."""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (
            expires_delta
            if expires_delta
            else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    def decode_token(self, token: str) -> str:
        """Décode le JWT et retourne l'email (sub)."""
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            email: str | None = payload.get("sub")
            if email is None:
                raise InvalidTokenError("Pas de sub dans le token")
            return email
        except InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalide ou expiré",
                headers={"WWW-Authenticate": "Bearer"},
            )


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: SessionDep,
):
    """
    Dependency FastAPI : extrait l'utilisateur courant depuis le Bearer JWT.
    À injecter dans les routes protégées.
    """
    from database.models import User  # import local pour éviter les circulaires

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Impossible de valider les identifiants",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email: str | None = payload.get("sub")
        if email is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception

    user = session.exec(select(User).where(User.email == email)).first()
    if user is None:
        raise credentials_exception
    return user
