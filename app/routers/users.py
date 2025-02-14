# User-related endpoints
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/users", tags=["users"])

# TODO: GET /users/ - List users
# TODO: POST /users/ - Create user
# TODO: GET /users/{user_id} - Get user
# TODO: PUT /users/{user_id} - Update user
# TODO: DELETE /users/{user_id} - Delete user 