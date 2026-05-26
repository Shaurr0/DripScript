"""
AI Integration for Clothing Recommendation System
Handles clothing labeling, outfit suggestions, and natural language processing
"""

import json
import random
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re

# Optional Hugging Face integration
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    HUGGINGFACE_AVAILABLE = True
except ImportError:
    HUGGINGFACE_AVAILABLE = False
    print("Hugging Face transformers not installed. Natural AI suggestions will be disabled.")


class ClothingType(Enum):
    """Enumeration for clothing types"""
    HOODIE = "hoodie"
    T_SHIRT = "t-shirt"
    JEANS = "jeans"
    SHORTS = "shorts"
    JACKET = "jacket"
    SWEATER = "sweater"
    DRESS = "dress"
    SKIRT = "skirt"
    PANTS = "pants"
    SNEAKERS = "sneakers"
    BOOTS = "boots"
    SANDALS = "sandals"


class Style(Enum):
    """Enumeration for clothing styles"""
    CASUAL = "casual"
    FORMAL = "formal"
    SPORTY = "sporty"
    TRENDY = "trendy"
    VINTAGE = "vintage"
    MINIMALIST = "minimalist"


class WeatherType(Enum):
    """Enumeration for weather conditions"""
    HOT = "hot"
    WARM = "warm"
    MILD = "mild"
    COOL = "cool"
    COLD = "cold"
    RAINY = "rainy"
    SNOWY = "snowy"


@dataclass
class ClothingItem:
    """Data class representing a clothing item"""
    name: str
    type: ClothingType
    style: Style
    weather_suitability: List[WeatherType]
    color: str
    season: List[str]
    formality_level: int  # 1-10 scale
    warmth_rating: int    # 1-10 scale


