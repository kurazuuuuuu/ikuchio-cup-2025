from google.cloud import firestore
import os

# Cloud Run環境での初期化を改善
def get_firestore_client():
    try:
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'ikuchio-cup-2025')
        database_id = 'ikuchio-cup-2025-dev'
        print(f"[Firestore] Initializing client for project: {project_id}, database: {database_id}")
        
        # 指定したデータベースを使用
        client = firestore.Client(project=project_id, database=database_id)
        print(f"[Firestore] Client initialized successfully")
        return client
    except Exception as e:
        print(f"[Firestore] Error initializing client: {e}")
        import traceback
        print(f"[Firestore] Traceback: {traceback.format_exc()}")
        raise e

db = get_firestore_client()