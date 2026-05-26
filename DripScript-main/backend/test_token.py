#!/usr/bin/env python3
"""
Simple test to verify Hugging Face API token
"""

import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_huggingface_token():
    """Test if the Hugging Face token is valid"""
    
    token = os.getenv('HUGGINGFACE_API_TOKEN')
    
    if not token:
        print("❌ No HUGGINGFACE_API_TOKEN found in environment")
        return False
    
    print(f"✅ Token found: {token[:10]}...")
    
    # Test with a simple, always available model
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Test with a basic sentiment analysis model (always available)
    test_models = [
        "cardiffnlp/twitter-roberta-base-sentiment-latest",
        "distilbert-base-uncased-finetuned-sst-2-english",
        "microsoft/DialoGPT-small"
    ]
    
    for model in test_models:
        print(f"\n🧪 Testing model: {model}")
        
        url = f"https://api-inference.huggingface.co/models/{model}"
        
        payload = {
            "inputs": "I love fashion and style!"
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Success! Response: {result}")
                return True
            elif response.status_code == 403:
                print("❌ 403 Forbidden - Token might be invalid or expired")
            elif response.status_code == 503:
                print("⏳ 503 Service Unavailable - Model loading, please wait...")
            else:
                print(f"❌ Error {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
    
    return False

def test_simple_generation():
    """Test text generation with a simple model"""
    
    token = os.getenv('HUGGINGFACE_API_TOKEN')
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Try GPT-2 which is always available
    url = "https://api-inference.huggingface.co/models/gpt2"
    
    payload = {
        "inputs": "Fashion advice for today:",
        "parameters": {
            "max_new_tokens": 50,
            "temperature": 0.7
        }
    }
    
    try:
        print(f"\n🤖 Testing GPT-2 for text generation...")
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ GPT-2 Success! Response: {result}")
            return True
        else:
            print(f"❌ GPT-2 Error {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ GPT-2 Request failed: {e}")
    
    return False

if __name__ == "__main__":
    print("🔍 Hugging Face Token Test")
    print("=" * 40)
    
    # Test basic token functionality
    token_ok = test_huggingface_token()
    
    # Test text generation
    generation_ok = test_simple_generation()
    
    print("\n" + "=" * 40)
    if token_ok or generation_ok:
        print("✅ Token is working! You can use Hugging Face API")
    else:
        print("❌ Token test failed. Please check:")
        print("   1. Token is correctly set in .env file")
        print("   2. Token has the right permissions")
        print("   3. You have internet connection")
        print("   4. Try creating a new token at: https://huggingface.co/settings/tokens")