import asyncio
import datetime
from db.rooms import firestore_reset_all_rooms
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
        try:
            return firestore_reset_all_rooms()
        except:
            return {"error": "Failed to reset rooms"}
    
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