class ClothingLabeler:
    """AI-powered clothing labeling system"""
    
    def __init__(self):
        self.clothing_keywords = {
            ClothingType.HOODIE: ['hoodie', 'hooded', 'pullover'],
            ClothingType.T_SHIRT: ['t-shirt', 'tee', 'shirt', 'top'],
            ClothingType.JEANS: ['jeans', 'denim'],
            ClothingType.SHORTS: ['shorts', 'short pants'],
            ClothingType.JACKET: ['jacket', 'blazer', 'coat'],
            ClothingType.SWEATER: ['sweater', 'jumper', 'cardigan'],
            ClothingType.DRESS: ['dress', 'gown'],
            ClothingType.SKIRT: ['skirt', 'mini', 'maxi'],
            ClothingType.PANTS: ['pants', 'trousers', 'slacks'],
            ClothingType.SNEAKERS: ['sneakers', 'trainers', 'athletic shoes'],
            ClothingType.BOOTS: ['boots', 'ankle boots', 'hiking boots'],
            ClothingType.SANDALS: ['sandals', 'flip flops', 'slides']
        }
        
        self.style_keywords = {
            Style.CASUAL: ['casual', 'relaxed', 'comfortable', 'everyday'],
            Style.FORMAL: ['formal', 'business', 'professional', 'elegant'],
            Style.SPORTY: ['sporty', 'athletic', 'active', 'gym'],
            Style.TRENDY: ['trendy', 'fashionable', 'stylish', 'modern'],
            Style.VINTAGE: ['vintage', 'retro', 'classic', 'old-school'],
            Style.MINIMALIST: ['minimalist', 'simple', 'clean', 'basic']
        }
    
    def label_clothing_from_text(self, description: str) -> Dict[str, Any]:
        """
        Label clothing item from text description using AI/NLP techniques
        
        Args:
            description: Text description of the clothing item
            
        Returns:
            Dictionary with predicted labels
        """
        description_lower = description.lower()
        
        # Detect clothing type
        detected_type = None
        for clothing_type, keywords in self.clothing_keywords.items():
            if any(keyword in description_lower for keyword in keywords):
                detected_type = clothing_type
                break
        
        # Detect style
        detected_styles = []
        for style, keywords in self.style_keywords.items():
            if any(keyword in description_lower for keyword in keywords):
                detected_styles.append(style)
        
        # Predict weather suitability based on keywords
        weather_suitability = self._predict_weather_suitability(description_lower)
        
        # Predict formality and warmth
        formality = self._predict_formality(description_lower)
        warmth = self._predict_warmth(description_lower)
        
        return {
            'type': detected_type.value if detected_type else 'unknown',
            'styles': [style.value for style in detected_styles],
            'weather_suitability': [weather.value for weather in weather_suitability],
            'formality_level': formality,
            'warmth_rating': warmth,
            'confidence': self._calculate_confidence(description_lower)
        }
    
    def _predict_weather_suitability(self, description: str) -> List[WeatherType]:
        """Predict weather suitability from description"""
        weather_keywords = {
            WeatherType.HOT: ['summer', 'hot', 'breathable', 'light', 'cooling'],
            WeatherType.WARM: ['warm', 'spring', 'light'],
            WeatherType.MILD: ['mild', 'transitional', 'layering'],
            WeatherType.COOL: ['cool', 'fall', 'autumn', 'light jacket'],
            WeatherType.COLD: ['winter', 'cold', 'thick', 'insulated', 'warm'],
            WeatherType.RAINY: ['waterproof', 'rain', 'water-resistant'],
            WeatherType.SNOWY: ['snow', 'insulated', 'thermal', 'heavy']
        }
        
        suitable_weather = []
        for weather, keywords in weather_keywords.items():
            if any(keyword in description for keyword in keywords):
                suitable_weather.append(weather)
        
        # Default predictions based on common clothing items
        if not suitable_weather:
            if any(word in description for word in ['hoodie', 'sweater', 'jacket']):
                suitable_weather = [WeatherType.COOL, WeatherType.COLD]
            elif any(word in description for word in ['t-shirt', 'shorts', 'sandals']):
                suitable_weather = [WeatherType.HOT, WeatherType.WARM]
            else:
                suitable_weather = [WeatherType.MILD]
        
        return suitable_weather
    
    def _predict_formality(self, description: str) -> int:
        """Predict formality level (1-10)"""
        formal_keywords = ['formal', 'business', 'professional', 'suit', 'dress shirt']
        casual_keywords = ['casual', 'relaxed', 'hoodie', 'jeans', 't-shirt']
        
        formal_score = sum(1 for keyword in formal_keywords if keyword in description)
        casual_score = sum(1 for keyword in casual_keywords if keyword in description)
        
        if formal_score > casual_score:
            return min(7 + formal_score, 10)
        elif casual_score > formal_score:
            return max(3 - casual_score, 1)
        else:
            return 5  # neutral
    
    def _predict_warmth(self, description: str) -> int:
        """Predict warmth rating (1-10)"""
        warm_keywords = ['thick', 'insulated', 'wool', 'fleece', 'down', 'winter']
        cool_keywords = ['light', 'breathable', 'cotton', 'linen', 'summer']
        
        warm_score = sum(1 for keyword in warm_keywords if keyword in description)
        cool_score = sum(1 for keyword in cool_keywords if keyword in description)
        
        base_warmth = 5
        return max(1, min(10, base_warmth + warm_score - cool_score))
    
    def _calculate_confidence(self, description: str) -> float:
        """Calculate confidence score for predictions"""
        total_keywords = len(description.split())
        matched_keywords = 0
        
        all_keywords = []
        for keywords in self.clothing_keywords.values():
            all_keywords.extend(keywords)
        for keywords in self.style_keywords.values():
            all_keywords.extend(keywords)
        
        for word in description.split():
            if word in all_keywords:
                matched_keywords += 1
        
        return min(1.0, matched_keywords / max(1, total_keywords) * 2)


