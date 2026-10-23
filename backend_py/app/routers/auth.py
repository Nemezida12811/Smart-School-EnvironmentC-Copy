from fastapi import APIRouter, Depends

from ..errors import ApiError, failing_as, ok
from ..repositories import Users
from ..schemas import LoginBody, RegisterBody
from ..security import (current_user_id, generate_token, hash_password, validate_email,
                        validate_password, verify_password)

router = APIRouter(prefix="/api/auth")


@router.post("/register")
async def register(body: RegisterBody = RegisterBody()):
    with failing_as("Registration failed", with_details=True):
        if not body.username or not body.email or not body.password:
            raise ApiError(400, "All fields are required")
        if not validate_email(body.email):
            raise ApiError(400, "Invalid email format")
        if not validate_password(body.password):
            raise ApiError(400, "Password must be at least 6 characters")
        if await Users.find_by_email(body.email):
            raise ApiError(400, "User with this email already exists")

        user_id = await Users.create(body.username, body.email, await hash_password(body.password))
        return ok({
            "message": "User registered successfully",
            "token": generate_token(str(user_id)),
            "user": {"id": str(user_id), "username": body.username, "email": body.email, "role": "user"},
        }, 201)


@router.post("/login")
async def login(body: LoginBody = LoginBody()):
    with failing_as("Login failed", with_details=True):
        if not body.email or not body.password:
            raise ApiError(400, "Email and password are required")
        user = await Users.find_by_email(body.email)
        if not user or not await verify_password(body.password, user["password"]):
            raise ApiError(401, "Invalid credentials")
        return ok({
            "message": "Login successful",
            "token": generate_token(str(user["_id"])),
            "user": Users.to_json(user),
        })


@router.post("/logout")
async def logout():
    return ok({"message": "Logout successful"})


@router.get("/me")
async def me(user_id: str = Depends(current_user_id)):
    with failing_as("Failed to get user info", with_details=True):
        user = await Users.find_by_id(user_id)
        if not user:
            raise ApiError(404, "User not found")
        return ok(Users.to_json(user))
