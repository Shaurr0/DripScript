#!/usr/bin/env python3
"""
FitCheck - AI-Powered Backend Server with Gemini Integration
"""

from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
import os
from dotenv import load_dotenv
import sys

# Add the current directory to the path so we can import our services
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.ai_service import RealAIService

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Initialize AI service
ai_service = RealAIService()

@app.route('/')
def home():
    """API home page"""
    gemini_status = "✅ Connected" if ai_service.gemini_api_key else "❌ Not configured"
    weather_status = "✅ Connected" if ai_service.openweather_api_key else "❌ Not configured"
    
    html = f"""
    <html>
    <head>
        <title>FitCheck - AI Wardrobe API</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto; 
                   max-width: 800px; margin: 50px auto; padding: 20px; 
                   background: #0f172a; color: #e2e8f0; }}
            .header {{ text-align: center; margin-bottom: 40px; }}
            .emoji {{ font-size: 48px; }}
            .endpoint {{ background: #1e293b; padding: 15px; margin: 10px 0; 
                       border-radius: 8px; border-left: 4px solid #8b5cf6; }}
            .method {{ background: #22d3ee; color: #0f172a; padding: 2px 8px; 
                     border-radius: 4px; font-size: 12px; font-weight: bold; }}
            .status {{ padding: 5px 10px; border-radius: 20px; font-size: 12px; margin: 5px 0; }}
            .available {{ background: #059669; color: white; }}
            .ai {{ background: #8b5cf6; color: white; }}
            .warning {{ background: #f59e0b; color: white; }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="emoji">🤖</div>
            <h1>FitCheck - AI Wardrobe API</h1>
            <p>Powered by Google Gemini AI</p>
        </div>
        
        <div class="status available">✅ AI Server Running</div>
        <div class="status ai">🤖 Gemini API: {gemini_status}</div>
        <div class="status ai">🌤️ Weather API: {weather_status}</div>
        
        <h2>AI Endpoints</h2>
        
        <div class="endpoint">
            <span class="method">GET</span>
            <strong>/api/health</strong> - Server health check with AI status
        </div>
        
        <div class="endpoint">
            <span class="method">POST</span>
            <strong>/api/ai/analyze</strong> - AI-powered clothing analysis
            <br><small>Body: {{"filename": "blue-jeans.jpg", "image_data": ""}}</small>
        </div>
        
        <div class="endpoint">
            <span class="method">POST</span>
            <strong>/api/ai/recommend</strong> - AI outfit recommendations
            <br><small>Body: {{"wardrobe": [...], "weather": {{}}, "occasion": "casual"}}</small>
        </div>
        
        <div class="endpoint">
            <span class="method">GET</span>
            <strong>/api/weather</strong> - Real weather data
            <br><small>Query: ?city=London</small>
        </div>
        
        <p><a href="/api/health" style="color: #8b5cf6;">Test Health Endpoint</a></p>
        <p><a href="/api/weather?city=London" style="color: #8b5cf6;">Test Weather Endpoint</a></p>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/api/health')
def health():
    """Health check endpoint with AI status"""
    return jsonify({
        'status': 'healthy',
        'service': 'FitCheck AI Wardrobe API',
        'mode': 'production',
        'ai': {
            'gemini_available': bool(ai_service.gemini_api_key),
            'weather_available': bool(ai_service.openweather_api_key),
            'model': ai_service.model_name
        },
        'version': '2.0.0-ai'
    })

@app.route('/api/ai/analyze', methods=['POST'])
def ai_analyze_clothing():
    """AI-powered clothing analysis using Gemini"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        filename = data.get('filename', '')
        image_data = data.get('image_data', '')
        
        if not filename:
            return jsonify({'error': 'Filename is required'}), 400
        
        # Use AI service to analyze clothing
        result = ai_service.analyze_clothing_image(image_data, filename)
        
        return jsonify({
            'success': True,
            'analysis': result,
            'filename': filename,
            'ai_powered': True,
            'model': ai_service.model_name
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Analysis failed: {str(e)}',
            'success': False
        }), 500

@app.route('/api/ai/recommend', methods=['POST'])
def ai_recommend_outfit():
    """AI-powered outfit recommendations using Gemini"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        wardrobe = data.get('wardrobe', [])
        weather = data.get('weather', {'temperature': 20, 'condition': 'clear'})
        occasion = data.get('occasion', 'casual')
        
        if not wardrobe:
            return jsonify({'error': 'Wardrobe items are required'}), 400
        
        # Use AI service to generate recommendations
        result = ai_service.generate_outfit_recommendation(wardrobe, weather, occasion)
        
        return jsonify({
            'success': True,
            'recommendation': result,
            'input': {
                'wardrobe_items': len(wardrobe),
                'weather': weather,
                'occasion': occasion
            },
            'ai_powered': True,
            'model': ai_service.model_name
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Recommendation failed: {str(e)}',
            'success': False
        }), 500

@app.route('/api/weather')
def weather():
    """Real weather data (or mock if API not available)"""
    try:
        city = request.args.get('city', 'London')
        
        # Get weather data using AI service
        weather_data = ai_service.get_weather_data(city)
        
        return jsonify({
            'success': True,
            'weather': weather_data,
            'city': city,
            'source': 'OpenWeatherMap' if ai_service.openweather_api_key else 'Mock'
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Weather data failed: {str(e)}',
            'success': False
        }), 500

@app.route('/api/test/gemini', methods=['POST'])
def test_gemini():
    """Test Gemini API directly"""
    try:
        data = request.get_json()
        prompt = data.get('prompt', 'Hello, are you working?')
        
        result = ai_service._query_gemini(prompt)
        
        return jsonify({
            'success': bool(result),
            'response': result,
            'model': ai_service.model_name,
            'api_key_present': bool(ai_service.gemini_api_key)
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Gemini test failed: {str(e)}',
            'success': False
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    print("🤖 Starting FitCheck - AI-Powered Server...")
    print(f"🎯 Gemini API: {'✅ Connected' if ai_service.gemini_api_key else '❌ Not configured'}")
    print(f"🌤️ Weather API: {'✅ Connected' if ai_service.openweather_api_key else '❌ Not configured'}")
    print("🌐 Server will be available at: http://localhost:5001")
    print("📚 API Documentation: http://localhost:5001")
    print("🔧 Health Check: http://localhost:5001/api/health")
    
    app.run(
        host='0.0.0.0',
        port=5001,  # Different port to avoid conflict
        debug=True,
        threaded=True
    )