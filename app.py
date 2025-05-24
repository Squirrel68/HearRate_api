from flask import Flask, request, jsonify
from firebase_service import get_user_heart_data, update_calories_tracking
from model_service import predict_warning
from auth_service import register_user, login_user, refresh_auth_token, logout_user, get_user_profile, update_user_profile
from auth_middleware import token_required
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Hàm tiện ích để chuẩn hóa response
def success_response(data, status_code=200):
    return jsonify({
        'statusCode': status_code,
        'data': data
    }), status_code

def error_response(error_message, status_code=400):
    return jsonify({
        'statusCode': status_code,
        'errorString': error_message
    }), status_code

# Authentication routes
@app.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Validate required fields
    if not all(k in data for k in ('email', 'password', 'name')):
        return error_response('Missing required fields', 400)
    
    # Optional profile data
    age = data.get('age')
    gender = data.get('gender')
    height = data.get('height')
    weight = data.get('weight')
    
    # Call register function
    result = register_user(data['email'], data['password'], data['name'], 
                          age=age, gender=gender, height=height, weight=weight)
    
    if result['success']:
        del result['success']  # Remove success flag as it's redundant now
        return success_response(result, 201)
    else:
        return error_response(result.get('message', 'Registration failed'), 400)

@app.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    
    # Validate required fields
    if not all(k in data for k in ('email', 'password')):
        return error_response('Missing required fields', 400)
    
    # Call login function
    result = login_user(data['email'], data['password'])
    
    if result['success']:
        del result['success']  # Remove success flag as it's redundant now
        return success_response(result, 200)
    else:
        return error_response(result.get('message', 'Login failed'), 401)

@app.route('/auth/refresh', methods=['POST'])
def refresh_token():
    data = request.get_json()
    
    # Validate required fields
    if 'refresh_token' not in data:
        return error_response('Refresh token is required', 400)
    
    # Call refresh token function
    result = refresh_auth_token(data['refresh_token'])
    
    if result['success']:
        del result['success']  # Remove success flag as it's redundant now
        return success_response(result, 200)
    else:
        return error_response(result.get('message', 'Token refresh failed'), 401)

@app.route('/auth/logout', methods=['POST'])
@token_required
def logout(user_id):
    # Call logout function
    result = logout_user(user_id)
    
    if result['success']:
        del result['success']  # Remove success flag as it's redundant now
        return success_response(result, 200)
    else:
        return error_response(result.get('message', 'Logout failed'), 500)

# Protected route for user profile
@app.route('/profile', methods=['GET'])
@token_required
def get_profile(user_id):
    # Get user profile with additional user data
    user_data = get_user_profile(user_id, include_user_data=True)
    
    if user_data:
        response_data = {
            'user_id': user_id,
            'name': user_data.get('name'),
            'email': user_data.get('email'),
            'profile': user_data.get('profile', {})
        }
        return success_response(response_data, 200)
    else:
        return error_response('Profile not found', 404)

@app.route('/profile', methods=['PUT'])
@token_required
def update_profile(user_id):
    data = request.get_json()
    
    # Extract update fields
    name = data.get('name')
    email = data.get('email')
    
    # Extract profile fields
    profile = data.get('profile', {})
    age = profile.get('age')
    gender = profile.get('gender')
    height = profile.get('height')
    weight = profile.get('weight')
    smoke = profile.get('smoke')
    alco = profile.get('alco')
    
    # Call update function
    result = update_user_profile(
        user_id, 
        name=name,
        email=email,
        age=age,
        gender=gender, 
        height=height, 
        weight=weight,
        smoke=smoke,
        alco=alco
    )
    
    if result['success']:
        del result['success']  # Remove success flag as it's redundant now
        return success_response(result, 200)
    else:
        return error_response(result.get('message', 'Update failed'), 400)

