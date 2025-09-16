from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import uvicorn

from db.users import firestore_create_user, firestore_get_user

class UserCreate(BaseModel):
    fingerprint_id: str

users_router = APIRouter()

@users_router.post("/api/users")
async def create_user(user_data: UserCreate):
    try:
        fingerprint_id = user_data.fingerprint_id
        
        if not fingerprint_id or len(fingerprint_id) < 8:
            raise HTTPException(status_code=400, detail="無効なフィンガープリントです")
        
        result = firestore_create_user(fingerprint_id)
        if isinstance(result, str) and "already exist" in result:
            return firestore_get_user(fingerprint_id)
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ユーザー作成に失敗しました: {str(e)}")
    
@users_router.get("/api/users")
async def get_users(fingerprint_id: str):
    try:
        if not fingerprint_id or len(fingerprint_id) < 8:
            raise HTTPException(status_code=400, detail="無効なフィンガープリントです")
        
        result = firestore_get_user(fingerprint_id)
        if not result:
            raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ユーザー取得に失敗しました: {str(e)}")