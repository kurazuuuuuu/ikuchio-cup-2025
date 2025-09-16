from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer
import os

# Firebase Admin SDKを遅延インポート
firebase_app = None
firebase_auth = None

def get_firebase_auth():
    global firebase_app, firebase_auth
    if firebase_auth is None:
        try:
            from firebase_admin import auth, initialize_app, credentials
            if firebase_app is None:
                firebase_app = initialize_app()
                print("[Firebase] Admin SDK initialized successfully")
            firebase_auth = auth
        except Exception as e:
            print(f"[Firebase] Admin SDK initialization failed: {e}")
            firebase_auth = None
    return firebase_auth

security = HTTPBearer()

async def verify_firebase_token(request: Request) -> dict:
    """Firebase IDトークンを検証してユーザー情報を返す"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        print(f"[Firebase] Missing or invalid auth header: {auth_header}")
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = auth_header.split(' ')[1]
    print(f"[Firebase] Attempting to verify token: {token[:20]}...")
    
    try:
        # Firebase IDトークンを検証
        auth_module = get_firebase_auth()
        if auth_module is None:
            raise Exception("Firebase Admin SDK not available")
        decoded_token = auth_module.verify_id_token(token)
        print(f"[Firebase] Token verified successfully for UID: {decoded_token['uid']}")
        return {
            'firebase_uid': decoded_token['uid'],
            'email': decoded_token.get('email'),
            'email_verified': decoded_token.get('email_verified', False)
        }
    except Exception as e:
        print(f"[Firebase] Token verification failed: {type(e).__name__}: {str(e)}")
        import traceback
        print(f"[Firebase] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=401, detail=f"Invalid Firebase token: {str(e)}")

async def get_current_user(request: Request) -> dict:
    """現在認証されているユーザーを取得"""
    try:
        return await verify_firebase_token(request)
    except HTTPException as e:
        print(f"[Firebase] Authentication failed: {e.detail}")
        raise e