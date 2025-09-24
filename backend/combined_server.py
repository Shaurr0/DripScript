#!/usr/bin/env python3
"""
FitCheck - Combined Server with Demo API + Gemini AI
"""

from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
import os
from dotenv import load_dotenv
import sys
import random

# Add the current directory to the path so we can import our services
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from services.ai_service import RealAIService
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    print("⚠️ AI Service not available, using demo mode")

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Initialize AI service if available
ai_service = None
if AI_AVAILABLE:
    try:
        ai_service = RealAIService()
        gemini_status = "✅ Connected" if ai_service.gemini_api_key else "❌ Not configured"
        print(f"🤖 Gemini API: {gemini_status}")
    except Exception as e:
        print(f"⚠️ AI Service initialization failed: {e}")
        AI_AVAILABLE = False

@app.route('/')
def home():
    """API home page"""
    ai_status = "✅ Gemini AI Active" if (AI_AVAILABLE and ai_service and ai_service.gemini_api_key) else "⚠️ Demo Mode"
    
    html = f"""
    <html>
    <head>
        <title>FitCheck - Fashion AI API</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto; 
                   max-width: 800px; margin: 50px auto; padding: 20px; 
                   background: #0f172a; color: #e2e8f0; }}
            .header {{ text-align: center; margin-bottom: 40px; }}
            .emoji {{ font-size: 48px; }}
            .status {{ padding: 5px 10px; border-radius: 20px; font-size: 12px; margin: 5px 0; }}
            .available {{ background: #059669; color: white; }}
            .ai {{ background: #8b5cf6; color: white; }}
            .demo {{ background: #f59e0b; color: white; }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="emoji">🎯</div>
            <h1>FitCheck - Fashion AI API</h1>
            <p>Smart Wardrobe Management with AI</p>
        </div>
        
        <div class="status available">✅ Server Running</div>
        <div class="status {'ai' if AI_AVAILABLE and ai_service and ai_service.gemini_api_key else 'demo'}">{ai_status}</div>
        
        <h2>Available Endpoints</h2>
        <p><strong>/api/health</strong> - Health check</p>
        <p><strong>/api/classify</strong> - Clothing analysis (POST)</p>
        <p><strong>/api/weather</strong> - Weather data (GET)</p>
        <p><strong>/api/recommend</strong> - Outfit recommendations (POST)</p>
        
        <p><a href="/api/health" style="color: #8b5cf6;">Test Health Check</a></p>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'FitCheck Fashion AI API',
        'mode': 'ai' if (AI_AVAILABLE and ai_service and ai_service.gemini_api_key) else 'demo',
        'gemini_available': bool(AI_AVAILABLE and ai_service and ai_service.gemini_api_key),
        'version': '3.0.0'
    })

@app.route('/api/classify', methods=['POST'])
def classify_clothing():
    """AI-powered clothing classification"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        filename = data.get('filename', '')
        description = data.get('description', filename)
        
        # Try AI analysis first
        if AI_AVAILABLE and ai_service and ai_service.gemini_api_key:
            try:
                result = ai_service.analyze_clothing_image('', filename)
                return jsonify({
                    'success': True,
                    'classification': result,
                    'filename': filename,
                    'ai_powered': True,
                    'source': 'Gemini AI'
                })
            except Exception as e:
                print(f"AI analysis failed: {e}")
                # Fall through to demo analysis
        
        # Demo/fallback analysis
        return demo_classify_clothing(filename, description)
        
    except Exception as e:
        return jsonify({
            'error': f'Analysis failed: {str(e)}',
            'success': False
        }), 500

