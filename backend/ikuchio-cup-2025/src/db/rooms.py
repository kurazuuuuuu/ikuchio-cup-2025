import gcp.firestore
import uuid
import datetime
import random

db = gcp.firestore.db

def create_room_with_random_users():
    # 全ユーザーを取得（効率化のため制限付き）
    users_ref = db.collection("users")
    users_docs = users_ref.limit(10).get()  # 2人必要だが余裕を持って10人取得
    
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
        "created_at": datetime.datetime.now(datetime.timezone.utc),
        "users": [f"user_{user1_id}", f"user_{user2_id}"]
    }
    
    try:
        db.collection("rooms").document(room_id).set(room_data)
        return room_data
    except Exception as e:
        print(f"Error creating room: {e}")
        return None

def firestore_get_room(room_id: str):
    room_doc = db.collection("rooms").document(room_id).get()
    
    if room_doc.exists:
        return room_doc.to_dict()
    else:
        return None

def firestore_get_all_rooms():
    rooms_ref = db.collection("rooms")
    docs = rooms_ref.get()
    
    return [doc.to_dict() for doc in docs if doc.to_dict()]

def firestore_send_message(room_id: str, sender_id: str, original_text: str):
    turn_id = f"turn_{uuid.uuid4()}"
    processed_text = original_text  # 現在は元のテキストをそのまま使用
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    
    turn_data = {
        "id": turn_id,
        "room_id": room_id,
        "original_sender_id": sender_id,
        "original_text": original_text,
        "processed_text": processed_text,
        "created_at": now.isoformat(),
        "processed_at": now.isoformat()
    }
    
    try:
        db.collection("turns").document(turn_id).set(turn_data)
        return turn_data
    except Exception as e:
        print(f"Error sending message: {e}")
        return None

def firestore_get_messages(room_id: str):
    turns_ref = db.collection("turns")
    query = turns_ref.where("room_id", "==", room_id).limit(100)
    docs = query.get()
    
    messages = []
    for doc in docs:
        data = doc.to_dict()
        if data:
            # created_atを文字列に変換
            if 'created_at' in data and hasattr(data['created_at'], 'isoformat'):
                data['created_at'] = data['created_at'].isoformat()
            if 'processed_at' in data and hasattr(data['processed_at'], 'isoformat'):
                data['processed_at'] = data['processed_at'].isoformat()
            messages.append(data)
    
    # ソート処理
    try:
        messages.sort(key=lambda x: x.get('created_at', ''))
    except (TypeError, ValueError, KeyError) as e:
        print(f"Warning: Failed to sort messages: {e}")
        # ソートに失敗した場合はそのまま返す
    
    return messages

def _clear_all_data():
    """Delete all rooms and messages from database"""
    # 全ルーム削除
    rooms_ref = db.collection("rooms")
    docs = rooms_ref.get()
    for doc in docs:
        doc.reference.delete()
    
    # 全メッセージ削除
    turns_ref = db.collection("turns")
    turn_docs = turns_ref.get()
    for doc in turn_docs:
        doc.reference.delete()

def _clear_user_room_assignments():
    """Clear room_id from all users and return user documents"""
    users_ref = db.collection("users")
    user_docs = users_ref.get()
    for user_doc in user_docs:
        try:
            user_doc.reference.update({"room_id": None})
            user_data = user_doc.to_dict()
            fingerprint_id = user_data.get('fingerprint_id', 'unknown') if user_data else 'unknown'
            print(f"Debug: Cleared room_id for user user_{fingerprint_id}")
        except Exception as e:
            print(f"Debug: Failed to clear room_id: {e}")
    return user_docs

def _create_pair_rooms(users_list):
    """Create rooms for user pairs"""
    created_rooms = []
    i = 0
    while i < len(users_list) - 1:
        user1_dict = users_list[i].to_dict()
        user2_dict = users_list[i + 1].to_dict()
        
        if user1_dict and user2_dict and "fingerprint_id" in user1_dict and "fingerprint_id" in user2_dict:
            user1_id = user1_dict["fingerprint_id"]
            user2_id = user2_dict["fingerprint_id"]
            
            room_id = f"room_{uuid.uuid4()}"
            room_data = {
                "id": room_id,
                "created_at": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))),
                "users": [f"user_{user1_id}", f"user_{user2_id}"]
            }
            
            try:
                db.collection("rooms").document(room_id).set(room_data)
            except Exception as e:
                print(f"Error creating pair room: {e}")
                continue
            
            try:
                users_list[i].reference.update({"room_id": room_id})
                users_list[i + 1].reference.update({"room_id": room_id})
                print(f"Debug: Assigned room {room_id} to users user_{user1_id} and user_{user2_id}")
            except Exception as e:
                print(f"Debug: Failed to assign room_id: {e}")
            
            created_rooms.append(room_data)
        
        i += 2
    return created_rooms

def _handle_odd_user(users_list):
    """Handle the last user if odd number of users - leave without room"""
    if len(users_list) % 2 == 1:
        last_user_dict = users_list[-1].to_dict()
        if last_user_dict and "fingerprint_id" in last_user_dict:
            user_id = last_user_dict["fingerprint_id"]
            print(f"Debug: User user_{user_id} left without room assignment (odd number)")
    return None

def firestore_reset_all_rooms():
    """Reset all rooms and create new room assignments"""
    _clear_all_data()
    user_docs = _clear_user_room_assignments()
    
    print(f"Debug: Found {len(user_docs)} users for room creation")
    
    if len(user_docs) < 2:
        return {"message": "Not enough users to create rooms", "created_rooms": 0}
    
    users_list = [doc for doc in user_docs]
    random.shuffle(users_list)
    
    created_rooms = _create_pair_rooms(users_list)
    _handle_odd_user(users_list)
    
    return {"message": "All rooms have been reset and new rooms created", "created_rooms": len(created_rooms)}
