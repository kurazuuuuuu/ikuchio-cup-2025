import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from gcp.firestore import db

db = db

def test_firestore():
    users = db.collection('users').get()
    print(users)

if __name__ == '__main__':
    test_firestore()