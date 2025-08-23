from pydantic import BaseModel
from typing import Optional


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    created_at: float


class CreateUserRequest(BaseModel):
    name: str
    email: str


class ApiResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    message: str = ""
    server_id: str = ""
