from pydantic import BaseModel


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
    data: dict | None = None
    message: str = ""
    server_id: str = ""