# New endpoint that matches frontend expectations
@app.route('/api/ai/analyze', methods=['POST'])
def ai_analyze_clothing():
    """AI-powered clothing analysis - matches frontend expectations"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        filename = data.get('filename', '')
        image_data = data.get('image_data', '')
        
        if not filename:
            return jsonify({'error': 'Filename is required'}), 400
        
        # Try real AI analysis with image data
        if AI_AVAILABLE and ai_service and ai_service.gemini_api_key:
            try:
                print(f"🔍 Analyzing with Gemini: {filename}, image_data_length: {len(image_data) if image_data else 0}")
                result = ai_service.analyze_clothing_image(image_data, filename)
                print(f"✅ Gemini result: {result}")
                return jsonify({
                    'success': True,
                    'analysis': result,
                    'filename': filename,
                    'ai_powered': True,
                    'model': ai_service.model_name,
                    'source': 'Gemini AI'
                })
            except Exception as e:
                print(f"🔴 Gemini AI Error: {e}")
                # Fall through to smart fallback
        
        # Smart fallback analysis
        fallback_result = smart_fallback_analysis(filename)
        return jsonify({
            'success': True,
            'analysis': fallback_result,
            'filename': filename,
            'ai_powered': False,
            'source': 'Smart Fallback'
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Analysis failed: {str(e)}',
            'success': False
        }), 500

def smart_fallback_analysis(filename):
    """Smart fallback analysis with better color detection"""
    filename_lower = filename.lower()
    
    # Better name processing
    name = filename.replace('_', ' ').replace('-', ' ')
    name = ''.join(c for c in name if c.isalnum() or c.isspace())
    name = ' '.join(name.split()).title()
    if not name:
        name = "Stylish Item"
    
    # Color detection - check filename for color words
    colors = {
        'yellow': ['yellow', 'golden', 'mustard', 'lemon'],
        'blue': ['blue', 'navy', 'royal', 'sky'],
        'red': ['red', 'crimson', 'scarlet', 'cherry'],
        'green': ['green', 'forest', 'lime', 'olive'],
        'black': ['black', 'dark'],
        'white': ['white', 'cream', 'ivory'],
        'purple': ['purple', 'violet', 'lavender'],
        'orange': ['orange', 'peach', 'coral'],
        'pink': ['pink', 'rose', 'magenta'],
        'brown': ['brown', 'tan', 'beige'],
        'gray': ['gray', 'grey', 'silver']
    }
    
    detected_color = 'gray'  # neutral default
    for color, keywords in colors.items():
        if any(keyword in filename_lower for keyword in keywords):
            detected_color = color
            break
    
    # Category detection
    if any(word in filename_lower for word in ['shirt', 'tee', 't-shirt', 'top', 'blouse', 'hoodie', 'sweater', 'tank']):
        category = 'tops'
    elif any(word in filename_lower for word in ['jean', 'pant', 'trouser', 'short', 'skort']):
        category = 'bottoms'
    elif any(word in filename_lower for word in ['dress', 'gown', 'frock']):
        category = 'dresses'
    elif any(word in filename_lower for word in ['shoe', 'boot', 'sneaker', 'sandal', 'heel']):
        category = 'shoes'
    else:
        # Neutral default category
        category = 'accessories'
    
    # Style detection
    if any(word in filename_lower for word in ['formal', 'dress', 'business', 'suit']):
        style = 'formal'
    elif any(word in filename_lower for word in ['sport', 'athletic', 'gym', 'running']):
        style = 'sporty'
    elif any(word in filename_lower for word in ['vintage', 'retro', 'classic']):
        style = 'vintage'
    elif any(word in filename_lower for word in ['trendy', 'fashion', 'designer']):
        style = 'trendy'
    else:
        style = 'casual'
    
    return {
        'name': name,
        'category': category,
        'color': detected_color.title(),
        'style': style,
        'weather_suitability': ['mild', 'warm'] if category in ['tops', 'dresses'] else ['mild', 'cool'],
        'occasions': ['casual', 'everyday'] if style == 'casual' else [style, 'special'],
        'confidence': 0.8,
        'description': f'Smart analysis based on filename patterns and clothing characteristics'
    }

def demo_classify_clothing(filename, description):
    """Original demo classification for backward compatibility"""
    mock_classifications = {
        'hoodie': {'type': 'hoodie', 'category': 'tops', 'warmth': 'warm', 'style': 'casual'},
        'shirt': {'type': 'shirt', 'category': 'tops', 'warmth': 'light', 'style': 'casual'},
        'jeans': {'type': 'jeans', 'category': 'bottoms', 'warmth': 'medium', 'style': 'casual'},
    }
    
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
        'note': 'Demo classification'
    })

@app.route('/api/weather')
def weather():
    """Weather data"""
    city = request.args.get('city', 'London')
    
    if AI_AVAILABLE and ai_service and hasattr(ai_service, 'get_weather_data'):
        try:
            weather_data = ai_service.get_weather_data(city)
            return jsonify({
                'success': True,
                'weather': weather_data,
                'city': city,
                'source': 'Real API' if ai_service.openweather_api_key else 'Mock'
            })
        except:
            pass
    
    # Mock weather data
    conditions = [
        {'temp': 15, 'condition': 'cloudy', 'humidity': 65, 'description': 'Cloudy'},
        {'temp': 22, 'condition': 'sunny', 'humidity': 45, 'description': 'Sunny'},
        {'temp': 8, 'condition': 'cold', 'humidity': 70, 'description': 'Cold'},
        {'temp': 28, 'condition': 'hot', 'humidity': 30, 'description': 'Hot'}
    ]
    
    weather_data = random.choice(conditions)
    return jsonify({
        'success': True,
        'weather': {
            'city': city,
            'temperature': weather_data['temp'],
            'condition': weather_data['condition'],
            'humidity': weather_data['humidity'],
            'description': weather_data['description']
        },
        'source': 'Mock'
    })

@app.route('/api/recommend', methods=['POST'])
def recommend_outfit():
    """Outfit recommendations"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request data is required'}), 400
    
    wardrobe = data.get('wardrobe', [])
    weather = data.get('weather', {})
    occasion = data.get('occasion', 'casual')
    
    # Try AI recommendations if available
    if AI_AVAILABLE and ai_service and ai_service.gemini_api_key:
        try:
            result = ai_service.generate_outfit_recommendation(wardrobe, weather, occasion)
            return jsonify({
                'success': True,
                'recommendation': result,
                'ai_powered': True,
                'source': 'Gemini AI'
            })
        except Exception as e:
            print(f"AI recommendation failed: {e}")
    
    # Basic recommendation logic
    temp = weather.get('temperature', 20)
    is_cold = temp < 15
    
    recommendation = {
        'outfit': [
            {'name': 'Comfortable Top', 'category': 'tops', 'reason': 'Good base layer'},
            {'name': 'Suitable Bottom', 'category': 'bottoms', 'reason': 'Matches the occasion'},
            {'name': 'Appropriate Shoes', 'category': 'shoes', 'reason': 'Completes the look'}
        ],
        'overall_reasoning': f'Basic recommendation for {occasion} in {temp}°C weather',
        'style_score': 7,
        'weather_score': 8,
        'confidence': 0.7
    }
    
    return jsonify({
        'success': True,
        'recommendation': recommendation,
        'occasion': occasion,
        'weather': weather,
        'source': 'Basic Logic'
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    print("🎯 Starting FitCheck - Combined Server...")
    print(f"🤖 AI Available: {AI_AVAILABLE}")
    if AI_AVAILABLE and ai_service:
        print(f"🎯 Gemini API: {'✅ Connected' if ai_service.gemini_api_key else '❌ Not configured'}")
    print("🌐 Server will be available at: http://localhost:5000")
    print("📚 API Documentation: http://localhost:5000")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True
    )