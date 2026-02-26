

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from uuid import UUID
from entity.session import SessionDep
from service.user_service import UserService
from service.auth_service import AuthService
from schema.user import UserCreateDTO, UserReadDTO

router = APIRouter(prefix="/users", tags=["Users"])

def get_user_service(session: SessionDep) -> UserService:
    return UserService(session)

def get_auth_service(session: SessionDep) -> AuthService:
    return AuthService(session)

UserServiceDep = Annotated[UserService, Depends(get_user_service)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


@router.post("/", response_model=UserReadDTO, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreateDTO,
    user_service: UserServiceDep,
):
    db_user = user_service.create_user(user_data)
    if not db_user:
        raise HTTPException(status_code=400, detail="User already exists")  
    return db_user

# @router.get("/me", response_model=UserReadDTO)
# def read_user_me(
#     current_user: CurrentUserDep
# ):
#     return current_user

# @router.get("/{user_id}", response_model=UserReadDTO)
# def read_user(
#     user_id: UUID,
#     user_service: UserServiceDep,
#     current_user: CurrentUserDep,
# ):
#     if current_user.id != user_id and current_user.role != "admin":
#         raise HTTPException(status_code=403, detail="Not authorized to access this user")
    
#     db_user = user_service.get_user(user_id)
#     if not db_user:
#         raise HTTPException(status_code=404, detail="User not found")
    
#     return db_user