class OutfitSuggestionEngine:
    """Rule-based outfit suggestion engine"""
    
    def __init__(self):
        self.wardrobe = self._initialize_sample_wardrobe()
        self.outfit_rules = self._initialize_outfit_rules()
    
    def _initialize_sample_wardrobe(self) -> List[ClothingItem]:
        """Initialize a sample wardrobe for demonstration"""
        return [
            # Casual items
            ClothingItem("Basic White Tee", ClothingType.T_SHIRT, Style.CASUAL, 
                        [WeatherType.HOT, WeatherType.WARM], "white", ["spring", "summer"], 3, 2),
            ClothingItem("Gray Hoodie", ClothingType.HOODIE, Style.CASUAL,
                        [WeatherType.COOL, WeatherType.COLD], "gray", ["fall", "winter"], 2, 7),
            ClothingItem("Blue Jeans", ClothingType.JEANS, Style.CASUAL,
                        [WeatherType.MILD, WeatherType.COOL], "blue", ["all"], 4, 5),
            ClothingItem("Summer Dress", ClothingType.DRESS, Style.CASUAL,
                        [WeatherType.HOT, WeatherType.WARM], "floral", ["spring", "summer"], 6, 2),
            ClothingItem("White Sneakers", ClothingType.SNEAKERS, Style.CASUAL,
                        [WeatherType.MILD, WeatherType.WARM, WeatherType.HOT], "white", ["all"], 3, 4),
            
            # Professional/Formal items
            ClothingItem("Navy Blazer", ClothingType.JACKET, Style.FORMAL,
                        [WeatherType.MILD, WeatherType.COOL], "navy", ["all"], 9, 5),
            ClothingItem("White Dress Shirt", ClothingType.T_SHIRT, Style.FORMAL,
                        [WeatherType.MILD, WeatherType.COOL, WeatherType.WARM], "white", ["all"], 8, 3),
            ClothingItem("Black Dress Pants", ClothingType.PANTS, Style.FORMAL,
                        [WeatherType.MILD, WeatherType.COOL], "black", ["all"], 8, 4),
            ClothingItem("Black Oxford Shoes", ClothingType.BOOTS, Style.FORMAL,
                        [WeatherType.MILD, WeatherType.COOL], "black", ["all"], 9, 3),
            
            # Trendy items
            ClothingItem("Leather Jacket", ClothingType.JACKET, Style.TRENDY,
                        [WeatherType.COOL], "black", ["fall", "spring"], 7, 6),
            ClothingItem("Skinny Black Jeans", ClothingType.JEANS, Style.TRENDY,
                        [WeatherType.MILD, WeatherType.COOL], "black", ["all"], 6, 4),
            
            # Weather-specific items
            ClothingItem("Winter Boots", ClothingType.BOOTS, Style.CASUAL,
                        [WeatherType.COLD, WeatherType.SNOWY], "brown", ["winter"], 4, 8),
            ClothingItem("Rain Jacket", ClothingType.JACKET, Style.CASUAL,
                        [WeatherType.RAINY, WeatherType.COOL], "navy", ["all"], 4, 6),
            ClothingItem("Cotton Shorts", ClothingType.SHORTS, Style.CASUAL,
                        [WeatherType.HOT, WeatherType.WARM], "khaki", ["summer"], 3, 1),
            ClothingItem("Wool Sweater", ClothingType.SWEATER, Style.CASUAL,
                        [WeatherType.COLD, WeatherType.COOL], "gray", ["winter", "fall"], 5, 8),
            
            # Additional shoes
            ClothingItem("Waterproof Boots", ClothingType.BOOTS, Style.CASUAL,
                        [WeatherType.RAINY, WeatherType.COLD], "black", ["all"], 4, 7)
        ]
    
    def _initialize_outfit_rules(self) -> Dict[str, Any]:
        """Initialize rules for outfit suggestions"""
        return {
            "weather_rules": {
                WeatherType.HOT: {
                    "preferred_types": [ClothingType.T_SHIRT, ClothingType.SHORTS, ClothingType.DRESS],
                    "avoid_types": [ClothingType.HOODIE, ClothingType.JACKET, ClothingType.BOOTS],
                    "max_warmth": 4
                },
                WeatherType.COLD: {
                    "preferred_types": [ClothingType.HOODIE, ClothingType.JACKET, ClothingType.BOOTS],
                    "avoid_types": [ClothingType.SHORTS, ClothingType.SANDALS],
                    "min_warmth": 6
                }
            },
            "vibe_rules": {
                "casual": {
                    "preferred_styles": [Style.CASUAL],
                    "max_formality": 6,
                    "avoid_types": []
                },
                "professional": {
                    "preferred_styles": [Style.FORMAL],
                    "min_formality": 7,
                    "preferred_types": [ClothingType.JACKET, ClothingType.PANTS, ClothingType.T_SHIRT],
                    "avoid_types": [ClothingType.HOODIE, ClothingType.SHORTS]
                },
                "business": {
                    "preferred_styles": [Style.FORMAL],
                    "min_formality": 8,
                    "preferred_types": [ClothingType.JACKET, ClothingType.PANTS, ClothingType.T_SHIRT],
                    "avoid_types": [ClothingType.HOODIE, ClothingType.SHORTS, ClothingType.JEANS]
                },
                "trendy": {
                    "preferred_styles": [Style.TRENDY],
                    "avoid_styles": [Style.VINTAGE],
                    "min_formality": 5
                },
                "sporty": {
                    "preferred_styles": [Style.SPORTY, Style.CASUAL],
                    "max_formality": 4
                }
            }
        }
    
    def suggest_outfit(self, weather: str, vibe: str, occasion: str = "general") -> Dict[str, Any]:
        """
        Suggest an outfit based on weather and vibe
        
        Args:
            weather: Weather condition (hot, cold, mild, etc.)
            vibe: Desired vibe (casual, professional, trendy, etc.)
            occasion: Specific occasion (optional)
            
        Returns:
            Dictionary with suggested outfit and reasoning
        """
        try:
            weather_enum = WeatherType(weather.lower())
        except ValueError:
            weather_enum = WeatherType.MILD
        
        # Filter wardrobe based on rules
        suitable_items = self._filter_items_by_weather(weather_enum)
        suitable_items = self._filter_items_by_vibe(suitable_items, vibe.lower())
        
        # Create outfit combination
        outfit = self._create_outfit_combination(suitable_items)
        
        # Generate reasoning
        reasoning = self._generate_outfit_reasoning(outfit, weather, vibe)
        
        return {
            "outfit": [item.name for item in outfit],
            "items_details": [
                {
                    "name": item.name,
                    "type": item.type.value,
                    "style": item.style.value,
                    "color": item.color
                } for item in outfit
            ],
            "reasoning": reasoning,
            "weather": weather,
            "vibe": vibe,
            "confidence": self._calculate_outfit_confidence(outfit, weather_enum, vibe)
        }
    
    def _filter_items_by_weather(self, weather: WeatherType) -> List[ClothingItem]:
        """Filter items suitable for given weather"""
        return [item for item in self.wardrobe if weather in item.weather_suitability]
    
    def _filter_items_by_vibe(self, items: List[ClothingItem], vibe: str) -> List[ClothingItem]:
        """Filter items based on desired vibe"""
        vibe_rules = self.outfit_rules.get("vibe_rules", {}).get(vibe, {})
        
        filtered_items = []
        for item in items:
            # Check formality requirements
            if "min_formality" in vibe_rules and item.formality_level < vibe_rules["min_formality"]:
                continue
            if "max_formality" in vibe_rules and item.formality_level > vibe_rules["max_formality"]:
                continue
            
            # Check type restrictions
            if "avoid_types" in vibe_rules and item.type in vibe_rules["avoid_types"]:
                continue
            
            # Check style preferences (allow if no preferred styles specified OR item matches)
            if "preferred_styles" in vibe_rules and len(vibe_rules["preferred_styles"]) > 0:
                if item.style not in vibe_rules["preferred_styles"]:
                    continue
            
            # Check style restrictions
            if "avoid_styles" in vibe_rules and item.style in vibe_rules["avoid_styles"]:
                continue
                
            filtered_items.append(item)
        
        # If no items match strict criteria, try relaxed filtering for professional/business
        if not filtered_items and vibe in ["professional", "business"]:
            for item in items:
                if item.formality_level >= 6:  # At least smart casual
                    filtered_items.append(item)
        
        return filtered_items if filtered_items else items  # Fall back to all items if no matches
    
    def _create_outfit_combination(self, items: List[ClothingItem]) -> List[ClothingItem]:
        """Create a complete outfit from available items"""
        outfit = []
        
        # Categorize items
        tops = [item for item in items if item.type in [ClothingType.T_SHIRT, ClothingType.HOODIE, ClothingType.SWEATER]]
        bottoms = [item for item in items if item.type in [ClothingType.JEANS, ClothingType.SHORTS, ClothingType.PANTS]]
        dresses = [item for item in items if item.type == ClothingType.DRESS]
        shoes = [item for item in items if item.type in [ClothingType.SNEAKERS, ClothingType.BOOTS, ClothingType.SANDALS]]
        outerwear = [item for item in items if item.type == ClothingType.JACKET]
        
        # Prioritize formal items if available for professional look
        formal_items = [item for item in items if item.formality_level >= 7]
        has_formal_items = len(formal_items) > 0
        
        # Build outfit - prefer complete combinations
        if dresses and (not has_formal_items or random.choice([True, False])):
            # Choose dress for simpler outfit
            outfit.append(random.choice(dresses))
        else:
            # Build top + bottom combination
            if has_formal_items:
                # For formal looks, prioritize formal items
                formal_tops = [item for item in tops if item.formality_level >= 7]
                formal_bottoms = [item for item in bottoms if item.formality_level >= 7]
                
                if formal_tops:
                    outfit.append(random.choice(formal_tops))
                elif tops:
                    outfit.append(random.choice(tops))
                    
                if formal_bottoms:
                    outfit.append(random.choice(formal_bottoms))
                elif bottoms:
                    outfit.append(random.choice(bottoms))
            else:
                # Regular casual combination
                if tops:
                    outfit.append(random.choice(tops))
                if bottoms:
                    outfit.append(random.choice(bottoms))
        
        # Always try to add shoes
        if shoes:
            # Prefer formal shoes for formal outfits
            if has_formal_items:
                formal_shoes = [item for item in shoes if item.formality_level >= 7]
                if formal_shoes:
                    outfit.append(random.choice(formal_shoes))
                else:
                    outfit.append(random.choice(shoes))
            else:
                outfit.append(random.choice(shoes))
        
        # Add outerwear based on context
        if outerwear:
            # Always add outerwear for cold/rainy weather or formal occasions
            weather_needs_outerwear = any(item.type in [ClothingType.JACKET] and 
                                        any(weather in item.weather_suitability for weather in [WeatherType.COLD, WeatherType.RAINY]) 
                                        for item in outerwear)
            formal_needs_outerwear = has_formal_items and any(item.formality_level >= 7 for item in outerwear)
            
            if weather_needs_outerwear or formal_needs_outerwear or random.choice([True, False]):
                if has_formal_items:
                    formal_outerwear = [item for item in outerwear if item.formality_level >= 7]
                    if formal_outerwear:
                        outfit.append(random.choice(formal_outerwear))
                    else:
                        outfit.append(random.choice(outerwear))
                else:
                    outfit.append(random.choice(outerwear))
        
        return outfit
    
    def _generate_outfit_reasoning(self, outfit: List[ClothingItem], weather: str, vibe: str) -> str:
        """Generate explanation for outfit choice"""
        reasons = []
        
        for item in outfit:
            reasons.append(f"{item.name} is perfect for {weather} weather")
        
        reasons.append(f"This combination matches your {vibe} vibe")
        
        return ". ".join(reasons) + "."
    
    def _calculate_outfit_confidence(self, outfit: List[ClothingItem], weather: WeatherType, vibe: str) -> float:
        """Calculate confidence score for outfit suggestion"""
        if not outfit:
            return 0.0
        
        weather_match = sum(1 for item in outfit if weather in item.weather_suitability) / len(outfit)
        return weather_match


