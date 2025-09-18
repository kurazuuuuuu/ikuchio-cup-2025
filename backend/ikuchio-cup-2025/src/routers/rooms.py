from fastapi import APIRouter
import uvicorn
import asyncio

from db.rooms import firestore_get_room, firestore_get_all_rooms, firestore_reset_all_rooms, create_room_with_random_users, firestore_send_message, firestore_get_messages
from pydantic import BaseModel

class MessageCreate(BaseModel):
    original_text: str
    sender_id: str = ""

rooms_router = APIRouter()

@rooms_router.post("/api/rooms")
async def create_room():
    try:
        result = create_room_with_random_users()
        if result is None:
            return {"error": "Not enough users to create room"}
        return result
    except:
        return {"error": "Failed to create room"}
    
@rooms_router.get("/api/rooms/{room_id}")
async def get_room(room_id: str):
    try:
        return(firestore_get_room(room_id))
    except:
        return("Error!")

@rooms_router.get("/api/rooms")
async def get_all_rooms():
    try:
        return firestore_get_all_rooms()
    except:
        return {"error": "Failed to get rooms"}

@rooms_router.post("/api/rooms/refresh")
async def refresh_rooms():
    try:
        return firestore_reset_all_rooms()
    except:
        return {"error": "Failed to reset rooms"}

# Singular endpoints for frontend compatibility
@rooms_router.get("/api/room/{room_id}")
async def get_room_messages(room_id: str):
    try:
        return firestore_get_messages(room_id)
    except Exception as e:
        return {"error": f"Failed to get messages: {str(e)}"}



@rooms_router.post("/api/room/{room_id}")
async def send_message(room_id: str, message_data: MessageCreate):
    print(f"[Router Debug] Received message request for room {room_id}")
    print(f"[Router Debug] Message data: {message_data.original_text}")
    try:
        # AI処理を含むメッセージ送信処理
        result = await firestore_send_message(room_id, message_data.sender_id, message_data.original_text)
        print(f"[Router Debug] Message and AI processing completed")
        
        # AI処理完了後にRedis Pub/Subで全Podに通知
        from websocket_manager import websocket_manager
        notification = {
            "type": "new_message",
            "room_id": room_id,
            "message_id": result.get("id", ""),
            "sender_id": message_data.sender_id
        }
        websocket_manager.publish_message(room_id, notification)
        print(f"[Router Debug] Notification published after AI processing")
        
        return result
    except Exception as e:
        print(f"[Router Debug] Error sending message: {str(e)}")
        return {"error": f"Failed to send message: {str(e)}"}

@rooms_router.post("/api/rooms/{room_id}")
async def send_message_plural(room_id: str, message_data: MessageCreate):
    try:
        # AI処理を含むメッセージ送信処理
        result = await firestore_send_message(room_id, message_data.sender_id, message_data.original_text)
        
        # AI処理完了後にRedis Pub/Subで全Podに通知
        from websocket_manager import websocket_manager
        notification = {
            "type": "new_message",
            "room_id": room_id,
            "message_id": result.get("id", ""),
            "sender_id": message_data.sender_id
        }
        websocket_manager.publish_message(room_id, notification)
        
        return result
    except Exception as e:
        return {"error": f"Failed to send message: {str(e)}"}
    
