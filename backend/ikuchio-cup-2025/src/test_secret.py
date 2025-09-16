#!/usr/bin/env python3
"""Secret Manager接続テスト用スクリプト"""

import sys
import os
sys.path.append('/app/src')

from gcp.secret_manager import SecretManagerUtil

def test_secret_manager():
    print("=== Secret Manager Test ===")
    try:
        print("Creating SecretManagerUtil instance...")
        util = SecretManagerUtil()
        
        print("Attempting to get secret...")
        secret = util.get_secret("88236233617", "google-vertexai-api-key")
        
        print(f"Success! Secret length: {len(secret)}")
        print(f"Secret preview: {secret[:10]}...")
        
    except Exception as e:
        print(f"Error: {type(e).__name__}: {str(e)}")
        import traceback
        print(f"Full traceback:\n{traceback.format_exc()}")

if __name__ == "__main__":
    test_secret_manager()