class HuggingFaceIntegration:
    """Optional Hugging Face integration for natural language outfit suggestions"""
    
    def __init__(self):
        self.available = HUGGINGFACE_AVAILABLE
        self.classifier = None
        self.generator = None
        
        if self.available:
            try:
                # Initialize sentiment analysis for vibe detection
                self.classifier = pipeline("sentiment-analysis")
                print("Hugging Face integration initialized successfully")
            except Exception as e:
                print(f"Failed to initialize Hugging Face models: {e}")
                self.available = False
    
    def analyze_outfit_request(self, request_text: str) -> Dict[str, Any]:
        """
        Analyze natural language outfit request
        
        Args:
            request_text: Natural language description of outfit needs
            
        Returns:
            Dictionary with extracted parameters
        """
        if not self.available:
            return {"error": "Hugging Face integration not available"}
        
        try:
            # Extract weather information
            weather = self._extract_weather_from_text(request_text)
            
            # Extract vibe/mood
            vibe = self._extract_vibe_from_text(request_text)
            
            # Extract occasion
            occasion = self._extract_occasion_from_text(request_text)
            
            # Sentiment analysis for overall mood
            sentiment = self.classifier(request_text)[0] if self.classifier else None
            
            return {
                "weather": weather,
                "vibe": vibe,
                "occasion": occasion,
                "sentiment": sentiment,
                "original_request": request_text
            }
            
        except Exception as e:
            return {"error": f"Analysis failed: {str(e)}"}
    
    def _extract_weather_from_text(self, text: str) -> str:
        """Extract weather information from text"""
        weather_patterns = {
            "hot": ["hot", "sunny", "warm", "summer", "heat"],
            "cold": ["cold", "winter", "freezing", "chilly", "snow"],
            "rainy": ["rain", "wet", "drizzle", "storm", "umbrella"],
            "mild": ["mild", "pleasant", "moderate", "spring", "fall"]
        }
        
        text_lower = text.lower()
        for weather, keywords in weather_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                return weather
        
        return "mild"  # default
    
    def _extract_vibe_from_text(self, text: str) -> str:
        """Extract vibe/style from text"""
        vibe_patterns = {
            "business": ["business", "meeting", "presentation", "corporate", "executive"],
            "professional": ["professional", "work", "office", "formal"],
            "casual": ["casual", "relaxed", "comfortable", "laid-back", "everyday"],
            "trendy": ["trendy", "stylish", "fashionable", "hip", "cool", "modern"],
            "sporty": ["sporty", "athletic", "gym", "workout", "active", "exercise"]
        }
        
        text_lower = text.lower()
        for vibe, keywords in vibe_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                return vibe
        
        return "casual"  # default
    
    def _extract_occasion_from_text(self, text: str) -> str:
        """Extract occasion from text"""
        occasion_patterns = {
            "date": ["date", "romantic", "dinner", "restaurant"],
            "work": ["work", "office", "meeting", "presentation"],
            "party": ["party", "celebration", "event", "night out"],
            "casual": ["everyday", "general", "normal", "regular"]
        }
        
        text_lower = text.lower()
        for occasion, keywords in occasion_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                return occasion
        
        return "general"  # default


