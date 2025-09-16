import gcp.firestore
import uuid
import datetime
import random

db = gcp.firestore.db

def create_room_with_random_users():
    # 全ユーザーを取得
    users_ref = db.collection("users")
    users_docs = users_ref.get()
    
    if len(users_docs) < 2:
        return None
    
    # ランダムに2名選択
    selected_users = random.sample(users_docs, 2)
    user1_dict = selected_users[0].to_dict()
    user2_dict = selected_users[1].to_dict()
    if user1_dict is None or user2_dict is None or "fingerprint_id" not in user1_dict or "fingerprint_id" not in user2_dict:
        return None
    user1_id = user1_dict["fingerprint_id"]
    user2_id = user2_dict["fingerprint_id"]
    
    # ルーム作成
    room_id = f"room_{uuid.uuid4()}"
    room_data = {
        "id": room_id,
        "created_at": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))),
        "users": [f"user_{user1_id}", f"user_{user2_id}"]
    }
    
    db.collection("rooms").document(room_id).set(room_data)
    return room_data

def firestore_get_room(room_id: str):
    room_doc = db.collection("rooms").document(room_id).get()
    
    if room_doc.exists:
        return room_doc.to_dict()
    else:
        return None

def firestore_get_all_rooms():
    rooms_ref = db.collection("rooms")
    docs = rooms_ref.get()
    
    rooms = []
    for doc in docs:
        rooms.append(doc.to_dict())
    
    return rooms

def firestore_reset_all_rooms():
    # 全ルーム削除
    rooms_ref = db.collection("rooms")
    docs = rooms_ref.get()
    for doc in docs:
        doc.reference.delete()
    
    # 全ユーザーのroom_idをクリア
    users_ref = db.collection("users")
    user_docs = users_ref.get()
    for user_doc in user_docs:
        user_doc.reference.update({"room_id": None})
    
    # ユーザーをペアにしてルーム作成
    users_list = [doc for doc in user_docs]
    random.shuffle(users_list)
    
    created_rooms = []
    for i in range(0, len(users_list) - 1, 2):
        user1_dict = users_list[i].to_dict()
        user2_dict = users_list[i + 1].to_dict()
        
        if user1_dict and user2_dict and "fingerprint_id" in user1_dict and "fingerprint_id" in user2_dict:
            user1_id = user1_dict["fingerprint_id"]
            user2_id = user2_dict["fingerprint_id"]
            
            # ルーム作成
            room_id = f"room_{uuid.uuid4()}"
            room_data = {
                "id": room_id,
                "created_at": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))),
                "users": [f"user_{user1_id}", f"user_{user2_id}"]
            }
            
            db.collection("rooms").document(room_id).set(room_data)
            
            # ユーザーにroom_idを割り当て
            users_list[i].reference.update({"room_id": room_id})
            users_list[i + 1].reference.update({"room_id": room_id})
            
            created_rooms.append(room_data)
    
    return {"message": "All rooms have been reset and new rooms created", "created_rooms": len(created_rooms)}
