# Authentication endpoints
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(tags=["auth"])

# TODO: POST /token - Login
# TODO: POST /register - Register new user
# TODO: GET /me - Get current user 