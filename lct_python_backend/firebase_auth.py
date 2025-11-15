# Firebase configuration for backend
# This file helps manage Firebase Admin SDK initialization

import os
import json
import firebase_admin
from firebase_admin import credentials, auth
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

def get_firebase_credentials():
    """
    Get Firebase credentials from environment or service account file
    """
    # Use service account file
    service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH', 'serviceAccountKey.json')
    if os.path.exists(service_account_path):
        return credentials.Certificate(service_account_path)
    
    # gcloud
    print("Using application default credentials")
    return None

def initialize_firebase_admin():
    """
    Initialize Firebase Admin SDK
    """
    if firebase_admin._apps:
        return firebase_admin.get_app()
    
    try:
        cred = get_firebase_credentials()
        if cred:
            app = firebase_admin.initialize_app(cred)
        else:
            app = firebase_admin.initialize_app()
        
        print("Firebase Admin SDK initialized successfully")
        return app
    except Exception as e:
        print(f"Error initializing Firebase Admin SDK: {e}")
        raise

# Security scheme for Bearer token
security = HTTPBearer()

async def verify_firebase_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Verify Firebase ID token and return user information
    """
    try:
        # Extract the token from the Authorization header
        token = credentials.credentials
        
        # Verify the token with Firebase Admin SDK
        decoded_token = auth.verify_id_token(token)
        
        # Extract user information
        user_info = {
            'uid': decoded_token['uid'],
            'email': decoded_token.get('email'),
            'name': decoded_token.get('name'),
            'picture': decoded_token.get('picture'),
            'email_verified': decoded_token.get('email_verified', False)
        }
        return user_info
        
    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=401,
            detail="Authentication token has expired"
        )
    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token"
        )
    except Exception as e:
        print(f"[ERROR] Token verification failed: {e}")
        raise HTTPException(
            status_code=401,
            detail="Authentication failed"
        )

def get_user_by_email(email: str) -> dict:
    """
    Get user information by email address
    """
    try:
        user = auth.get_user_by_email(email)
        return {
            'uid': user.uid,
            'email': user.email,
            'email_verified': user.email_verified,
            'display_name': user.display_name
        }
    except auth.UserNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"User with email {email} not found"
        )
    except Exception as e:
        print(f"[ERROR] Error getting user by email: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get user information"
        )

def get_users_by_uids(uids: list) -> list:
    """
    Get user information by list of UIDs
    """
    users = []
    for uid in uids:
        try:
            user = auth.get_user(uid)
            users.append({
                'uid': user.uid,
                'email': user.email,
                'display_name': user.display_name,
                'email_verified': user.email_verified
            })
        except auth.UserNotFoundError:
            print(f"[WARNING] User with UID {uid} not found")
            continue
        except Exception as e:
            print(f"[ERROR] Error getting user {uid}: {e}")
            continue
    return users