"""
FitCheck - Wardrobe AI Backend Server
Simple Flask API for clothing recommendations and AI processing
"""

from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'ai-ml'))

try:
    from config.config import *
    # Remove imports of JS modules (weatherService.js, environmentService.js)
    from services.ai_service import ai_service
    print("✅ Successfully imported backend modules")
    AI_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Some modules not available: {e}")
    AI_AVAILABLE = False

try:
    from clothing_ai import ClothingLabeler, OutfitRecommender
    print("✅ Successfully imported legacy AI modules")
except ImportError as e:
    print(f"⚠️ Legacy AI modules not available: {e}")

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Initialize AI components if available
if AI_AVAILABLE:
    clothing_labeler = ClothingLabeler()
    # outfit_recommender = OutfitRecommender()

@app.route('/')
def home():
    """API home page"""
    html = """
    <html>
    <head>
        <title>FitCheck - Wardrobe AI API</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto; 
                   max-width: 800px; margin: 50px auto; padding: 20px; 
                   background: #0f172a; color: #e2e8f0; }
            .header { text-align: center; margin-bottom: 40px; }
            .emoji { font-size: 48px; }
            .endpoint { background: #1e293b; padding: 15px; margin: 10px 0; 
                       border-radius: 8px; border-left: 4px solid #8b5cf6; }
            .method { background: #22d3ee; color: #0f172a; padding: 2px 8px; 
                     border-radius: 4px; font-size: 12px; font-weight: bold; }
            .status { padding: 5px 10px; border-radius: 20px; font-size: 12px; margin: 5px 0; }
            .available { background: #059669; color: white; }
            .unavailable { background: #dc2626; color: white; }
        </style>
    </head>
    <body>
        <div class="header">
            <div class="emoji">🎯</div>
            <h1>FitCheck - Wardrobe AI API</h1>
            <p>Backend services for AI-powered wardrobe management</p>
        </div>
        
        <div class="status available">✅ API Server Running</div>
        <div class="status {{ 'available' if ai_status else 'unavailable' }}">
            {{ '✅ AI Components Loaded' if ai_status else '⚠️ AI Components Not Available' }}
        </div>
        
        <h2>Available Endpoints</h2>
        
        <div class="endpoint">
            <span class="method">GET</span>
            <strong>/api/health</strong> - Server health check
        </div>
        
        <div class="endpoint">
            <span class="method">POST</span>
            <strong>/api/classify</strong> - Classify clothing from text description
            <br><small>Body: {"description": "black hoodie comfortable winter"}</small>
        </div>
        
        <div class="endpoint">
            <span class="method">GET</span>
            <strong>/api/weather</strong> - Get weather data for recommendations
        </div>
        
        <div class="endpoint">
            <span class="method">POST</span>
            <strong>/api/recommend</strong> - Get outfit recommendations
            <br><small>Body: {"wardrobe": [...], "weather": "cold", "occasion": "casual"}</small>
        </div>
        
        <p><a href="/api/health" style="color: #8b5cf6;">Test Health Endpoint</a></p>
    </body>
    </html>
    """
    return render_template_string(html, ai_status=AI_AVAILABLE)

@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'FitCheck Wardrobe AI API',
        'ai_available': AI_AVAILABLE,
        'version': '1.0.0'
    })

@app.route('/api/classify', methods=['POST'])
def classify_clothing():
    """Classify clothing from image and filename using real AI"""
    if not AI_AVAILABLE:
        return jsonify({'error': 'AI components not available'}), 503
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request data is required'}), 400
    
    filename = data.get('filename', '')
    image_data = data.get('image_data', '')
    
    try:
        result = ai_service.analyze_clothing_image(image_data, filename)
        return jsonify({
            'success': True,
            'classification': result,
            'filename': filename
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/weather')
def weather():
    """Get real weather data for outfit recommendations"""
    try:
        city = request.args.get('city', 'London')
        weather_data = ai_service.get_weather_data(city)
        return jsonify({
            'success': True,
            'weather': weather_data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/recommend', methods=['POST'])
def recommend_outfit():
    """Get AI-powered outfit recommendations"""
    if not AI_AVAILABLE:
        return jsonify({'error': 'AI components not available'}), 503
        
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request data is required'}), 400
    
    try:
        wardrobe = data.get('wardrobe', [])
        weather = data.get('weather', {})
        occasion = data.get('occasion', 'casual')
        
        # Get AI recommendation
        recommendation = ai_service.generate_outfit_recommendation(wardrobe, weather, occasion)
        
        return jsonify({
            'success': True,
            'recommendation': recommendation,
            'occasion': occasion,
            'weather': weather
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    print("🎯 Starting FitCheck - Wardrobe AI API Server...")
    print(f"🤖 AI Components: {'Available' if AI_AVAILABLE else 'Not Available'}")
    print("🌐 Server will be available at: http://localhost:5000")
    print("📚 API Documentation: http://localhost:5000")
    print("🔧 Health Check: http://localhost:5000/api/health")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True
    )