import logging
from sqlmodel import Session, select
from uuid import UUID

from .auth_service import AuthService
from database.models import User
from schema.user import UserCreateDTO, UserUpdateDTO

logger = logging.getLogger(__name__)


class UserService:
    """
    Service contenant la logique métier pour les utilisateurs.
    Encapsule la validation, le hachage des mots de passe et les règles métier.
    """

    def __init__(self, session: Session):
        self.session = session
        self.auth_service = AuthService(session)

    def get_user(self, user_id: UUID) -> User | None:
        """Récupère un utilisateur par son ID."""
        return self.session.exec(select(User).where(User.id == user_id)).first()

    def get_user_by_email(self, email: str) -> User | None:
        """Récupère un utilisateur par son email."""
        return self.session.exec(select(User).where(User.email == email)).first()

    def get_all_users(self, skip: int = 0, limit: int = 10) -> list[User]:
        """Récupère la liste paginée de tous les utilisateurs."""
        statement = select(User).offset(skip).limit(limit)
        return list(self.session.exec(statement).all())

    def create_user(self, user: UserCreateDTO) -> User:
        """
        Crée un nouvel utilisateur.
        Lève ValueError si l'email est déjà utilisé.
        """
        existing = self.get_user_by_email(user.email)
        if existing:
            logger.warning(f"Email déjà enregistré : {user.email}")
            raise ValueError("Email déjà enregistré")

        hashed_password = self.auth_service.get_password_hash(user.password)
        db_user = User(
            nom=user.nom,
            prenom=user.prenom,
            email=user.email,
            hashed_password=hashed_password,
            role=user.role,
        )
        self.session.add(db_user)
        self.session.commit()
        self.session.refresh(db_user)

        logger.info(f"Utilisateur créé : {user.email}")
        return db_user
