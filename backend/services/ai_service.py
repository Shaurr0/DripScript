"""
Real AI Service for Clothing Analysis and Outfit Recommendations
Uses Groq API (free tier with excellent limits) for AI analysis
"""

import os
import requests
import json
import base64
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ClothingItem:
    name: str
    category: str
    color: str
    style: str
    weather_suitability: List[str]
    occasion: List[str]
    confidence: float

class RealAIService:
    """Real AI service for clothing analysis using Groq API"""
    
    def __init__(self):
        # Accept both backend-style and Vite-style env var names
        self.gemini_api_key = os.getenv('GEMINI_API_KEY') or os.getenv('VITE_GEMINI_API_KEY')
        self.openweather_api_key = os.getenv('OPENWEATHER_API_KEY') or os.getenv('VITE_WEATHER_API_KEY')
        self.gemini_base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self.weather_base_url = "http://api.openweathermap.org/data/2.5"
        self.model_name = "gemini-1.5-flash"
        
        if not self.gemini_api_key:
            logger.warning("GEMINI_API_KEY not found in environment variables")
        if not self.openweather_api_key:
            logger.warning("OPENWEATHER_API_KEY not found in environment variables")
    
    def analyze_clothing_image(self, image_data: str, filename: str = "") -> Dict[str, Any]:
        """
        Analyze clothing from image using AI
        
        Args:
            image_data: Base64 encoded image data
            filename: Optional filename for context
            
        Returns:
            Dictionary with clothing analysis
        """
        try:
            # Build strict prompt with normalization guidance
            analysis_prompt = f"""
            You are a fashion product tagger. Analyze the clothing item provided (image attached if present) and the filename "{filename}".
            Return ONLY a single JSON object, nothing else. Keys must be exactly:
            name, category, color, style, weather_suitability, occasions, confidence, description.
            - category must be one of: tops, bottoms, dresses, shoes, accessories.
            - color must be one of: black, white, red, blue, green, yellow, purple, pink, brown, gray, orange.
            If you detect synonyms, normalize them (e.g., navy->blue, denim->blue, beige->brown, grey->gray).
            Choose the primary color of the garment (ignore the background and model's skin/shoes if not the product).
            Example valid JSON:
            {{"name":"Black Jeans","category":"bottoms","color":"black","style":"casual","weather_suitability":["mild","cool"],"occasions":["casual","everyday"],"confidence":0.9,"description":"Denim pants; dark black tone"}}
            """
            
            if self.gemini_api_key:
                # Try multimodal query when image is available
                image_base64 = None
                mime_type = None
                if image_data:
                    # Accept full data URL or plain base64
                    if image_data.startswith('data:') and ';base64,' in image_data:
                        header, b64 = image_data.split(','); image_base64 = b64
                        # Extract mime from header e.g., data:image/jpeg;base64
                        try:
                            mime_type = header.split(':',1)[1].split(';',1)[0]
                        except Exception:
                            mime_type = 'image/jpeg'
                    else:
                        image_base64 = image_data
                        mime_type = 'image/jpeg'
                result = self._query_gemini(analysis_prompt, image_base64=image_base64, mime_type=mime_type)
                if result:
                    try:
                        # Parse JSON from the response
                        json_start = result.find('{')
                        json_end = result.rfind('}') + 1
                        if json_start != -1 and json_end > json_start:
                            json_str = result[json_start:json_end]
                            parsed_result = json.loads(json_str)
                            return self._normalize_analysis(parsed_result, filename)
                    except json.JSONDecodeError:
                        logger.error("Failed to parse JSON from AI response")
            
            # Fallback to rule-based analysis
            return self._fallback_analysis(filename)
            
        except Exception as e:
            logger.error(f"Error in clothing analysis: {e}")
            return self._fallback_analysis(filename)
    
    def get_weather_data(self, city: str = "London") -> Dict[str, Any]:
        """
        Get real weather data from OpenWeatherMap API
        
        Args:
            city: City name for weather data
            
        Returns:
            Dictionary with weather information
        """
        try:
            if not self.openweather_api_key:
                return self._mock_weather_data()
            
            url = f"{self.weather_base_url}/weather"
            params = {
                'q': city,
                'appid': self.openweather_api_key,
                'units': 'metric'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Convert to our format
            temperature = data['main']['temp']
            condition = data['weather'][0]['main'].lower()
            description = data['weather'][0]['description']
            humidity = data['main']['humidity']
            wind_speed = data['wind']['speed']
            
            # Determine weather category for outfit selection
            weather_category = self._categorize_weather(temperature, condition)
            
            return {
                'temperature': round(temperature),
                'condition': condition,
                'description': description.title(),
                'humidity': humidity,
                'wind_speed': wind_speed,
                'weather_category': weather_category,
                'city': city,
                'recommendation': self._get_weather_recommendation(temperature, condition)
            }
            
        except Exception as e:
            logger.error(f"Error getting weather data: {e}")
            return self._mock_weather_data()
    
    def generate_outfit_recommendation(self, wardrobe: List[Dict], weather: Dict, occasion: str) -> Dict[str, Any]:
        """
        Generate AI-powered outfit recommendation
        
        Args:
            wardrobe: List of user's clothing items
            weather: Weather data
            occasion: Occasion type
            
        Returns:
            Dictionary with outfit recommendation
        """
        try:
            if not wardrobe:
                return {"error": "No wardrobe items available"}
            
            # Create context for AI
            wardrobe_context = self._format_wardrobe_for_ai(wardrobe)
            weather_context = f"Temperature: {weather.get('temperature', 20)}°C, Condition: {weather.get('condition', 'clear')}"
            
            recommendation_prompt = f"""
            You are a professional fashion stylist. Based on the following information, recommend ONE complete outfit:
            
            WARDROBE ITEMS:
            {wardrobe_context}
            
            WEATHER: {weather_context}
            OCCASION: {occasion}
            
            Please select items from the wardrobe to create one cohesive outfit. Respond in JSON format:
            {{
                "outfit": [
                    {{
                        "name": "item name from wardrobe",
                        "category": "category",
                        "reason": "why this item was chosen"
                    }}
                ],
                "overall_reasoning": "Why this outfit works well together",
                "style_score": 9,
                "weather_score": 8,
                "confidence": 0.9
            }}
            
            Choose items that:
            1. Are appropriate for the weather
            2. Match the occasion
            3. Work well together in terms of style and color
            4. Create a complete, practical outfit
            """
            
            if self.gemini_api_key:
                result = self._query_gemini(recommendation_prompt)
                if result:
                    try:
                        json_start = result.find('{')
                        json_end = result.rfind('}') + 1
                        if json_start != -1 and json_end > json_start:
                            json_str = result[json_start:json_end]
                            parsed_result = json.loads(json_str)
                            return parsed_result
                    except json.JSONDecodeError:
                        logger.error("Failed to parse outfit recommendation JSON")
            
            # Fallback to rule-based recommendation
            return self._fallback_outfit_recommendation(wardrobe, weather, occasion)
            
        except Exception as e:
            logger.error(f"Error generating outfit recommendation: {e}")
            return self._fallback_outfit_recommendation(wardrobe, weather, occasion)
    
    def _query_gemini(self, prompt: str, image_base64: Optional[str] = None, mime_type: Optional[str] = None) -> Optional[str]:
        """Query Google Gemini API with optional inline image data"""
        try:
            url = f"{self.gemini_base_url}/{self.model_name}:generateContent?key={self.gemini_api_key}"
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            # Format prompt for Gemini
            formatted_prompt = f"You are a professional fashion stylist with expertise in clothing analysis and outfit coordination. {prompt}"
            
            parts = []
            if image_base64:
                parts.append({
                    "inlineData": {
                        "mimeType": mime_type or "image/jpeg",
                        "data": image_base64
                    }
                })
            parts.append({"text": formatted_prompt})
            
            payload = {
                "contents": [{
                    "parts": parts
                }],
                "generationConfig": {
                    "temperature": 0.2,
                    "topK": 1,
                    "topP": 1,
                    "maxOutputTokens": 1000,
                    "stopSequences": []
                },
                "safetySettings": [
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    }
                ]
            }
            
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Extract text from Gemini response
            if 'candidates' in result and len(result['candidates']) > 0:
                candidate = result['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    if len(candidate['content']['parts']) > 0:
                        return candidate['content']['parts'][0]['text']
            
            logger.warning(f"Unexpected Gemini response format: {result}")
            return None
            
        except Exception as e:
            logger.error(f"Error querying Gemini API: {e}")
            return None
    
    def _normalize_analysis(self, data: Dict[str, Any], filename: str = "") -> Dict[str, Any]:
        """Normalize category and color to supported sets and apply synonyms"""
        category = (data.get('category') or '').strip().lower()
        color = (data.get('color') or '').strip().lower()
        name = data.get('name') or 'Stylish Item'
        style = (data.get('style') or 'casual').strip().lower()

        # Category normalization
        cat_map = {
            'top': 'tops', 't-shirt': 'tops', 'tee': 'tops', 'shirt': 'tops', 'blouse': 'tops', 'hoodie': 'tops', 'sweater': 'tops', 'jacket': 'tops', 'coat': 'tops',
            'pant': 'bottoms', 'pants': 'bottoms', 'jean': 'bottoms', 'jeans': 'bottoms', 'trouser': 'bottoms', 'short': 'bottoms', 'shorts': 'bottoms', 'skirt': 'bottoms',
            'dress': 'dresses', 'gown': 'dresses',
            'shoe': 'shoes', 'shoes': 'shoes', 'sneaker': 'shoes', 'sneakers': 'shoes', 'boot': 'shoes', 'boots': 'shoes', 'sandal': 'shoes', 'sandals': 'shoes',
            'accessory': 'accessories', 'belt': 'accessories', 'cap': 'accessories', 'hat': 'accessories', 'scarf': 'accessories', 'watch': 'accessories', 'glove': 'accessories'
        }
        if category in ['tops', 'bottoms', 'dresses', 'shoes', 'accessories']:
            normalized_category = category
        else:
            normalized_category = cat_map.get(category)
            if not normalized_category:
                # Try to infer from name or description keywords
                text = f"{name} {data.get('description','')}".lower()
                for key, val in cat_map.items():
                    if key in text:
                        normalized_category = val
                        break
            if not normalized_category:
                normalized_category = 'accessories'

        # Color normalization
        color_map = {
            'navy': 'blue', 'denim': 'blue', 'sky blue': 'blue', 'teal': 'blue',
            'grey': 'gray', 'charcoal': 'gray', 'silver': 'gray',
            'beige': 'brown', 'tan': 'brown', 'khaki': 'brown', 'camel': 'brown',
            'maroon': 'red', 'burgundy': 'red',
            'violet': 'purple', 'lavender': 'purple',
            'gold': 'yellow', 'mustard': 'yellow',
            'magenta': 'pink', 'fuchsia': 'pink',
            'orange': 'orange', 'black': 'black', 'white': 'white', 'red': 'red', 'blue': 'blue', 'green': 'green', 'yellow': 'yellow', 'purple': 'purple', 'pink': 'pink', 'brown': 'brown', 'gray': 'gray'
        }
        normalized_color = color_map.get(color)
        if not normalized_color:
            # Try containment mapping
            for k, v in color_map.items():
                if k in color:
                    normalized_color = v
                    break
        if not normalized_color:
            # Try filename-based color inference with common synonyms
            file_lower = (filename or '').lower()
            filename_color_hints = {
                'yellow': ['yellow','gold','mustard','lemon','sun'],
                'blue': ['blue','navy','denim','royal','sky'],
                'red': ['red','crimson','scarlet','maroon','burgundy','cherry'],
                'green': ['green','olive','forest','lime'],
                'black': ['black','charcoal'],
                'white': ['white','ivory','cream'],
                'purple': ['purple','violet','lavender'],
                'orange': ['orange','peach','coral'],
                'pink': ['pink','magenta','fuchsia','rose'],
                'brown': ['brown','beige','tan','khaki','camel'],
                'gray': ['gray','grey','silver']
            }
            for base, hints in filename_color_hints.items():
                if any(h in file_lower for h in hints):
                    normalized_color = base
                    break
            if not normalized_color:
                normalized_color = 'gray'

        occasions = data.get('occasions') or data.get('occasion') or ['casual', 'everyday']
        if isinstance(occasions, str):
            occasions = [occasions]

        return {
            'name': name,
            'category': normalized_category,
            'color': normalized_color,
            'style': style,
            'weather_suitability': data.get('weather_suitability') or ['mild', 'warm'],
            'occasions': occasions,
            'confidence': float(data.get('confidence') or 0.8),
            'description': data.get('description') or 'AI analysis with normalization'
        }
    
    def _mock_weather_data(self) -> Dict[str, Any]:
        """Mock weather data when API is not available"""
        return {
            'temperature': 22,
            'condition': 'clear',
            'description': 'Clear Sky',
            'humidity': 60,
            'wind_speed': 5,
            'weather_category': 'mild',
            'city': 'Demo Location',
            'recommendation': 'Perfect weather for light layers'
        }
    
    def _categorize_weather(self, temperature: float, condition: str) -> str:
        """Categorize weather for outfit selection"""
        if temperature >= 25:
            return 'hot'
        elif temperature >= 20:
            return 'warm'
        elif temperature >= 15:
            return 'mild'
        elif temperature >= 5:
            return 'cool'
        else:
            return 'cold'
    
    def _get_weather_recommendation(self, temperature: float, condition: str) -> str:
        """Get weather-specific clothing recommendation"""
        if temperature >= 25:
            return "Light, breathable fabrics recommended"
        elif temperature >= 20:
            return "Comfortable light layers work well"
        elif temperature >= 15:
            return "Light jacket or sweater recommended"
        elif temperature >= 5:
            return "Warm layers and outerwear needed"
        else:
            return "Heavy winter clothing recommended"
    
    def _format_wardrobe_for_ai(self, wardrobe: List[Dict]) -> str:
        """Format wardrobe items for AI context"""
        items = []
        for item in wardrobe:
            items.append(f"- {item.get('name', 'Unknown')} ({item.get('category', 'unknown')}, {item.get('color', 'unknown')} color, {item.get('vibe', 'casual')} style)")
        return '\n'.join(items)
    
    def _fallback_analysis(self, filename: str) -> Dict[str, Any]:
        """Fallback analysis based on filename heuristics (no AI)."""
        filename_lower = (filename or '').lower()
        # Color detection
        colors = {
            'yellow': ['yellow','golden','mustard','lemon'],
            'blue': ['blue','navy','royal','sky','denim'],
            'red': ['red','crimson','scarlet','cherry','maroon','burgundy'],
            'green': ['green','forest','lime','olive'],
            'black': ['black','charcoal','dark'],
            'white': ['white','cream','ivory'],
            'purple': ['purple','violet','lavender'],
            'orange': ['orange','peach','coral'],
            'pink': ['pink','rose','magenta','fuchsia'],
            'brown': ['brown','tan','beige','khaki','camel'],
            'gray': ['gray','grey','silver']
        }
        detected_color = 'gray'
        for color, hints in colors.items():
            if any(h in filename_lower for h in hints):
                detected_color = color
                break
        # Category detection
        if any(w in filename_lower for w in ['shirt','tee','t-shirt','top','blouse','hoodie','sweater','tank','jacket','coat']):
            category = 'tops'
        elif any(w in filename_lower for w in ['jean','pant','trouser','short','skirt']):
            category = 'bottoms'
        elif any(w in filename_lower for w in ['dress','gown','frock']):
            category = 'dresses'
        elif any(w in filename_lower for w in ['shoe','boot','sneaker','sandal','heel']):
            category = 'shoes'
        else:
            category = 'accessories'
        # Name cleanup
        name = filename.replace('_',' ').replace('-',' ')
        name = ''.join(c for c in name if c.isalnum() or c.isspace()).strip() or 'Stylish Item'
        name = ' '.join(name.split()).title()
        return {
            'name': name,
            'category': category,
            'color': detected_color,
            'style': 'casual',
            'weather_suitability': ['mild','warm'] if category in ['tops','dresses'] else ['mild','cool'],
            'occasions': ['casual','everyday'],
            'confidence': 0.8,
            'description': 'Filename-based fallback analysis'
        }
    def _fallback_outfit_recommendation(self, wardrobe: List[Dict], weather: Dict, occasion: str) -> Dict[str, Any]:
        """Fallback rule-based outfit recommendation"""
        # Simple rule-based selection
        temperature = weather.get('temperature', 20)
        
        # Filter items by weather appropriateness
        suitable_items = []
        for item in wardrobe:
            if temperature >= 20 and item.get('category') in ['tops', 'dresses', 'shorts']:
                suitable_items.append(item)
            elif temperature < 20 and item.get('category') in ['tops', 'bottoms', 'outerwear']:
                suitable_items.append(item)
            elif item.get('category') == 'shoes':
                suitable_items.append(item)
        
        if not suitable_items:
            suitable_items = wardrobe
        
        # Select one item from each category if possible
        outfit = []
        categories_needed = ['tops', 'bottoms', 'shoes']
        
        for category in categories_needed:
            items_in_category = [item for item in suitable_items if item.get('category') == category]
            if items_in_category:
                outfit.append({
                    'name': items_in_category[0].get('name', 'Item'),
                    'category': category,
                    'reason': f'Selected for {occasion} occasion and {weather.get("weather_category", "current")} weather'
                })
        
        return {
            'outfit': outfit,
            'overall_reasoning': f'Rule-based selection appropriate for {occasion} in {weather.get("weather_category", "current")} weather',
            'style_score': 7,
            'weather_score': 8,
            'confidence': 0.8
        }

# Create global instance
ai_service = RealAIService()