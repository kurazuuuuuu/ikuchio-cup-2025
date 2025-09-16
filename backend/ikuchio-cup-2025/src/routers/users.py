from fastapi import APIRouter
import uvicorn

from db.users import firestore_create_user, firestore_get_user

users_router = APIRouter()

@users_router.post("/api/users")
async def create_user(fingerprint_id: str = "0000"):
    try:
        return(firestore_create_user(fingerprint_id))
    except:
        return("Error!")
    
@users_router.get("/api/users")
async def get_users(fingerprint_id: str = "0000"):
    try:
        return(firestore_get_user(fingerprint_id))
    except:
        return("Error!")