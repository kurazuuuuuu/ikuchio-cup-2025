from google.cloud import firestore

DB_NAME = "ikuchio-cup-2025"

db = firestore.Client(database=(DB_NAME))