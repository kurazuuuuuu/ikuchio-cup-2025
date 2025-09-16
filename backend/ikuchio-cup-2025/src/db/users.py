import gcp.firestore
import datetime

def get_db():
    return gcp.firestore.get_firestore_client()

db = get_db()

def firestore_create_user(firebase_uid: str):
    user_id = f"user_{firebase_uid}"
    
    # 既存ユーザーをチェック
    existing_user = firestore_get_user(firebase_uid)
    if existing_user:
        return existing_user
    
    # 新規ユーザー作成
    user_data = {
        "firebase_uid": firebase_uid,
        "created_at": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))),
        "room_id": None
    }

    db.collection("users").document(user_id).set(user_data)
    print(f"Debug: Created new user {user_id} without room assignment")
    return user_data

def firestore_get_user(firebase_uid: str):
    user_id = f"user_{firebase_uid}"
    user_doc = db.collection("users").document(user_id).get()
    
    if user_doc.exists:
        user_data = user_doc.to_dict()
        room_id = user_data.get('room_id', 'None') if user_data else 'None'
        print(f"Debug: Retrieved user {user_id} with room_id: {room_id}")
        return user_data
    else:
        print(f"Debug: User {user_id} not found")
        return None

def firestore_get_all_users():
    users_ref = db.collection("users")
    docs = users_ref.get()
    
    users = []
    for doc in docs:
        user_data = doc.to_dict()
        if user_data:
            users.append(user_data)
    
    return users