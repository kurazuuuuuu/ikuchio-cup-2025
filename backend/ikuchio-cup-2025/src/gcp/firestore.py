from google.cloud import firestore

DB_NAME = "ikuchio-cup-2025-dev"

db = firestore.Client(database=(DB_NAME))