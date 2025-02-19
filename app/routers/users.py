# User-related endpoints
from fastapi import APIRouter, Form, Depends
#import jwt

router = APIRouter()

@router.get("/users")
def get_users():
    return {"message": "List of users"}

@router.post("/users")
def create_access_token(name: str = Form(...), email: str = Form(...)):
    # Create the access token logic goes here
    return {"name": name, "email": email}

###potential code for generating jwt###
    #expiration_time = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    
    # Create the JWT token
    #token = jwt.encode(
        #{'exp': expiration_time, **data},  # Add the expiration to the data
        #SECRET_KEY,
        #algorithm='HS256'
    #)
###

# TODO: GET /users/{user_id} - Get user
# TODO: PUT /users/{user_id} - Update user
# TODO: DELETE /users/{user_id} - Delete user 