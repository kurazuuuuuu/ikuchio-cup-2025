from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
import uvicorn

from db.users import firestore_create_user, firestore_get_user
from auth.firebase_auth import get_current_user

class UserCreate(BaseModel):
    firebase_uid: str

users_router = APIRouter()

@users_router.post("/api/users")
async def create_user(user_data: UserCreate, current_user: dict = Depends(get_current_user)):
    try:
        print(f"[Users] Auth UID: {current_user['firebase_uid']}, Request UID: {user_data.firebase_uid}")
        if current_user['firebase_uid'] != user_data.firebase_uid:
            raise HTTPException(status_code=403, detail="Unauthorized: UID mismatch")
        
        result = firestore_create_user(user_data.firebase_uid)
        if isinstance(result, str) and "already exist" in result:
            return firestore_get_user(user_data.firebase_uid)
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ユーザー作成に失敗しました: {str(e)}")
    
@users_router.get("/api/users")
async def get_users(firebase_uid: str, current_user: dict = Depends(get_current_user)):
    try:
        print(f"[Users] Auth UID: {current_user['firebase_uid']}, Request UID: {firebase_uid}")
        if current_user['firebase_uid'] != firebase_uid:
            raise HTTPException(status_code=403, detail="Unauthorized: UID mismatch")
        
        result = firestore_get_user(firebase_uid)
        if not result:
            raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ユーザー取得に失敗しました: {str(e)}")