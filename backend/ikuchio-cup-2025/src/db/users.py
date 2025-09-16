import gcp.firestore
import datetime

db = gcp.firestore.db

def firestore_create_user(fingerprint_id: str = "0000"):
    # 既存ユーザーをチェック
    existing_user = firestore_get_user(fingerprint_id)
    if existing_user:
        return existing_user  # 既存ユーザーのデータをそのまま返す
    
    # 新規ユーザー作成
    user_data = {
        "fingerprint_id": fingerprint_id,
        "created_at": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))),
        "room_id": None  # 初期状態ではルームに参加していない
    }

    db.collection("users").document().set(user_data)
    return user_data

def firestore_get_user(fingerprint_id: str = "0000"):
    users_ref = db.collection("users")
    query = users_ref.where("fingerprint_id", "==", fingerprint_id)
    docs = query.get()
    
    if docs:
        user_doc = docs[0]
        user_data = user_doc.to_dict()
        return user_data
    else:
        return None