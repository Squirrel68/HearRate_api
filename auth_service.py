import firebase_admin
from firebase_admin import credentials, db, auth
import datetime
import jwt
import os
import hashlib
import uuid

# Secret key for JWT tokens - in production, use environment variables
JWT_SECRET_KEY = "heart-monitor-jwt-secret-key"  # Should be an environment variable in production
JWT_REFRESH_SECRET_KEY = "heart-monitor-refresh-jwt-secret-key"  # Should be an environment variable in production
ACCESS_TOKEN_EXPIRES = datetime.timedelta(hours=1)
REFRESH_TOKEN_EXPIRES = datetime.timedelta(days=30)

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(email, password, name, age=None, gender=None, height=None, weight=None):
    """Register a new user in Firebase"""
    try:
        # Check if user already exists
        users_ref = db.reference('users')
        existing_users = users_ref.order_by_child('email').equal_to(email).get()
        
        if existing_users:
            return {"success": False, "message": "Email already registered"}
        
        # Create user in Firebase Authentication
        user_id = str(uuid.uuid4())  # Generate a unique ID
        
        # Hash the password before storing
        hashed_password = hash_password(password)
        
        # Prepare user data
        user_data = {
            "user_id": user_id,
            "email": email,
            "password": hashed_password,  # Never store plain text passwords
            "name": name,
            "created_at": datetime.datetime.now().isoformat(),
            "profile": {
                "age": age if age is not None else 25,  # Default values
                "gender": gender if gender is not None else 1,
                "height": height if height is not None else 170,
                "weight": weight if weight is not None else 65,
                "smoke": 0,
                "alco": 0
            }
        }
        
        # Create user entry in the database
        users_ref.child(user_id).set(user_data)
        
        # Create tokens
        access_token = create_access_token(user_id)
        refresh_token = create_refresh_token(user_id)
        
        # Store refresh token in database
        store_refresh_token(user_id, refresh_token)
        
        return {
            "success": True,
            "message": "User registered successfully",
            "user_id": user_id,
            "access_token": access_token,
            "refresh_token": refresh_token
        }
    
    except Exception as e:
        return {"success": False, "message": f"Registration failed: {str(e)}"}

def login_user(email, password):
    """Log in a user"""
    try:
        # Hash the password for comparison
        hashed_password = hash_password(password)
        
        # Query Firebase to get user with this email
        users_ref = db.reference('users')
        users = users_ref.order_by_child('email').equal_to(email).get()
        
        if not users:
            return {"success": False, "message": "Invalid email or password"}
        
        # Check credentials
        user_id = None
        user_data = None
        
        for id, data in users.items():
            if data.get('password') == hashed_password:
                user_id = id
                user_data = data
                break
        
        if not user_id:
            return {"success": False, "message": "Invalid email or password"}
        
        # Create tokens
        access_token = create_access_token(user_id)
        refresh_token = create_refresh_token(user_id)
        
        # Store refresh token in database
        store_refresh_token(user_id, refresh_token)
        
        return {
            "success": True,
            "message": "Login successful",
            "user_id": user_id,
            "name": user_data.get('name'),
            "access_token": access_token,
            "refresh_token": refresh_token
        }
        
    except Exception as e:
        return {"success": False, "message": f"Login failed: {str(e)}"}

def refresh_auth_token(refresh_token):
    """Create a new access token using refresh token"""
    try:
        # Decode refresh token
        payload = jwt.decode(
            refresh_token, 
            JWT_REFRESH_SECRET_KEY,
            algorithms=["HS256"]
        )
        
        user_id = payload.get('sub')
        
        # Verify refresh token exists in database
        tokens_ref = db.reference(f'refresh_tokens/{user_id}')
        stored_token = tokens_ref.get()
        
        if not stored_token or stored_token != refresh_token:
            return {"success": False, "message": "Invalid refresh token"}
        
        # Create new access token
        new_access_token = create_access_token(user_id)
        
        return {
            "success": True,
            "message": "Token refreshed successfully",
            "access_token": new_access_token
        }
        
    except jwt.ExpiredSignatureError:
        return {"success": False, "message": "Refresh token expired"}
    except jwt.InvalidTokenError:
        return {"success": False, "message": "Invalid refresh token"}
    except Exception as e:
        return {"success": False, "message": f"Token refresh failed: {str(e)}"}

