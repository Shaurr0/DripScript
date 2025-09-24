#!/usr/bin/env python3
"""
Test script for Gemini AI integration
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to the path so we can import our services
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.ai_service import RealAIService

def test_gemini_connection():
    """Test if Gemini API is accessible"""
    print("🔗 Testing Gemini API Connection...")
    
    ai_service = RealAIService()
    
    if not ai_service.gemini_api_key:
        print("❌ No Gemini API key found!")
        return False
    
    print(f"✅ API Key found: {ai_service.gemini_api_key[:10]}...")
    print(f"🤖 Model: {ai_service.model_name}")
    
    # Test basic API call
    test_prompt = "What should I wear for a casual day out when it's 22°C and sunny?"
    result = ai_service._query_gemini(test_prompt)
    
    if result:
        print(f"✅ Gemini API Test successful!")
        print(f"📝 Response: {result[:200]}...")
        return True
    else:
        print("❌ Gemini API Test failed!")
        return False

def test_clothing_analysis():
    """Test clothing analysis functionality with Gemini"""
    print("\n🧪 Testing Clothing Analysis with Gemini...")
    
    ai_service = RealAIService()
    
    # Test with a sample filename
    test_filename = "black-leather-jacket.jpg"
    result = ai_service.analyze_clothing_image("", test_filename)
    
    print(f"📸 Analyzing: {test_filename}")
    print(f"✅ Result: {result}")
    
    return result

def test_outfit_recommendation():
    """Test outfit recommendation functionality with Gemini"""
    print("\n👗 Testing Outfit Recommendations with Gemini...")
    
    ai_service = RealAIService()
    
    # Sample wardrobe
    sample_wardrobe = [
        {"name": "Dark Blue Jeans", "category": "bottoms", "color": "blue", "vibe": "casual"},
        {"name": "White Cotton T-Shirt", "category": "tops", "color": "white", "vibe": "casual"},
        {"name": "Black Leather Jacket", "category": "tops", "color": "black", "vibe": "edgy"},
        {"name": "White Sneakers", "category": "shoes", "color": "white", "vibe": "casual"},
        {"name": "Red Hoodie", "category": "tops", "color": "red", "vibe": "sporty"}
    ]
    
    # Sample weather
    sample_weather = {
        "temperature": 18,
        "condition": "partly cloudy",
        "weather_category": "mild"
    }
    
    result = ai_service.generate_outfit_recommendation(sample_wardrobe, sample_weather, "casual")
    
    print(f"🌤️ Weather: {sample_weather['temperature']}°C, {sample_weather['condition']}")
    print(f"👕 Wardrobe: {len(sample_wardrobe)} items")
    print(f"🎯 Occasion: casual")
    print(f"✅ Recommendation: {result}")
    
    return result

if __name__ == "__main__":
    print("🎯 FitCheck Gemini AI Test")
    print("=" * 60)
    
    # Test API connection first
    api_ok = test_gemini_connection()
    
    if api_ok:
        print("\n" + "=" * 60)
        
        # Test clothing analysis
        clothing_result = test_clothing_analysis()
        
        print("=" * 60)
        
        # Test outfit recommendations
        outfit_result = test_outfit_recommendation()
        
        print("\n" + "=" * 60)
        print("🎉 All Gemini tests completed!")
        
        if clothing_result and outfit_result:
            print("✅ Gemini AI Fashion Analysis is working perfectly!")
            print("🚀 Your fashion app is ready with AI-powered features!")
        else:
            print("⚠️ Some features may need adjustment, but basic AI is working!")
    else:
        print("❌ Gemini API connection failed. Please check your key!")