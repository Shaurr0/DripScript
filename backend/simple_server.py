"""
FitCheck - Simple Backend Server
Lightweight Flask API that works without heavy AI dependencies
"""

from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
import os
from dotenv import load_dotenv
import random

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

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
            .demo { background: #f59e0b; color: white; }
        </style>
    </head>
    <body>
        <div class="header">
            <div class="emoji">🎯</div>
            <h1>FitCheck - Wardrobe AI API</h1>
            <p>Backend services for AI-powered wardrobe management</p>
        </div>
        
        <div class="status available">✅ API Server Running</div>
        <div class="status demo">🎭 Demo Mode - Mock AI Responses</div>
        
        <h2>Available Endpoints</h2>
        
        <div class="endpoint">
            <span class="method">GET</span>
            <strong>/api/health</strong> - Server health check
        </div>
        
        <div class="endpoint">
            <span class="method">POST</span>
            <strong>/api/classify</strong> - Classify clothing from description
            <br><small>Body: {"description": "black hoodie comfortable winter"}</small>
        </div>
        
        <div class="endpoint">
            <span class="method">GET</span>
            <strong>/api/weather</strong> - Get weather data
            <br><small>Query: ?city=London</small>
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
    return render_template_string(html)

@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'FitCheck Wardrobe AI API',
        'mode': 'demo',
        'ai_available': False,
        'version': '1.0.0-demo'
    })

@app.route('/api/classify', methods=['POST'])
def classify_clothing():
    """Mock clothing classification"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request data is required'}), 400
    
    description = data.get('description', '')
    filename = data.get('filename', '')
    
    # Mock classification based on keywords
    mock_classifications = {
        'hoodie': {'type': 'hoodie', 'category': 'tops', 'warmth': 'warm', 'style': 'casual'},
        'shirt': {'type': 'shirt', 'category': 'tops', 'warmth': 'light', 'style': 'casual'},
        'jeans': {'type': 'jeans', 'category': 'bottoms', 'warmth': 'medium', 'style': 'casual'},
        'dress': {'type': 'dress', 'category': 'dresses', 'warmth': 'light', 'style': 'formal'},
        'jacket': {'type': 'jacket', 'category': 'outerwear', 'warmth': 'warm', 'style': 'casual'},
        'coat': {'type': 'coat', 'category': 'outerwear', 'warmth': 'very_warm', 'style': 'formal'},
        'sneakers': {'type': 'sneakers', 'category': 'shoes', 'warmth': 'medium', 'style': 'casual'},
        'boots': {'type': 'boots', 'category': 'shoes', 'warmth': 'warm', 'style': 'casual'}
    }
    
    # Find matching classification
    classification = {'type': 'unknown', 'category': 'misc', 'warmth': 'medium', 'style': 'casual'}
    for keyword, classif in mock_classifications.items():
        if keyword.lower() in description.lower():
            classification = classif
            break
    
    return jsonify({
        'success': True,
        'classification': classification,
        'description': description,
        'filename': filename,
        'confidence': round(random.uniform(0.7, 0.95), 2),
        'note': 'Mock classification for demo'
    })

@app.route('/api/weather')
def weather():
    """Mock weather data"""
    city = request.args.get('city', 'London')
    
    # Mock weather data
    weather_conditions = [
        {'temp': 15, 'condition': 'cloudy', 'humidity': 65, 'description': 'Cloudy with chance of rain'},
        {'temp': 22, 'condition': 'sunny', 'humidity': 45, 'description': 'Sunny and warm'},
        {'temp': 8, 'condition': 'cold', 'humidity': 70, 'description': 'Cold and windy'},
        {'temp': 28, 'condition': 'hot', 'humidity': 30, 'description': 'Hot and dry'}
    ]
    
    mock_weather = random.choice(weather_conditions)
    
    return jsonify({
        'success': True,
        'weather': {
            'city': city,
            'temperature': mock_weather['temp'],
            'condition': mock_weather['condition'],
            'humidity': mock_weather['humidity'],
            'description': mock_weather['description']
        },
        'note': 'Mock weather data for demo'
    })

@app.route('/api/recommend', methods=['POST'])
def recommend_outfit():
    """Mock outfit recommendations"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request data is required'}), 400
    
    wardrobe = data.get('wardrobe', [])
    weather = data.get('weather', {})
    occasion = data.get('occasion', 'casual')
    
    # Mock recommendations based on occasion and weather
    recommendations = {
        'casual_cold': {
            'tops': ['Warm hoodie', 'Long-sleeve shirt'],
            'bottoms': ['Jeans', 'Warm pants'],
            'outerwear': ['Winter jacket', 'Coat'],
            'shoes': ['Boots', 'Warm sneakers'],
            'accessories': ['Scarf', 'Beanie']
        },
        'casual_warm': {
            'tops': ['T-shirt', 'Light blouse'],
            'bottoms': ['Shorts', 'Light jeans'],
            'outerwear': [],
            'shoes': ['Sneakers', 'Sandals'],
            'accessories': ['Sunglasses']
        },
        'formal_cold': {
            'tops': ['Dress shirt', 'Blouse'],
            'bottoms': ['Dress pants', 'Skirt with tights'],
            'outerwear': ['Blazer', 'Dress coat'],
            'shoes': ['Dress shoes', 'Heels'],
            'accessories': ['Watch', 'Scarf']
        },
        'formal_warm': {
            'tops': ['Light dress shirt', 'Blouse'],
            'bottoms': ['Dress pants', 'Skirt'],
            'outerwear': ['Light blazer'],
            'shoes': ['Dress shoes', 'Heels'],
            'accessories': ['Watch', 'Light jewelry']
        }
    }
    
    # Determine recommendation key
    temp = weather.get('temperature', 20)
    is_cold = temp < 15
    weather_key = 'cold' if is_cold else 'warm'
    rec_key = f"{occasion}_{weather_key}"
    
    if rec_key not in recommendations:
        rec_key = f"casual_{weather_key}"
    
    recommendation = recommendations[rec_key]
    
    return jsonify({
        'success': True,
        'recommendation': recommendation,
        'occasion': occasion,
        'weather': weather,
        'reasoning': f"Based on {occasion} occasion and {weather_key} weather",
        'note': 'Mock recommendations for demo'
    })

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    print("🎯 Starting FitCheck - Simple Demo Server...")
    print("🎭 Running in Demo Mode (Mock AI responses)")
    print("🌐 Server will be available at: http://localhost:5000")
    print("📚 API Documentation: http://localhost:5000")
    print("🔧 Health Check: http://localhost:5000/api/health")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True
    )