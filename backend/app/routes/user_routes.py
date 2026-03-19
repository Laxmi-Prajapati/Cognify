from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.repositories.user_repo import UserRepository

MONGO_URI = "mongodb+srv://admin:admin@lit-coders.dcuhn.mongodb.net/?retryWrites=true&w=majority&appName=lit-coders"
DB_NAME = "error_stupifyed"

router = APIRouter()
repo = UserRepository(MONGO_URI, DB_NAME)


class CreateUserRequest(BaseModel):
    email: str
    name: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class UpdateUserRequest(BaseModel):
    uid: str
    update_data: dict


@router.post("/create_user", status_code=201)
def create_user(body: CreateUserRequest):
    try:
        uid = repo.create_user(body.email, body.name, body.password)
        return {"uid": uid}
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/login")
def login(body: LoginRequest):
    try:
        uid = repo.login_user(body.email, body.password)
        if uid:
            return {"uid": uid}
        raise HTTPException(status_code=401, detail="Invalid credentials")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get_user/{uid}")
def get_user(uid: str):
    try:
        user = repo.get_user(uid)
        if user:
            return {"data": user}
        raise HTTPException(status_code=404, detail="User not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update_user")
def update_user(body: UpdateUserRequest):
    try:
        repo.update_user(body.uid, body.update_data)
        return {"message": "User updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
