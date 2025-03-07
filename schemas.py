from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserLogin(BaseModel):
    username: str
    password: str

class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class PlayerBase(BaseModel):
    name: str
    position: Optional[str] = None
    team: Optional[str] = None
    age: Optional[int] = None
    jersey_number: Optional[int] = None

class PlayerCreate(PlayerBase):
    pass

class PlayerUpdate(PlayerBase):
    name: Optional[str] = None

class Player(PlayerBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True 