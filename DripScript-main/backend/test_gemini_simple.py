#!/usr/bin/env python3
"""
Simple test to verify Gemini API is working with the current setup
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_gemini_direct():
    """Test Gemini API directly with the current setup"""
    
    api_key = os.getenv('GEMINI_API_KEY')
    
    print("🔍 Environment Check:")
    print(f"GEMINI_API_KEY present: {bool(api_key)}")
    if api_key:
        print(f"API Key: {api_key[:10]}...")
    
    if not api_key:
        print("❌ No Gemini API key found!")
        return False
    
    # Test the actual API call
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    payload = {
        "contents": [{
            "parts": [{
                "text": "You are a fashion stylist. Analyze this clothing item: blue-jeans.jpg. Respond with: name, category, color, and style in JSON format."
            }]
        }],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 500
        }
    }
    
    try:
        print("\n🚀 Testing Gemini API...")
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Extract the response text
            if 'candidates' in result and len(result['candidates']) > 0:
                candidate = result['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    if len(candidate['content']['parts']) > 0:
                        text = candidate['content']['parts'][0]['text']
                        print("✅ Gemini API Success!")
                        print(f"📝 Response: {text}")
                        return True
            
            print(f"⚠️ Unexpected response format: {result}")
            return False
            
        else:
            print(f"❌ API Error {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

if __name__ == "__main__":
    print("🎯 Simple Gemini API Test")
    print("=" * 50)
    
    success = test_gemini_direct()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Gemini API is working perfectly!")
        print("🚀 Your fashion AI is ready!")
    else:
        print("❌ Gemini API test failed")
        print("Please check your API key and internet connection")