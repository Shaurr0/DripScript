"""
Firebase Authentication Service
Initializes firebase-admin and provides a @requires_auth decorator for Flask routes.
"""

import os
import functools
import logging

import firebase_admin
from firebase_admin import auth, credentials
from flask import request, jsonify, g

logger = logging.getLogger(__name__)

# --- Firebase Admin SDK Initialization ---
_firebase_app = None


def _init_firebase():
    global _firebase_app
    if _firebase_app is not None:
        return

    creds_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
    if not creds_path:
        logger.error(
            "FIREBASE_CREDENTIALS_PATH not set. Firebase Admin SDK not initialized."
        )
        return

    if not os.path.isabs(creds_path):
        creds_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), os.pardir, creds_path)
        )

    if not os.path.isfile(creds_path):
        logger.error("Firebase credentials file not found: %s", creds_path)
        return

    options = {}
    bucket_name = os.getenv("FIREBASE_STORAGE_BUCKET")
    if bucket_name:
        options["storageBucket"] = bucket_name
    else:
        logger.warning(
            "FIREBASE_STORAGE_BUCKET not set. Firebase Storage checks may fail."
        )

    try:
        cred = credentials.Certificate(creds_path)
        _firebase_app = firebase_admin.initialize_app(
            cred,
            options if options else None,
        )
        logger.info("Firebase Admin SDK initialized successfully")
    except Exception:
        logger.exception("Failed to initialize Firebase Admin SDK")
        _firebase_app = None
        return


def get_firestore_client():
    if _firebase_app is None:
        logger.error("Firestore client unavailable: Firebase Admin SDK not initialized.")
        return None
    try:
        from firebase_admin import firestore
        return firestore.client(app=_firebase_app)
    except Exception:
        logger.exception("Failed to initialize Firestore client")
        return None


def get_storage_bucket():
    if _firebase_app is None:
        logger.error("Storage bucket unavailable: Firebase Admin SDK not initialized.")
        return None
    try:
        from firebase_admin import storage
        return storage.bucket(app=_firebase_app)
    except Exception:
        logger.exception("Failed to initialize Firebase Storage bucket")
        return None


def verify_firebase_services():
    status = {
        "initialized": _firebase_app is not None,
        "firestore": False,
        "storage": False,
    }

    if _firebase_app is None:
        return status

    firestore_client = get_firestore_client()
    if firestore_client:
        try:
            next(firestore_client.collections(), None)
            status["firestore"] = True
        except Exception:
            logger.exception("Firestore connectivity check failed")

    storage_bucket = get_storage_bucket()
    if storage_bucket:
        try:
            status["storage"] = storage_bucket.exists()
            if not status["storage"]:
                logger.error(
                    "Firebase Storage bucket not found or access denied: %s",
                    storage_bucket.name,
                )
        except Exception:
            logger.exception("Firebase Storage connectivity check failed")

    return status


_init_firebase()


# --- Decorator ---

def requires_auth(f):
    """Flask route decorator that validates a Firebase ID token from the Authorization header."""

    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if _firebase_app is None:
            logger.error("Auth check failed: Firebase Admin SDK not initialized")
            return jsonify(
                {"error": "Authentication service unavailable. Firebase Admin SDK not initialized."}
            ), 503

        auth_header = request.headers.get("Authorization", "")

        if not auth_header:
            logger.warning("Auth check failed: no Authorization header present")
            return jsonify({"error": "Unauthorized. No token provided."}), 401

        if not auth_header.startswith("Bearer "):
            logger.warning("Auth check failed: malformed Authorization header (missing 'Bearer ' prefix)")
            return jsonify({"error": "Unauthorized. Malformed token format."}), 401

        token = auth_header.split("Bearer ", 1)[1]

        if not token:
            logger.warning("Auth check failed: empty token after 'Bearer ' prefix")
            return jsonify({"error": "Unauthorized. Empty token."}), 401

        try:
            decoded_token = auth.verify_id_token(token)
        except auth.ExpiredIdTokenError:
            logger.warning("Auth check failed: token expired")
            return jsonify({"error": "Unauthorized. Token expired. Please log in again."}), 401
        except auth.RevokedIdTokenError:
            logger.warning("Auth check failed: token revoked")
            return jsonify({"error": "Unauthorized. Token revoked. Please log in again."}), 401
        except auth.InvalidIdTokenError as e:
            logger.warning("Auth check failed: invalid token - %s", e)
            return jsonify({"error": "Unauthorized. Invalid token."}), 401
        except Exception as e:
            logger.warning("Auth check failed: unexpected error - %s", e)
            return jsonify({"error": "Unauthorized. Token verification failed."}), 401

        g.user_id = decoded_token["uid"]
        return f(*args, **kwargs)

    return decorated
