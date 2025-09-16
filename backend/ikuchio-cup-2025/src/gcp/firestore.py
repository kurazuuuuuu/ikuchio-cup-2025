from google.cloud import firestore
import os

DB_NAME = "ikuchio-cup-2025-dev"

# Cloud Run環境での初期化を改善
def get_firestore_client():
    try:
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'ikuchio-cup-2025')
        print(f"[Firestore] Initializing client for project: {project_id}")
        return firestore.Client(project=project_id, database=DB_NAME)
    except Exception as e:
        print(f"[Firestore] Error initializing client: {e}")
        raise e

db = get_firestore_client()