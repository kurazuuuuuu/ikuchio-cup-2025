import redis
import json
import asyncio
import os
from typing import Dict, List
from fastapi import WebSocket

class WebSocketManager:
    def __init__(self):
        redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.active_connections: Dict[str, List[WebSocket]] = {}
        
    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)
        print(f"[WebSocket] Client connected to room {room_id}")
        
    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.active_connections:
            try:
                self.active_connections[room_id].remove(websocket)
                if not self.active_connections[room_id]:
                    del self.active_connections[room_id]
                print(f"[WebSocket] Client disconnected from room {room_id}")
            except ValueError:
                pass
                
    async def send_to_room(self, room_id: str, message: dict):
        """同じPod内のWebSocket接続にメッセージを送信"""
        if room_id in self.active_connections:
            message_str = json.dumps(message)
            disconnected = []
            
            for connection in self.active_connections[room_id]:
                try:
                    await connection.send_text(message_str)
                except:
                    disconnected.append(connection)
            
            # 切断された接続を削除
            for conn in disconnected:
                self.disconnect(conn, room_id)
                
    def publish_message(self, room_id: str, message: dict):
        """Redis Pub/Subでメッセージを全Podに配信"""
        try:
            self.redis_client.publish(f"room:{room_id}", json.dumps(message))
            print(f"[Redis] Published message to room {room_id}")
        except Exception as e:
            print(f"[Redis] Failed to publish message: {e}")
            
    async def start_subscriber(self):
        """Redis Pub/Subの購読を開始"""
        pubsub = self.redis_client.pubsub()
        pubsub.psubscribe("room:*")
        
        async def listen():
            while True:
                try:
                    message = pubsub.get_message(timeout=1.0)
                    if message and message['type'] == 'pmessage':
                        channel = message['channel']
                        room_id = channel.split(':', 1)[1]
                        data = json.loads(message['data'])
                        await self.send_to_room(room_id, data)
                except Exception as e:
                    print(f"[Redis] Subscriber error: {e}")
                await asyncio.sleep(0.1)
        
        asyncio.create_task(listen())

# グローバルインスタンス
websocket_manager = WebSocketManager()