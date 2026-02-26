from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import logging, jwt
from pwdlib import PasswordHash
from jwt.exceptions import InvalidTokenError
from sqlmodel import Session
from core.config import settings

logger = logging.getLogger(__name__)

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/token")

class AuthService:
    def __init__(self, session: Session):
        self.session = session

    def get_password_hash(self, password: str) -> str:
            return password_hash.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return password_hash.verify(plain_password, hashed_password)

    # #Todo: A supprimer
    # def decode_token(self, token: str) -> str:
    #     """Décode le token et retourne le 'sub' (email)."""
    #     try:
    #         payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    #         email: str = payload.get("sub")
    #         if email is None:
    #             raise InvalidTokenError
    #         return email
    #     except InvalidTokenError:
    #         raise HTTPException(status_code=401, detail="Token invalide")

    # def create_access_token(self, data: dict, expires_delta: timedelta | None = None):
    #     to_encode = data.copy()
    #     if expires_delta:
    #         expire = datetime.now(timezone.utc) + expires_delta
    #     else:
    #         expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    #     to_encode.update({"exp": expire})
    #     encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    #     return encoded_jwt
        