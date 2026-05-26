"""
AI Service for Clothing Analysis and Outfit Recommendations
Uses Cohere API for text-based AI analysis
"""

import os
import requests
import json
from typing import Dict, Any, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RealAIService:
    """AI service for clothing analysis using Cohere"""

    def __init__(self):
        self.cohere_api_key = os.getenv('COHERE_API_KEY')
        self.openweather_api_key = os.getenv('OPENWEATHER_API_KEY')
        self.cohere_base_url = "https://api.cohere.com/v1"
        self.weather_base_url = "http://api.openweathermap.org/data/2.5"

        if not self.cohere_api_key:
            logger.warning("COHERE_API_KEY not found in environment variables")
        if not self.openweather_api_key:
            logger.info("OPENWEATHER_API_KEY not configured; using mock weather data")

    def analyze_clothing_image(self, image_data: str, filename: str = "") -> Dict[str, Any]:
        """
        Analyze clothing from image using AI.
        Cohere doesn't support vision, so we use filename + text inference.
        """
        try:
            analysis_prompt = (
                f'You are a fashion product tagger. Based on the filename "{filename}", '
                f'infer the clothing item details. Return ONLY a single JSON object with keys: '
                f'name, category, color, style, weather_suitability, occasions, confidence, description. '
                f'- category must be one of: tops, bottoms, dresses, shoes, accessories. '
                f'- color must be one of: black, white, red, blue, green, yellow, purple, pink, brown, gray, orange. '
                f'Example: {{"name":"Black Jeans","category":"bottoms","color":"black","style":"casual",'
                f'"weather_suitability":["mild","cool"],"occasions":["casual","everyday"],'
                f'"confidence":0.85,"description":"Classic dark denim pants"}}'
            )

            if self.cohere_api_key and filename:
                result = self._query_cohere(analysis_prompt)
                if result:
                    try:
                        json_start = result.find('{')
                        json_end = result.rfind('}') + 1
                        if json_start != -1 and json_end > json_start:
                            parsed_result = json.loads(result[json_start:json_end])
                            return self._normalize_analysis(parsed_result, filename)
                    except json.JSONDecodeError:
                        logger.error("Failed to parse JSON from Cohere response")

            return self._fallback_analysis(filename)

        except Exception as e:
            logger.error(f"Error in clothing analysis: {e}")
            return self._fallback_analysis(filename)

    def get_weather_data(self, city: str = "London") -> Dict[str, Any]:
        """Get real weather data from OpenWeatherMap API"""
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

            temperature = data['main']['temp']
            condition = data['weather'][0]['main'].lower()
            description = data['weather'][0]['description']
            humidity = data['main']['humidity']
            wind_speed = data['wind']['speed']
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

    def classify_clothing_image(self, image_data: str) -> Dict[str, Any]:
        """Classify a clothing image into the schema required by the frontend."""
        try:
            classify_prompt = (
                "You are a fashion AI. A user uploaded a clothing image. "
                "Based on common clothing items, return ONLY a JSON object with these fields: "
                "name (specific item name like 'Classic White T-Shirt'), "
                "category (one of: tops/bottoms/dresses/shoes/accessories), "
                "color (single main color as plain text), "
                "vibe (one of: casual/formal/sporty/trendy/vintage), "
                "tags (array of 3 descriptive words). "
                "Example: {\"name\":\"Navy Blazer\",\"category\":\"tops\",\"color\":\"blue\","
                "\"vibe\":\"formal\",\"tags\":[\"structured\",\"professional\",\"versatile\"]}"
            )

            if self.cohere_api_key:
                result_text = self._query_cohere(classify_prompt)
                if result_text:
                    json_start = result_text.find('{')
                    json_end = result_text.rfind('}') + 1
                    if json_start != -1 and json_end > json_start:
                        parsed = json.loads(result_text[json_start:json_end])
                        parsed = parsed if isinstance(parsed, dict) else {}
                        return {
                            "name": parsed.get("name", "Stylish Item"),
                            "category": (parsed.get("category", "tops") or "tops").strip().lower(),
                            "color": parsed.get("color", "gray"),
                            "vibe": (parsed.get("vibe", "casual") or "casual").strip().lower(),
                            "tags": parsed.get("tags", []) if isinstance(parsed.get("tags", []), list) else [],
                        }

            return {
                "name": "Stylish Item",
                "category": "tops",
                "color": "gray",
                "vibe": "casual",
                "tags": ["minimal", "everyday", "layering"],
            }
        except Exception as e:
            logger.error(f"Error in classify_clothing_image: {e}")
            return {
                "name": "Stylish Item",
                "category": "tops",
                "color": "gray",
                "vibe": "casual",
                "tags": ["minimal", "everyday", "layering"],
            }

    def generate_outfit_recommendation(self, wardrobe: List[Dict], weather: Dict, occasion: str) -> Dict[str, Any]:
        """Generate AI-powered outfit recommendations (3 outfits)."""
        try:
            if not wardrobe:
                return {"error": "No wardrobe items available"}

            wardrobe_context = self._format_wardrobe_for_ai(wardrobe)
            weather_context = f"Temperature: {weather.get('temperature', 20)}°C, Condition: {weather.get('condition', 'clear')}"

            recommendation_prompt = (
                f"You are a professional fashion stylist. Given these wardrobe items:\n"
                f"{wardrobe_context}\n\n"
                f"Occasion: {occasion}\nWeather: {weather_context}\n\n"
                f"Suggest 3 complete outfits. For each outfit return: items array (names from the wardrobe list above), "
                f"styling_tip (one sentence), color_story (describe the color combination), "
                f"and why_it_works (one sentence).\n\n"
                f"Return ONLY a JSON array of 3 outfit objects like:\n"
                f'[{{"items":["Item 1","Item 2"],"styling_tip":"...","color_story":"...","why_it_works":"..."}}]'
            )

            if self.cohere_api_key:
                result = self._query_cohere(recommendation_prompt)
                if result:
                    try:
                        # Try to find a JSON array first
                        arr_start = result.find('[')
                        arr_end = result.rfind(']') + 1
                        if arr_start != -1 and arr_end > arr_start:
                            parsed_result = json.loads(result[arr_start:arr_end])
                            if isinstance(parsed_result, list):
                                return {"outfits": parsed_result}

                        # Fallback: try finding a JSON object with "outfits" key
                        json_start = result.find('{')
                        json_end = result.rfind('}') + 1
                        if json_start != -1 and json_end > json_start:
                            parsed_result = json.loads(result[json_start:json_end])
                            if isinstance(parsed_result, dict) and isinstance(parsed_result.get("outfits"), list):
                                return parsed_result
                    except json.JSONDecodeError:
                        logger.error("Failed to parse outfit recommendation JSON")

            return self._fallback_outfit_recommendation(wardrobe, weather, occasion)

        except Exception as e:
            logger.error(f"Error generating outfit recommendation: {e}")
            return self._fallback_outfit_recommendation(wardrobe, weather, occasion)

    def _query_cohere(self, prompt: str) -> Optional[str]:
        """Query Cohere Chat API"""
        try:
            url = f"{self.cohere_base_url}/chat"

            headers = {
                'Authorization': f'Bearer {self.cohere_api_key}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }

            payload = {
                "model": "command-r-plus",
                "message": prompt,
                "temperature": 0.2,
                "preamble": "You are a fashion AI assistant. Always respond with valid JSON only, no extra text."
            }

            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()

            return result.get('text', '')

        except requests.exceptions.HTTPError as e:
            logger.error(f"Cohere API HTTP error: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error querying Cohere API: {e}")
            return None

    def _normalize_analysis(self, data: Dict[str, Any], filename: str = "") -> Dict[str, Any]:
        """Normalize category and color to supported sets"""
        category = (data.get('category') or '').strip().lower()
        color = (data.get('color') or '').strip().lower()
        name = data.get('name') or 'Stylish Item'
        style = (data.get('style') or 'casual').strip().lower()

        cat_map = {
            'top': 'tops', 't-shirt': 'tops', 'tee': 'tops', 'shirt': 'tops',
            'blouse': 'tops', 'hoodie': 'tops', 'sweater': 'tops', 'jacket': 'tops', 'coat': 'tops',
            'pant': 'bottoms', 'pants': 'bottoms', 'jean': 'bottoms', 'jeans': 'bottoms',
            'trouser': 'bottoms', 'short': 'bottoms', 'shorts': 'bottoms', 'skirt': 'bottoms',
            'dress': 'dresses', 'gown': 'dresses',
            'shoe': 'shoes', 'shoes': 'shoes', 'sneaker': 'shoes', 'sneakers': 'shoes',
            'boot': 'shoes', 'boots': 'shoes', 'sandal': 'shoes', 'sandals': 'shoes',
            'accessory': 'accessories', 'belt': 'accessories', 'cap': 'accessories',
            'hat': 'accessories', 'scarf': 'accessories', 'watch': 'accessories', 'glove': 'accessories'
        }
        if category in ['tops', 'bottoms', 'dresses', 'shoes', 'accessories']:
            normalized_category = category
        else:
            normalized_category = cat_map.get(category)
            if not normalized_category:
                text = f"{name} {data.get('description', '')}".lower()
                for key, val in cat_map.items():
                    if key in text:
                        normalized_category = val
                        break
            if not normalized_category:
                normalized_category = 'accessories'

        color_map = {
            'navy': 'blue', 'denim': 'blue', 'sky blue': 'blue', 'teal': 'blue',
            'grey': 'gray', 'charcoal': 'gray', 'silver': 'gray',
            'beige': 'brown', 'tan': 'brown', 'khaki': 'brown', 'camel': 'brown',
            'maroon': 'red', 'burgundy': 'red',
            'violet': 'purple', 'lavender': 'purple',
            'gold': 'yellow', 'mustard': 'yellow',
            'magenta': 'pink', 'fuchsia': 'pink',
            'orange': 'orange', 'black': 'black', 'white': 'white',
            'red': 'red', 'blue': 'blue', 'green': 'green', 'yellow': 'yellow',
            'purple': 'purple', 'pink': 'pink', 'brown': 'brown', 'gray': 'gray'
        }
        normalized_color = color_map.get(color)
        if not normalized_color:
            for k, v in color_map.items():
                if k in color:
                    normalized_color = v
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
            'description': data.get('description') or 'AI-powered analysis'
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
        items = []
        for item in wardrobe:
            items.append(f"- {item.get('name', 'Unknown')} ({item.get('category', 'unknown')}, {item.get('color', 'unknown')} color, {item.get('vibe', 'casual')} style)")
        return '\n'.join(items)

    def _fallback_analysis(self, filename: str) -> Dict[str, Any]:
        """Fallback analysis based on filename heuristics"""
        filename_lower = (filename or '').lower()
        colors = {
            'yellow': ['yellow', 'golden', 'mustard', 'lemon'],
            'blue': ['blue', 'navy', 'royal', 'sky', 'denim'],
            'red': ['red', 'crimson', 'scarlet', 'cherry', 'maroon', 'burgundy'],
            'green': ['green', 'forest', 'lime', 'olive'],
            'black': ['black', 'charcoal', 'dark'],
            'white': ['white', 'cream', 'ivory'],
            'purple': ['purple', 'violet', 'lavender'],
            'orange': ['orange', 'peach', 'coral'],
            'pink': ['pink', 'rose', 'magenta', 'fuchsia'],
            'brown': ['brown', 'tan', 'beige', 'khaki', 'camel'],
            'gray': ['gray', 'grey', 'silver']
        }
        detected_color = 'gray'
        for color, hints in colors.items():
            if any(h in filename_lower for h in hints):
                detected_color = color
                break

        if any(w in filename_lower for w in ['shirt', 'tee', 't-shirt', 'top', 'blouse', 'hoodie', 'sweater', 'tank', 'jacket', 'coat']):
            category = 'tops'
        elif any(w in filename_lower for w in ['jean', 'pant', 'trouser', 'short', 'skirt']):
            category = 'bottoms'
        elif any(w in filename_lower for w in ['dress', 'gown', 'frock']):
            category = 'dresses'
        elif any(w in filename_lower for w in ['shoe', 'boot', 'sneaker', 'sandal', 'heel']):
            category = 'shoes'
        else:
            category = 'accessories'

        name = filename.replace('_', ' ').replace('-', ' ')
        name = ''.join(c for c in name if c.isalnum() or c.isspace()).strip() or 'Stylish Item'
        name = ' '.join(name.split()).title()

        return {
            'name': name,
            'category': category,
            'color': detected_color,
            'style': 'casual',
            'weather_suitability': ['mild', 'warm'] if category in ['tops', 'dresses'] else ['mild', 'cool'],
            'occasions': ['casual', 'everyday'],
            'confidence': 0.8,
            'description': 'Filename-based fallback analysis'
        }

    def _fallback_outfit_recommendation(self, wardrobe: List[Dict], weather: Dict, occasion: str) -> Dict[str, Any]:
        """Fallback rule-based outfit recommendation"""
        temperature = weather.get('temperature', 20)

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
            'outfits': [{
                'items': [item['name'] for item in outfit],
                'styling_tip': f'A solid choice for a {occasion} look in {weather.get("weather_category", "mild")} weather.',
                'color_story': 'Complementary tones that work well together.',
                'why_it_works': f'Weather-appropriate and suited for {occasion} occasions.'
            }]
        }


ai_service = RealAIService()
