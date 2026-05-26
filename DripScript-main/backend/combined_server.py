#!/usr/bin/env python3
"""
DripScript backend API.
"""

import os
import sys
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from services.ai_service import RealAIService
except ImportError:
    RealAIService = None

load_dotenv()

app = Flask(__name__)
CORS(app)

ai_service = RealAIService() if RealAIService else None


@app.route('/')
def home():
    return jsonify(
        {
            "service": "DripScript API",
            "status": "ok",
            "endpoints": ["/api/health", "/api/recommendations"],
        }
    )


@app.route('/api/health')
def health():
    cohere_configured = bool(os.getenv('COHERE_API_KEY'))
    return jsonify(
        {
            "status": "healthy",
            "service": "DripScript API",
            "ai_configured": cohere_configured,
        }
    )


@app.route('/api/classify-clothing', methods=['POST'])
def classify_clothing():
    data = request.get_json(silent=True) or {}
    image = data.get('image')

    if not image or not isinstance(image, str):
        return jsonify({"error": "image (base64string) is required"}), 400

    cohere_api_key = os.getenv('COHERE_API_KEY')
    if not cohere_api_key:
        return jsonify({"error": "API key not configured"}), 503

    if not ai_service:
        return jsonify({"error": "AI service unavailable"}), 500

    result = ai_service.classify_clothing_image(image)
    if isinstance(result, dict) and result.get('error'):
        return jsonify({"error": result.get('error')}), 500

    # Return parsed JSON directly to frontend
    return jsonify(result)


@app.route('/api/recommendations', methods=['POST'])
def recommendations():
    data = request.get_json(silent=True) or {}
    wardrobe = data.get('wardrobe', [])
    occasion = data.get('occasion', 'casual')
    weather = data.get('weather', {})


    if not isinstance(wardrobe, list) or len(wardrobe) == 0:
        return jsonify({"error": "Wardrobe is required"}), 400

    cohere_api_key = os.getenv('COHERE_API_KEY')
    if not cohere_api_key:
        return jsonify({"error": "API key not configured"}), 503

    if not ai_service:
        return jsonify({"error": "AI service unavailable"}), 500

    result = ai_service.generate_outfit_recommendation(wardrobe, weather or {}, occasion)
    if isinstance(result, dict) and result.get('error'):
        return jsonify({"error": result.get('error')}), 500

    # New format: result expected to be { "outfits": [ ... ] } from Gemini
    outfits_raw = result.get('outfits', []) if isinstance(result, dict) else []
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
            }
        )

    return jsonify(
        {
            "outfits": normalized_outfits,
            "weather": weather,
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
