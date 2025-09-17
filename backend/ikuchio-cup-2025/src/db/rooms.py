import gcp.firestore
import uuid
import datetime
import random
from gcp.gemini import generate

def get_db():
    return gcp.firestore.get_firestore_client()

db = get_db()

def create_room_with_random_users():
    # ルーム未割り当てのユーザーのみ取得
    users_ref = db.collection("users")
    query = users_ref.where("room_id", "==", None).limit(10)
    users_docs = query.get()
    
    if len(users_docs) < 2:
        print(f"[Room Debug] Not enough unassigned users: {len(users_docs)}")
        return None
    
    # ランダムに2名選択
    selected_users = random.sample(users_docs, 2)
    user1_dict = selected_users[0].to_dict()
    user2_dict = selected_users[1].to_dict()
    if user1_dict is None or user2_dict is None or "firebase_uid" not in user1_dict or "firebase_uid" not in user2_dict:
        return None
    user1_id = user1_dict["firebase_uid"]
    user2_id = user2_dict["firebase_uid"]
    
    # ルーム作成
    room_id = f"room_{uuid.uuid4()}"
    room_data = {
        "id": room_id,
        "created_at": datetime.datetime.now(datetime.timezone.utc),
        "users": [f"user_{user1_id}", f"user_{user2_id}"]
    }
    
    try:
        # ルーム作成
        db.collection("rooms").document(room_id).set(room_data)
        
        # ユーザーにルームIDを割り当て
        selected_users[0].reference.update({"room_id": room_id})
        selected_users[1].reference.update({"room_id": room_id})
        
        print(f"[Room Debug] Created room {room_id} for users {user1_id} and {user2_id}")
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
    print(f"[Message Debug] Starting message processing for room {room_id}")
    print(f"[Message Debug] Original text: {original_text}")
    
    turn_id = f"turn_{uuid.uuid4()}"
    
    # AIによるテキスト処理
    try:
        print(f"[Message Debug] Calling Gemini AI for processing...")
        processed_text = generate(original_text)
        print(f"[Message Debug] Gemini processing completed")
        print(f"[Message Debug] Processed text: {processed_text}")
    except Exception as e:
        print(f"[Message Debug] AI processing failed: {e}")
        import traceback
        print(f"[Message Debug] Full traceback: {traceback.format_exc()}")
        processed_text = original_text  # フォールバック
        print(f"[Message Debug] Using fallback (original text)")
    
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
            firebase_uid = user_data.get('firebase_uid', 'unknown') if user_data else 'unknown'
            print(f"Debug: Cleared room_id for user user_{firebase_uid}")
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
        
        if user1_dict and user2_dict and "firebase_uid" in user1_dict and "firebase_uid" in user2_dict:
            user1_id = user1_dict["firebase_uid"]
            user2_id = user2_dict["firebase_uid"]
            
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
        if last_user_dict and "firebase_uid" in last_user_dict:
            user_id = last_user_dict["firebase_uid"]
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
