import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime, date

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

def update_calories_tracking(user_id, calories_per_minute, minutes):
    """Update user's calorie tracking data
    
    Args:
        user_id: The user ID to update
        calories_per_minute: Calories burned in this minute
        minutes: Number of minutes to add (typically 1)
    
    Returns:
        dict with updated tracking information
    """
    # Get today's date as string (YYYY-MM-DD)
    today = date.today().isoformat()
    
    # Reference to user's calorie tracking data
    ref = db.reference(f'calories_tracking/{user_id}')
    tracking_data = ref.get() or {}
    
    # Check if we need to reset (new day)
    last_tracked_date = tracking_data.get('date')
    if not last_tracked_date or last_tracked_date != today:
        # Reset for new day
        tracking_data = {
            'date': today,
            'total_calories': 0,
            'total_minutes': 0
        }
    
    # Update tracking data
    new_total_calories = tracking_data.get('total_calories', 0) + calories_per_minute
    new_total_minutes = tracking_data.get('total_minutes', 0) + minutes
    
    # Write updated data back to Firebase
    updated_data = {
        'date': today,
        'total_calories': new_total_calories,
        'total_minutes': new_total_minutes,
        'last_updated': datetime.now().isoformat()
    }
    ref.set(updated_data)
    
    return updated_data