class ClothingAI:
    """Main AI integration class combining all components"""
    
    def __init__(self):
        self.labeler = ClothingLabeler()
        self.suggestion_engine = OutfitSuggestionEngine()
        self.hf_integration = HuggingFaceIntegration()
    
    def label_clothing(self, description: str) -> Dict[str, Any]:
        """Label clothing item from description"""
        return self.labeler.label_clothing_from_text(description)
    
    def suggest_outfit_from_params(self, weather: str, vibe: str, occasion: str = "general") -> Dict[str, Any]:
        """Suggest outfit from explicit parameters"""
        return self.suggestion_engine.suggest_outfit(weather, vibe, occasion)
    
    def suggest_outfit_from_text(self, request_text: str) -> Dict[str, Any]:
        """Suggest outfit from natural language request"""
        if self.hf_integration.available:
            # Use AI to parse the request
            analysis = self.hf_integration.analyze_outfit_request(request_text)
            if "error" in analysis:
                # Fall back to simple rule-based parsing
                return self._fallback_text_parsing(request_text)
            
            weather = analysis.get("weather", "mild")
            vibe = analysis.get("vibe", "casual")
            occasion = analysis.get("occasion", "general")
            
        else:
            # Use simple rule-based parsing
            return self._fallback_text_parsing(request_text)
        
        # Generate outfit suggestion
        outfit_suggestion = self.suggestion_engine.suggest_outfit(weather, vibe, occasion)
        outfit_suggestion["natural_language_analysis"] = analysis if self.hf_integration.available else None
        
        return outfit_suggestion
    
    def _fallback_text_parsing(self, text: str) -> Dict[str, Any]:
        """Simple rule-based text parsing when HuggingFace is not available"""
        text_lower = text.lower()
        
        # Simple weather detection
        weather = "mild"
        if any(word in text_lower for word in ["hot", "warm", "summer", "sunny", "beach"]):
            weather = "hot"
        elif any(word in text_lower for word in ["cold", "winter", "chilly", "freezing", "snow"]):
            weather = "cold"
        elif any(word in text_lower for word in ["rain", "wet", "rainy", "drizzle", "storm"]):
            weather = "rainy"
        elif any(word in text_lower for word in ["cool", "fall", "autumn"]):
            weather = "cool"
        
        # Simple vibe detection with better matching
        vibe = "casual"
        if any(word in text_lower for word in ["business", "meeting", "presentation", "office", "formal", "suit"]):
            vibe = "business" if any(word in text_lower for word in ["business", "meeting", "presentation"]) else "professional"
        elif any(word in text_lower for word in ["professional", "work"]):
            vibe = "professional"
        elif any(word in text_lower for word in ["trendy", "stylish", "fashionable", "hip", "cool"]):
            vibe = "trendy"
        elif any(word in text_lower for word in ["sporty", "gym", "workout", "exercise", "athletic"]):
            vibe = "sporty"
        elif any(word in text_lower for word in ["casual", "relaxed", "comfortable", "everyday"]):
            vibe = "casual"
        
        return self.suggestion_engine.suggest_outfit(weather, vibe)
    
    def add_clothing_item(self, item: ClothingItem):
        """Add new clothing item to wardrobe"""
        self.suggestion_engine.wardrobe.append(item)
    
    def get_wardrobe_summary(self) -> Dict[str, Any]:
        """Get summary of current wardrobe"""
        wardrobe = self.suggestion_engine.wardrobe
        
        types_count = {}
        styles_count = {}
        
        for item in wardrobe:
            types_count[item.type.value] = types_count.get(item.type.value, 0) + 1
            styles_count[item.style.value] = styles_count.get(item.style.value, 0) + 1
        
        return {
            "total_items": len(wardrobe),
            "types_distribution": types_count,
            "styles_distribution": styles_count,
            "items": [
                {
                    "name": item.name,
                    "type": item.type.value,
                    "style": item.style.value,
                    "color": item.color
                } for item in wardrobe
            ]
        }


