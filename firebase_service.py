import firebase_admin
from firebase_admin import credentials, db

# Khởi tạo Firebase
cred = credentials.Certificate("firebase-adminsdk.json")  # file key bạn download từ Firebase
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://heart-monitor-system-default-rtdb.asia-southeast1.firebasedatabase.app/'
})

def get_user_heart_data(user_id=None):
    if not user_id:
        user_id = 'anonymous'
        
    ref = db.reference(f'heart_data/{user_id}')
    data = ref.get()
    return data
