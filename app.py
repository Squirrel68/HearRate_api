from flask import Flask, request, jsonify
from firebase_service import get_user_heart_data
from model_service import predict_warning
from auth_service import register_user, login_user, refresh_auth_token, logout_user, get_user_profile, update_user_profile
from auth_middleware import token_required
from flask_cors import CORS

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
    profile = get_user_profile(user_id)
    
    if profile:
        response_data = {
            'user_id': user_id,
            'profile': profile
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)