def logout_user(user_id):
    """Invalidate all refresh tokens for a user"""
    try:
        # Remove refresh token from database
        db.reference(f'refresh_tokens/{user_id}').delete()
        
        return {"success": True, "message": "Logged out successfully"}
    except Exception as e:
        return {"success": False, "message": f"Logout failed: {str(e)}"}

def create_access_token(user_id):
    """Create a JWT access token"""
    expires = datetime.datetime.utcnow() + ACCESS_TOKEN_EXPIRES
    
    payload = {
        "sub": user_id,
        "exp": expires,
        "type": "access"
    }
    
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")

def create_refresh_token(user_id):
    """Create a JWT refresh token"""
    expires = datetime.datetime.utcnow() + REFRESH_TOKEN_EXPIRES
    
    payload = {
        "sub": user_id,
        "exp": expires,
        "type": "refresh"
    }
    
    return jwt.encode(payload, JWT_REFRESH_SECRET_KEY, algorithm="HS256")

def store_refresh_token(user_id, refresh_token):
    """Store refresh token in database"""
    tokens_ref = db.reference(f'refresh_tokens/{user_id}')
    tokens_ref.set(refresh_token)

def verify_access_token(token):
    """Verify an access token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        
        if payload.get('type') != "access":
            return None
        
        user_id = payload.get('sub')
        return user_id
    
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def get_user_profile(user_id, include_user_data=False):
    """Get user profile data from Firebase
    
    Args:
        user_id: The user ID to retrieve profile for
        include_user_data: If True, includes the full user data (name, email)
    
    Returns:
        If include_user_data is True: dict with user data and profile
        Otherwise: just the profile dict or None if user not found
    """
    try:
        user_ref = db.reference(f'users/{user_id}')
        user_data = user_ref.get()
        
        if not user_data:
            return None
        
        if include_user_data:
            return {
                'name': user_data.get('name'),
                'email': user_data.get('email'),
                'profile': user_data.get('profile', {})
            }
        else:
            return user_data.get('profile', {})
    except Exception:
        return None

def update_user_profile(user_id, name=None, email=None, age=None, gender=None, height=None, weight=None, smoke=None, alco=None):
    """Update user profile in Firebase"""
    try:
        # Get a reference to the user
        user_ref = db.reference(f'users/{user_id}')
        user_data = user_ref.get()
        
        if not user_data:
            return {"success": False, "message": "User not found"}
        
        # Update basic info
        updates = {}
        if name is not None:
            updates['name'] = name
        if email is not None:
            # Check if email already exists for another user
            if email != user_data.get('email'):
                users_ref = db.reference('users')
                existing_users = users_ref.order_by_child('email').equal_to(email).get()
                if existing_users:
                    return {"success": False, "message": "Email already registered to another user"}
            updates['email'] = email
        
        # Update profile fields
        profile_updates = {}
        if age is not None:
            profile_updates['age'] = age
        if gender is not None:
            profile_updates['gender'] = gender
        if height is not None:
            profile_updates['height'] = height
        if weight is not None:
            profile_updates['weight'] = weight
        if smoke is not None:
            profile_updates['smoke'] = smoke
        if alco is not None:
            profile_updates['alco'] = alco
        
        # Only update profile if there are profile changes
        if profile_updates:
            updates['profile'] = {**user_data.get('profile', {}), **profile_updates}
        
        # Only perform update if there are changes
        if updates:
            user_ref.update(updates)
            
            # Get updated data
            updated_user = user_ref.get()
            
            return {
                "success": True,
                "message": "User profile updated successfully",
                "user_id": user_id,
                "name": updated_user.get('name'),
                "email": updated_user.get('email'),
                "profile": updated_user.get('profile', {})
            }
        else:
            return {
                "success": True,
                "message": "No changes made",
                "user_id": user_id,
                "name": user_data.get('name'),
                "email": user_data.get('email'),
                "profile": user_data.get('profile', {})
            }
            
    except Exception as e:
        return {"success": False, "message": f"Update failed: {str(e)}"}