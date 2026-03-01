from datetime import timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from core.config import settings
from entity.session import SessionDep
from entity.user_entity import User
from schema.user import Token, UserCreateDTO, UserReadDTO
from service.auth_service import AuthService, get_current_user
from service.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])

# ── Dependency helpers ────────────────────────────────────────────────────────

def get_user_service(session: SessionDep) -> UserService:
    return UserService(session)

def get_auth_service(session: SessionDep) -> AuthService:
    return AuthService(session)

UserServiceDep   = Annotated[UserService, Depends(get_user_service)]
AuthServiceDep   = Annotated[AuthService, Depends(get_auth_service)]
CurrentUserDep   = Annotated[User, Depends(get_current_user)]

# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/", response_model=UserReadDTO, status_code=status.HTTP_201_CREATED,
             summary="Créer un compte utilisateur")
def create_user(user_data: UserCreateDTO, user_service: UserServiceDep):
    """Inscription d'un nouvel utilisateur."""
    try:
        return user_service.create_user(user_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/token", response_model=Token, tags=["Auth"],
             summary="Connexion — obtenir un JWT")
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_service: UserServiceDep,
    auth_service: AuthServiceDep,
):
    """
    Connexion via email + mot de passe (OAuth2 password flow).
    Retourne un access_token JWT Bearer.
    """
    user = user_service.get_user_by_email(form_data.username)
    if not user or not auth_service.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = auth_service.create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserReadDTO, summary="Profil de l'utilisateur connecté")
def read_user_me(current_user: CurrentUserDep):
    """Retourne les informations de l'utilisateur authentifié."""
    return current_user


@router.get("/{user_id}", response_model=UserReadDTO,
            summary="Récupérer un utilisateur par ID")
def read_user(
    user_id: UUID,
    user_service: UserServiceDep,
    current_user: CurrentUserDep,
):
    """
    Accès à un profil utilisateur.
    Un utilisateur ne peut voir que son propre profil ; un admin peut voir tous les profils.
    """
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Non autorisé à accéder à ce profil",
        )
    db_user = user_service.get_user(user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Utilisateur introuvable")
    return db_user
