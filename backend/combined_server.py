#!/usr/bin/env python3
"""
DripScript backend API.
"""

import os
import sys
import base64
import tempfile
import functools
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

try:
    from services.ai_service import RealAIService, analyze_clothing, classify_with_fashion_model
except ImportError:
    RealAIService = None
    analyze_clothing = None
    classify_with_fashion_model = None

try:
    from services import fashionclip_service
except ImportError:
    fashionclip_service = None

try:
    from services.auth_service import requires_auth
except ImportError:
    requires_auth = None

logger = logging.getLogger(__name__)

if requires_auth is None:
    def requires_auth(f):
        @functools.wraps(f)
        def decorated(*args, **kwargs):
            logger.error("Authentication service unavailable. Firebase Admin SDK not loaded.")
            return jsonify(
                {
                    "error": "Authentication service unavailable. Install firebase-admin and set FIREBASE_CREDENTIALS_PATH."
                }
            ), 503

        return decorated

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ai_service = RealAIService() if RealAIService else None


def _allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    """Serve uploaded images as static files."""
    from flask import send_from_directory
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route('/api/upload-image', methods=['POST'])
@requires_auth
def upload_image():
    """
    Upload a clothing image to local storage.
    Accepts multipart/form-data with 'file' and 'userId' fields.
    Returns the public URL for the stored image.
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file provided. Use 'file' field in multipart form."}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    if not _allowed_file(file.filename):
        return jsonify({"error": f"File type not allowed. Use: {', '.join(ALLOWED_EXTENSIONS)}"}), 400

    user_id = request.form.get('userId', 'anonymous')
    safe_name = secure_filename(file.filename) or 'upload.jpg'
    timestamp = int(__import__('time').time() * 1000)
    stored_name = f"{user_id}_{timestamp}_{safe_name}"

    # Create user subdirectory
    user_dir = os.path.join(UPLOAD_FOLDER, user_id)
    os.makedirs(user_dir, exist_ok=True)

    filepath = os.path.join(user_dir, f"{timestamp}_{safe_name}")
    file.save(filepath)

    # Build the public URL relative to the backend
    relative_path = f"{user_id}/{timestamp}_{safe_name}"
    logger.info("[upload-image] Saved: %s (%d bytes)", filepath, os.path.getsize(filepath))

    return jsonify({
        "url": f"/uploads/{relative_path}",
        "path": relative_path,
        "filename": safe_name,
    })


@app.route('/')
def home():
    return jsonify(
        {
            "service": "DripScript API",
            "status": "ok",
            "endpoints": [
                "/api/health",
                "/api/recommendations",
                "/api/classify-clothing",
                "/api/suggest-clothing",
                "/api/upload-clothing",
            ],
        }
    )


@app.route('/api/health')
def health():
    cohere_configured = bool(os.getenv('COHERE_API_KEY'))
    blip_available = analyze_clothing is not None
    fashion_classifier_available = classify_with_fashion_model is not None
    fashionclip_available = fashionclip_service is not None and fashionclip_service.is_available()
    return jsonify(
        {
            "status": "healthy",
            "service": "DripScript API",
            "ai_configured": cohere_configured,
            "blip_available": blip_available,
            "fashion_classifier_available": fashion_classifier_available,
            "fashionclip_available": fashionclip_available,
        }
    )


@app.route('/api/classify-clothing', methods=['POST'])
@requires_auth
def classify_clothing():
    data = request.get_json(silent=True) or {}
    image = data.get('image')
    filename = data.get('filename', '')

    if not image or not isinstance(image, str):
        return jsonify({"error": "image (base64string) is required"}), 400

    if len(image) > 10_000_000:
        return jsonify({"error": "Image too large. Maximum 10MB base64 allowed."}), 413

    cohere_api_key = os.getenv('COHERE_API_KEY')
    if not cohere_api_key and not analyze_clothing:
        return jsonify({"error": "No AI service available"}), 503

    if not ai_service:
        return jsonify({"error": "AI service unavailable"}), 500

    logger.info("=== classify-clothing request ===")
    logger.info("Filename: %s", filename)

    # Decode base64 to a temp file so BLIP can process it
    image_path = None
    try:
        image_bytes = base64.b64decode(image)
        with tempfile.NamedTemporaryFile(suffix='.jpg', dir=UPLOAD_FOLDER, delete=False) as tmp:
            tmp.write(image_bytes)
            image_path = tmp.name
        logger.info("Temp image saved: %s (%d bytes)", image_path, len(image_bytes))
    except Exception as e:
        logger.error("Failed to decode base64 image: %s", e)
        image_path = None

    try:
        result = ai_service.classify_clothing_image(image, image_path=image_path, filename=filename)
        logger.info("=== classify-clothing result ===")
        logger.info("Name: %s | Category: %s | Color: %s | Vibe: %s | Tags: %s",
                    result.get('name'), result.get('category'), result.get('color'),
                    result.get('vibe'), result.get('tags'))
        if isinstance(result, dict) and result.get('error'):
            return jsonify({"error": result.get('error')}), 500
        return jsonify(result)
    finally:
        if image_path and os.path.exists(image_path):
            os.remove(image_path)


@app.route('/api/suggest-clothing', methods=['POST'])
@requires_auth
def suggest_clothing():
    data = request.get_json(silent=True) or {}
    image = data.get('image')
    filename = data.get('filename', '')

    if not image or not isinstance(image, str):
        return jsonify({"error": "image (base64string) is required"}), 400

    if len(image) > 10_000_000:
        return jsonify({"error": "Image too large. Maximum 10MB base64 allowed."}), 413

    if not ai_service:
        return jsonify({"error": "AI service unavailable"}), 500

    image_path = None
    try:
        image_bytes = base64.b64decode(image)
        with tempfile.NamedTemporaryFile(suffix='.jpg', dir=UPLOAD_FOLDER, delete=False) as tmp:
            tmp.write(image_bytes)
            image_path = tmp.name
        logger.info("[suggest-clothing] Temp image saved: %s (%d bytes)", image_path, len(image_bytes))
    except Exception as e:
        logger.error("[suggest-clothing] Failed to decode base64 image: %s", e)
        image_path = None

    try:
        result = ai_service.suggest_clothing_lightweight(image_path=image_path, filename=filename)
        return jsonify(result)
    finally:
        if image_path and os.path.exists(image_path):
            os.remove(image_path)


@app.route('/api/upload-clothing', methods=['POST'])
@requires_auth
def upload_clothing():
    """
    Upload a clothing image file for BLIP-based analysis.
    Accepts multipart/form-data with a 'file' field.
    Returns extracted clothing attributes.
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file provided. Use 'file' field in multipart form."}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    if not _allowed_file(file.filename):
        return jsonify({"error": f"File type not allowed. Use: {', '.join(ALLOWED_EXTENSIONS)}"}), 400

    if not analyze_clothing:
        return jsonify({"error": "BLIP service unavailable"}), 503

    # Save uploaded file temporarily
    filename = secure_filename(file.filename) or 'upload.jpg'
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    try:
        blip_result = analyze_clothing(filepath)

        if blip_result.get("error"):
            return jsonify({"error": blip_result["error"]}), 500

        # If Cohere is available, enrich with AI classification
        if ai_service and os.getenv('COHERE_API_KEY'):
            enriched = ai_service.classify_clothing_image("", image_path=filepath, filename=filename)
            enriched["blip_raw"] = blip_result
            return jsonify(enriched)

        # Return BLIP-only result
        return jsonify({
            "name": blip_result["caption"].title() if blip_result["caption"] else filename,
            "category": blip_result["category"] if blip_result["category"] != "unknown" else "tops",
            "color": blip_result["color"] if blip_result["color"] != "unknown" else "gray",
            "pattern": blip_result["pattern"],
            "sleeve_length": blip_result["sleeve_length"],
            "vibe": "casual",
            "tags": [blip_result["pattern"], blip_result["sleeve_length"], "ai-detected"],
            "blip_caption": blip_result["caption"],
        })
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)


