from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os

class UserCreate(BaseModel):
    firebase_uid: str

users_router = APIRouter()

@users_router.post("/api/users")
async def create_user(user_data: UserCreate):
    if os.environ.get('DISABLE_FIRESTORE') == 'true':
        return {
            "firebase_uid": user_data.firebase_uid,
            "created_at": "2025-01-01T00:00:00",
            "room_id": None,
            "status": "firestore_disabled"
        }
    
    try:
        from db.users import firestore_create_user
        return firestore_create_user(user_data.firebase_uid)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ユーザー作成に失敗しました: {str(e)}")

@users_router.get("/api/users")
async def get_user(firebase_uid: str):
    if os.environ.get('DISABLE_FIRESTORE') == 'true':
        return {
            "firebase_uid": firebase_uid,
            "created_at": "2025-01-01T00:00:00",
            "room_id": None,
            "status": "firestore_disabled"
        }
    
    try:
        from db.users import firestore_get_user
        user = firestore_get_user(firebase_uid)
        if not user:
            raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ユーザー取得に失敗しました: {str(e)}")