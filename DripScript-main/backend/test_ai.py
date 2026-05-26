#!/usr/bin/env python3
"""
Test script for Hugging Face AI integration
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to the path so we can import our services
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.ai_service import RealAIService

def test_clothing_analysis():
    """Test clothing analysis functionality"""
    print("🧪 Testing Clothing Analysis...")
    
    ai_service = RealAIService()
    
    # Test with a sample filename
    test_filename = "blue-denim-jeans.jpg"
    result = ai_service.analyze_clothing_image("", test_filename)
    
    print(f"📸 Analyzing: {test_filename}")
    print(f"✅ Result: {result}")
    print()
    
    return result

def test_outfit_recommendation():
    """Test outfit recommendation functionality"""
    print("👗 Testing Outfit Recommendations...")
    
    ai_service = RealAIService()
    
    # Sample wardrobe
    sample_wardrobe = [
        {"name": "Blue Jeans", "category": "bottoms", "color": "blue", "vibe": "casual"},
        {"name": "White T-Shirt", "category": "tops", "color": "white", "vibe": "casual"},
        {"name": "Black Sneakers", "category": "shoes", "color": "black", "vibe": "casual"},
        {"name": "Red Hoodie", "category": "tops", "color": "red", "vibe": "casual"}
    ]
    
    # Sample weather
    sample_weather = {
        "temperature": 22,
        "condition": "clear",
        "weather_category": "mild"
    }
    
    result = ai_service.generate_outfit_recommendation(sample_wardrobe, sample_weather, "casual")
    
    print(f"🌤️ Weather: {sample_weather['temperature']}°C, {sample_weather['condition']}")
    print(f"👕 Wardrobe: {len(sample_wardrobe)} items")
    print(f"🎯 Occasion: casual")
    print(f"✅ Recommendation: {result}")
    print()
    
    return result

def test_api_connection():
    """Test if Hugging Face API is accessible"""
    print("🔗 Testing API Connection...")
    
    ai_service = RealAIService()
    
    if not ai_service.huggingface_api_key:
        print("❌ No Hugging Face API token found!")
        return False
    
    print(f"✅ API Token found: {ai_service.huggingface_api_key[:10]}...")
    print(f"🤖 Model: {ai_service.model_name}")
    
    # Test basic API call
    test_prompt = "What is a good outfit for sunny weather?"
    result = ai_service._query_huggingface(test_prompt)
    
    if result:
        print(f"✅ API Test successful!")
        print(f"📝 Response: {result[:100]}...")
    else:
        print("❌ API Test failed!")
    
    return result is not None

if __name__ == "__main__":
    print("🎯 FitCheck AI Service Test")
    print("=" * 50)
    
    # Test API connection first
    api_ok = test_api_connection()
    
    if api_ok:
        print("\n" + "=" * 50)
        
        # Test clothing analysis
        clothing_result = test_clothing_analysis()
        
        print("=" * 50)
        
        # Test outfit recommendations
        outfit_result = test_outfit_recommendation()
        
        print("=" * 50)
        print("🎉 All tests completed!")
        
        if clothing_result and outfit_result:
            print("✅ AI Fashion Analysis is working!")
        else:
            print("⚠️ Some features may need adjustment")
    else:
        print("❌ API connection failed. Please check your token!")