# Example usage and testing
if __name__ == "__main__":
    # Initialize the AI system
    clothing_ai = ClothingAI()
    
    print("=== Clothing AI Integration Demo ===\n")
    
    # Test clothing labeling
    print("1. Testing Clothing Labeling:")
    test_descriptions = [
        "A comfortable gray hoodie perfect for cold weather",
        "Light blue summer dress with floral patterns",
        "Professional black suit jacket for business meetings",
        "Casual white sneakers for everyday wear"
    ]
    
    for desc in test_descriptions:
        labels = clothing_ai.label_clothing(desc)
        print(f"   Description: {desc}")
        print(f"   Labels: {labels}\n")
    
    # Test outfit suggestions with parameters
    print("2. Testing Outfit Suggestions (Parameters):")
    suggestion = clothing_ai.suggest_outfit_from_params("cold", "casual")
    print(f"   Weather: cold, Vibe: casual")
    print(f"   Suggestion: {suggestion}\n")
    
    # Test natural language suggestions
    print("3. Testing Natural Language Suggestions:")
    nl_requests = [
        "I need something casual for a hot summer day",
        "What should I wear for a professional business meeting?",
        "Suggest an outfit for a cold winter evening"
    ]
    
    for request in nl_requests:
        suggestion = clothing_ai.suggest_outfit_from_text(request)
        print(f"   Request: {request}")
        print(f"   Suggestion: {suggestion['outfit']}")
        print(f"   Reasoning: {suggestion['reasoning']}\n")
    
    # Show wardrobe summary
    print("4. Current Wardrobe Summary:")
    summary = clothing_ai.get_wardrobe_summary()
    print(f"   Total items: {summary['total_items']}")
    print(f"   Types: {summary['types_distribution']}")
    print(f"   Styles: {summary['styles_distribution']}")