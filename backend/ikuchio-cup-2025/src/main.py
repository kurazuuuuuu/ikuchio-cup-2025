from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from routers import users, rooms
import json
import os
import asyncio
from contextlib import asynccontextmanager
from starlette.websockets import WebSocketState
# from websocket_manager import websocket_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[Startup] Application starting up...")
    
    # ルームスケジューラーを開始
    from scheduler.room_scheduler import room_scheduler
    asyncio.create_task(room_scheduler.start())
    
    # Redis Pub/Sub購読を開始
    # await websocket_manager.start_subscriber()
    
    yield
    
    # ルームスケジューラーを停止
    room_scheduler.stop()
    print("[Shutdown] Application shutting down...")

# 本番環境では/docsを無効化
is_production = os.environ.get('ENVIRONMENT') == 'production'
app = FastAPI(
    lifespan=lifespan,
    docs_url=None if is_production else "/docs",
    redoc_url=None if is_production else "/redoc",
    openapi_url=None if is_production else "/openapi.json"
)

# CORS設定を簡素化
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    try:
        return {"message": "Hello!", "status": "ok"}
    except Exception as e:
        print(f"[Health] Error: {str(e)}")
        import traceback
        print(f"[Health] Traceback: {traceback.format_exc()}")
        return {"message": f"Health check failed: {str(e)}", "status": "error"}

@app.get("/api/status")
def api_status():
    """APIの状態を詳細に返すエンドポイント"""
    try:
        import sys
        import os
        status_info = {
            "status": "ok",
            "python_version": sys.version,
            "python_path": sys.path,
            "working_directory": os.getcwd(),
            "environment_vars": {
                "PORT": os.environ.get("PORT", "Not set"),
                "PYTHONPATH": os.environ.get("PYTHONPATH", "Not set"),
                "API_KEY": "Set" if os.environ.get("API_KEY") else "Not set"
            }
        }
        return status_info
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }

@app.get("/api/health")
def api_health_check():
    return {"message": "API is working!", "status": "ok"}

@app.get("/api/debug")
def debug_database():
    import os
    from gcp.gemini import get_api_key
    
    # Firestoreアクセスをテスト
    firestore_status = "unknown"
    users = []
    rooms = []
    
    if os.environ.get('DISABLE_FIRESTORE') == 'true':
        firestore_status = "disabled"
    else:
        try:
            from db.users import firestore_get_all_users
            from db.rooms import firestore_get_all_rooms
            users = firestore_get_all_users()
            rooms = firestore_get_all_rooms()
            firestore_status = "success"
        except Exception as e:
            firestore_status = f"error: {str(e)}"
    
    # API KEYのテスト
    api_key_status = "unknown"
    try:
        api_key = get_api_key()
        if api_key == "fallback":
            api_key_status = "failed"
        else:
            api_key_status = f"success (length: {len(api_key)})"
    except Exception as e:
        api_key_status = f"error: {str(e)}"
    
    return {
        "firestore_status": firestore_status,
        "users_count": len(users),
        "rooms_count": len(rooms),
        "api_key_status": api_key_status,
        "environment": {
            "GOOGLE_CLOUD_PROJECT": os.environ.get("GOOGLE_CLOUD_PROJECT", "Not set"),
            "GCLOUD_PROJECT": os.environ.get("GCLOUD_PROJECT", "Not set")
        },
        "users": users[:5] if users else [],  # 最初の5件のみ
        "rooms": rooms[:5] if rooms else []   # 最初の5件のみ
    }

@app.get("/api/test-secret")
def test_secret_manager():
    """Secret Manager接続テスト用エンドポイント"""
    from gcp.secret_manager import SecretManagerUtil
    import traceback
    
    try:
        print("[Test] Creating SecretManagerUtil instance...")
        util = SecretManagerUtil()
        
        print("[Test] Attempting to get secret...")
        secret = util.get_secret("88236233617", "google-vertexai-api-key")
        
        return {
            "status": "success",
            "secret_length": len(secret),
            "secret_preview": secret[:10] + "..."
        }
        
    except Exception as e:
        error_info = {
            "status": "error",
            "error_type": type(e).__name__,
            "error_message": str(e),
            "traceback": traceback.format_exc()
        }
        print(f"[Test] Error: {error_info}")
        return error_info


# WebSocket接続管理
active_connections = {}

@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await websocket.accept()
    
    if room_id not in active_connections:
        active_connections[room_id] = []
    active_connections[room_id].append(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            print(f"[WebSocket] Received message in room {room_id}: {data}")
            
            # 同じルームの他の接続にメッセージを送信
            for connection in active_connections[room_id]:
                if connection != websocket:
                    try:
                        await connection.send_text(data)
                    except:
                        pass
                
    except (WebSocketDisconnect, Exception) as e:
        print(f"[WebSocket] Client disconnected from room {room_id}: {e}")
    finally:
        try:
            active_connections[room_id].remove(websocket)
            if not active_connections[room_id]:
                del active_connections[room_id]
        except (ValueError, KeyError):
            pass

try:
    import os
    if os.environ.get('DISABLE_FIRESTORE') == 'true':
        from routers import users_simple
        app.include_router(users_simple.users_router)
        print("[Startup] Simple routers loaded (Firestore disabled)")
    else:
        app.include_router(users.users_router)
        app.include_router(rooms.rooms_router)
        print("[Startup] Full routers loaded successfully")
except Exception as e:
    print(f"[Startup] Error loading routers: {str(e)}")
    import traceback
    print(f"[Startup] Traceback: {traceback.format_exc()}")
    raise e

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting server on http://0.0.0.0:{port}")
    print("Server starting...")
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False, log_level="info", timeout_keep_alive=30)
