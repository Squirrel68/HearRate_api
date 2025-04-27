from flask import Flask, request, jsonify
from firebase_service import get_user_heart_data
from model_service import predict_warning
from auth_service import register_user, login_user, refresh_auth_token, logout_user, get_user_profile
from auth_middleware import token_required
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Authentication routes
@app.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Validate required fields
    if not all(k in data for k in ('email', 'password', 'name')):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    
    # Optional profile data
    age = data.get('age')
    gender = data.get('gender')
    height = data.get('height')
    weight = data.get('weight')
    
    # Call register function
    result = register_user(data['email'], data['password'], data['name'], 
                          age=age, gender=gender, height=height, weight=weight)
    
    if result['success']:
        return jsonify(result), 201
    else:
        return jsonify(result), 400

@app.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    
    # Validate required fields
    if not all(k in data for k in ('email', 'password')):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    
    # Call login function
    result = login_user(data['email'], data['password'])
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 401

@app.route('/auth/refresh', methods=['POST'])
def refresh_token():
    data = request.get_json()
    
    # Validate required fields
    if 'refresh_token' not in data:
        return jsonify({'success': False, 'message': 'Refresh token is required'}), 400
    
    # Call refresh token function
    result = refresh_auth_token(data['refresh_token'])
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 401

@app.route('/auth/logout', methods=['POST'])
@token_required
def logout(user_id):
    # Call logout function
    result = logout_user(user_id)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 500

# Protected route for user profile
@app.route('/profile', methods=['GET'])
@token_required
def get_profile(user_id):
    profile = get_user_profile(user_id)
    
    if profile:
        return jsonify({
            'success': True,
            'user_id': user_id,
            'profile': profile
        }), 200
    else:
        return jsonify({
            'success': False,
            'message': 'Profile not found'
        }), 404

@app.route('/realtime-heart', methods=['GET'])
@token_required
def get_realtime_heart(user_id):
    # User ID is now obtained from the token
    
    # Lấy dữ liệu nhịp tim mới nhất từ Firebase
    data = get_user_heart_data(user_id)
    if not data:
        return jsonify({'success': False, 'error': 'Heart data not found'}), 404

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

    response = {
        'success': True,
        'userId': user_id,
        'bpm': bpm,
        'spo2': spo2,
        'warning': warning  # 1 = bất thường, 0 = bình thường
    }

    return jsonify(response)

# Public endpoint (for anonymous users)
@app.route('/public/heart-data', methods=['GET'])
def get_public_heart_data():
    # Gets anonymous user data
    data = get_user_heart_data('anonymous')
    if not data:
        return jsonify({'success': False, 'error': 'Anonymous data not found'}), 404

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

    response = {
        'success': True,
        'userId': 'anonymous',
        'bpm': bpm,
        'spo2': spo2,
        'warning': warning
    }

    return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
