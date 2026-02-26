import logging
from sqlmodel import Session, select
from uuid import UUID
from .auth_service import AuthService
from entity.user_entity import User
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
        statement = select(User).where(User.id == user_id)
        return self.session.exec(statement).first()

    def get_user_by_email(self, email: str) -> User | None:
        """Récupère un utilisateur par son email."""
        statement = select(User).where(User.email == email)
        return self.session.exec(statement).first()

    def get_all_users(self, skip: int = 0, limit: int = 10) -> list[User]:
        """Récupère la liste de tous les utilisateurs."""
        statement = select(User)
        results = self.session.exec(statement=statement.offset(skip).limit(limit))
        return list(results.all())

    def create_user(self, user: UserCreateDTO) -> User:
        """Crée un nouvel utilisateur."""
        # 1. Vérification de l'unicité de l'email
        existing_user = self.get_user_by_email(user.email)
        if existing_user:
            logger.warning(f"Attempt to create user with existing email: {user.email}")
            raise ValueError("Email already registered")

        # 2. Hachage du mot de passe
        hashed_password = self.auth_service.get_password_hash(user.password)

        # 3. Création de l'entité User
        db_user = User(
            nom=user.nom,
            prenom=user.prenom,
            email=user.email,
            hashed_password=hashed_password,
            role=user.role
        )

        # 4. Enregistrement en base de données
        self.session.add(db_user)
        self.session.commit()
        self.session.refresh(db_user)

        logger.info(f"User created with email: {user.email}")
        return db_user