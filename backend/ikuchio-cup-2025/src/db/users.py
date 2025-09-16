import gcp.firestore
import datetime

db = gcp.firestore.db

def firestore_create_user(fingerprint_id: str = "0000"):
    # 既存ユーザーをチェック
    existing_user = firestore_get_user(fingerprint_id)
    if existing_user:
        return existing_user  # 既存ユーザーのデータをそのまま返す
    
    # 新規ユーザー作成（ルームはリセット時にのみ割り当て）
    user_data = {
        "fingerprint_id": fingerprint_id,
        "created_at": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))),
        "room_id": None  # 新規ユーザーはリセットまでルームなし
    }

    db.collection("users").document().set(user_data)
    print(f"Debug: Created new user user_{fingerprint_id} without room assignment")
    return user_data

def firestore_get_user(fingerprint_id: str = "0000"):
    users_ref = db.collection("users")
    query = users_ref.where("fingerprint_id", "==", fingerprint_id)
    docs = query.get()
    
    if docs:
        user_doc = docs[0]
        user_data = user_doc.to_dict()
        print(f"Debug: Retrieved user user_{fingerprint_id} with room_id: {user_data.get('room_id', 'None')}")
        return user_data
    else:
        print(f"Debug: User user_{fingerprint_id} not found")
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