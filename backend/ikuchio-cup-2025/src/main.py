from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from routers import users, rooms
import json
from starlette.websockets import WebSocketState

app = FastAPI()

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
    return {"message": "Hello!", "status": "ok"}

@app.get("/api/health")
def api_health_check():
    return {"message": "API is working!", "status": "ok"}

@app.get("/api/debug")
def debug_database():
    from db.users import firestore_get_all_users
    from db.rooms import firestore_get_all_rooms
    
    users = firestore_get_all_users()
    rooms = firestore_get_all_rooms()
    
    return {
        "users_count": len(users),
        "rooms_count": len(rooms),
        "users": users,
        "rooms": rooms
    }


# WebSocket接続管理
active_connections = {}

@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    # CORSヘッダーを設定して接続を許可
    await websocket.accept()
    
    if room_id not in active_connections:
        active_connections[room_id] = []
    active_connections[room_id].append(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            # 同じルームの他の接続にメッセージを送信
            for connection in active_connections[room_id]:
                if connection != websocket:
                    try:
                        await connection.send_text(data)
                    except:
                        pass
    except (WebSocketDisconnect, Exception):
        try:
            active_connections[room_id].remove(websocket)
            if not active_connections[room_id]:
                del active_connections[room_id]
        except (ValueError, KeyError):
            pass

app.include_router(users.users_router)
app.include_router(rooms.rooms_router)

if __name__ == "__main__":
    import uvicorn
    print("Starting server on http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False, log_level="warning", access_log=False)
