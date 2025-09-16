from fastapi import APIRouter
import uvicorn

from db.users import firestore_create_user

users_router = APIRouter()

@users_router.post("/api/users")
async def create_user(fingerprint_id: str = "0000"):
    try:
        firestore_create_user(fingerprint_id)
        return("create user successed!!")
    except:
        return("Error!")