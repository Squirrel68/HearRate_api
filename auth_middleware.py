from functools import wraps
from flask import request, jsonify
from auth_service import verify_access_token

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check if the 'Authorization' header exists and has the right format
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({
                'success': False,
                'message': 'Authentication token is missing'
            }), 401
        
        # Verify the token
        user_id = verify_access_token(token)
        if not user_id:
            return jsonify({
                'success': False,
                'message': 'Invalid or expired token'
            }), 401
        
        # Add the user_id to kwargs so that the decorated function can access it
        kwargs['user_id'] = user_id
        return f(*args, **kwargs)
    
    return decorated