@app.route('/realtime-heart', methods=['GET'])
@token_required
def get_realtime_heart(user_id):
    # User ID is now obtained from the token
    
    # Lấy dữ liệu nhịp tim mới nhất từ Firebase
    data = get_user_heart_data(user_id)
    if not data:
        return error_response('Heart data not found', 404)

    bpm = data.get('bpm')
    spo2 = data.get('spo2')

    # Get profile from Firebase
    user_profile = get_user_profile(user_id)
    
    if not user_profile:
        # Fallback to default profile if not found
        user_profile = {
            'age': 25,
            'gender': 1,
            'height': 170,
            'weight': 65,
            'smoke': 0,
            'alco': 0
        }

    # Add heart data to profile for prediction
    user_profile['bpm'] = bpm
    user_profile['spo2'] = spo2

    # Dự đoán
    warning = predict_warning(user_profile)

    response_data = {
        'userId': user_id,
        'bpm': bpm,
        'spo2': spo2,
        'warning': warning  # 1 = bất thường, 0 = bình thường
    }

    return success_response(response_data, 200)

# Public endpoint (for anonymous users)
@app.route('/public/heart-data', methods=['GET'])
def get_public_heart_data():
    # Gets anonymous user data
    data = get_user_heart_data('anonymous')
    if not data:
        return error_response('Anonymous data not found', 404)

    bpm = data.get('bpm')
    spo2 = data.get('spo2')

    # Default profile
    user_profile = {
        'age': 25,
        'gender': 1,
        'height': 170,
        'weight': 65,
        'smoke': 0,
        'alco': 0,
        'bpm': bpm,
        'spo2': spo2
    }

    # Dự đoán
    warning = predict_warning(user_profile)

    response_data = {
        'userId': 'anonymous',
        'bpm': bpm,
        'spo2': spo2,
        'warning': warning
    }

    return success_response(response_data, 200)

@app.route('/calories', methods=['GET'])
@token_required
def calculate_calories(user_id):
    heart_data = get_user_heart_data(user_id)
    if not heart_data:
        return error_response('Heart data not found', 404)
    
    bpm = heart_data.get('bpm')
    
    # Skip calculation if heart rate is 0 (user not wearing device)
    if bpm == 0:
        return error_response('Heart rate is zero, user may not be wearing the device', 400)
    
    # Get user profile for weight, age, gender
    user_profile = get_user_profile(user_id)
    if not user_profile:
        return error_response('User profile not found', 404)
    
    weight = user_profile.get('weight', 70)  # kg
    age = user_profile.get('age', 30)  # years
    gender = user_profile.get('gender', 1)  # 1 for male, 0 for female
    height = user_profile.get('height', 170)  # cm
    
    # Calculate calories burned per minute based on gender
    # Adjust formula to be more realistic for calories burned during activity
    if gender == 1:  # Male
        # Simplified calculation focusing on heart rate over resting rate
        calories_per_minute = (0.4 * (bpm - 70) + (0.1 * weight)) / 4.184
    else:  # Female
        # Similar simplified formula for women
        calories_per_minute = (0.35 * (bpm - 70) + (0.08 * weight)) / 4.184
    
    # Ensure calories are not negative
    calories_per_minute = max(0, calories_per_minute)
    
    # Update tracking in Firebase (adding 1 minute)
    tracking_data = update_calories_tracking(user_id, calories_per_minute, 1)
    
    # Base metabolic rate (BMR) - calories burned at rest per day
    if gender == 1:  # Male
        bmr = 88.362 + (13.397 * weight) + (4.799 * height/100) - (5.677 * age)
    else:  # Female
        bmr = 447.593 + (9.247 * weight) + (3.098 * height/100) - (4.330 * age)
    
    # Calculate estimated daily calories
    # Assume user is active at current rate for 1 hour, and resting for 23 hours
    estimated_daily_calories = bmr + (calories_per_minute * 60)
    
    response_data = {
        'bpm': bpm,
        'calories_per_minute': round(calories_per_minute, 2),
        'total_calories_today': round(tracking_data.get('total_calories', 0), 2),
        'total_minutes_tracked': tracking_data.get('total_minutes', 0),
        'active_calories_per_hour': round(calories_per_minute * 60, 2),
        'bmr_calories_per_day': round(bmr, 2),
        'estimated_daily_calories': round(estimated_daily_calories, 2)
    }
    
    return success_response(response_data, 200)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)