import gcp.firestore
import datetime

db = gcp.firestore.db

def firestore_create_user(fingerprint_id: str = "0000") :
    user_data = {
        "fingerprint_id": fingerprint_id,
        "created_at": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))),
    }

    db.collection("users").document().set(user_data)
    print(f"User #{fingerprint_id} created successfully!") #debug