@app.route('/api/recommendations', methods=['POST'])
@requires_auth
def recommendations():
    data = request.get_json(silent=True) or {}
    wardrobe = data.get('wardrobe', [])
    occasion = data.get('occasion', 'casual')
    weather = data.get('weather', {})
    saved_outfits = data.get('saved_outfits', [])


    if not isinstance(wardrobe, list) or len(wardrobe) == 0:
        return jsonify({"error": "Wardrobe is required"}), 400

    cohere_api_key = os.getenv('COHERE_API_KEY')
    if not cohere_api_key:
        return jsonify({"error": "API key not configured"}), 503

    if not ai_service:
        return jsonify({"error": "AI service unavailable"}), 500

    result = ai_service.generate_outfit_recommendation(wardrobe, weather or {}, occasion, saved_outfits)
    if isinstance(result, dict) and result.get('error'):
        return jsonify({
            "error": result.get('error'),
            "warnings": result.get('warnings', []),
        }), 500

    # New format: result expected to be { "outfits": [ ... ] } from Gemini
    outfits_raw = result.get('outfits', []) if isinstance(result, dict) else []
    warnings = result.get('warnings', []) if isinstance(result, dict) else []
    normalized_outfits = []

    for idx, outfit in enumerate(outfits_raw or []):
        if not isinstance(outfit, dict):
            continue

        normalized_outfits.append(
            {
                "id": str(os.urandom(4).hex()),
                "occasion": occasion,
                "items": (outfit.get('items') or []) if isinstance(outfit.get('items'), list) else [],
                "styling_tip": outfit.get('styling_tip', ''),
                "color_story": outfit.get('color_story', ''),
                "why_it_works": outfit.get('why_it_works', ''),
                "fashionclip_score": outfit.get('fashionclip_score'),
            }
        )

    return jsonify(
        {
            "outfits": normalized_outfits,
            "weather": weather,
            "warnings": warnings,
        }
    )



@app.errorhandler(404)
def not_found(_error):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(_error):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True, threaded=True)
