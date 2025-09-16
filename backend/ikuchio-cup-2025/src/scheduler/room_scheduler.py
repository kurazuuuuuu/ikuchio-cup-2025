import asyncio
import datetime
from db.users import firestore_get_all_users, db
from db.rooms import firestore_create_room
import uuid
import random

class RoomScheduler:
    def __init__(self):
        self.running = False
    
    def get_next_reset_time(self):
        """次の15分区切りの時刻を取得"""
        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
        # 現在の分を15分区切りに調整
        next_minute = ((now.minute // 15) + 1) * 15
        if next_minute >= 60:
            next_hour = now.hour + 1
            next_minute = 0
        else:
            next_hour = now.hour
        
        next_reset = now.replace(hour=next_hour, minute=next_minute, second=0, microsecond=0)
        if next_reset <= now:
            next_reset += datetime.timedelta(hours=1)
        
        return next_reset
    
    async def reset_all_rooms(self):
        """全ユーザーのルームをリセットし、新しいペアリングを作成"""
        try:
            print("[Scheduler] Starting room reset...")
            
            # 全ユーザーを取得
            users = firestore_get_all_users()
            if not users:
                print("[Scheduler] No users found")
                return
            
            # 全ユーザーのroom_idをクリア
            batch = db.batch()
            for user in users:
                user_id = f"user_{user['firebase_uid']}"
                user_ref = db.collection("users").document(user_id)
                batch.update(user_ref, {"room_id": None})
            
            batch.commit()
            print(f"[Scheduler] Cleared room_id for {len(users)} users")
            
            # ユーザーをシャッフルしてペアリング
            random.shuffle(users)
            
            # ペアを作成
            pairs = []
            for i in range(0, len(users), 2):
                if i + 1 < len(users):
                    pairs.append([users[i], users[i + 1]])
                else:
                    # 奇数の場合、最後のユーザーは1人ルーム
                    pairs.append([users[i]])
            
            # 新しいルームを作成
            for pair in pairs:
                room_id = f"room_{uuid.uuid4()}"
                user_ids = [user['firebase_uid'] for user in pair]
                
                # ルーム作成
                firestore_create_room(room_id, user_ids)
                
                # ユーザーにルームIDを割り当て
                batch = db.batch()
                for user in pair:
                    user_id = f"user_{user['firebase_uid']}"
                    user_ref = db.collection("users").document(user_id)
                    batch.update(user_ref, {"room_id": room_id})
                batch.commit()
                
                print(f"[Scheduler] Created room {room_id} for {len(pair)} users")
            
            print(f"[Scheduler] Room reset completed. Created {len(pairs)} rooms")
            
        except Exception as e:
            print(f"[Scheduler] Error during room reset: {e}")
            import traceback
            print(f"[Scheduler] Traceback: {traceback.format_exc()}")
    
    async def start(self):
        """スケジューラーを開始"""
        if self.running:
            return
        
        self.running = True
        print("[Scheduler] Room scheduler started")
        
        while self.running:
            try:
                next_reset = self.get_next_reset_time()
                now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
                sleep_seconds = (next_reset - now).total_seconds()
                
                print(f"[Scheduler] Next reset at {next_reset.strftime('%H:%M')}, sleeping for {sleep_seconds:.0f} seconds")
                
                await asyncio.sleep(sleep_seconds)
                
                if self.running:
                    await self.reset_all_rooms()
                    
            except Exception as e:
                print(f"[Scheduler] Error in scheduler loop: {e}")
                await asyncio.sleep(60)  # エラー時は1分待機
    
    def stop(self):
        """スケジューラーを停止"""
        self.running = False
        print("[Scheduler] Room scheduler stopped")

# グローバルインスタンス
room_scheduler = RoomScheduler()