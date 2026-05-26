"""
Configuration settings for Clothing AI Integration
"""

# AI Model Configuration
AI_CONFIG = {
    "huggingface": {
        "enabled": True,
        "model_name": "distilbert-base-uncased-finetuned-sst-2-english",  # For sentiment analysis
        "cache_dir": "./models",
        "max_length": 512
    },
    "confidence_threshold": 0.7,
    "enable_caching": True
}

# Weather API Configuration (optional - for real weather integration)
WEATHER_CONFIG = {
    "api_key": None,  # Set your weather API key here
    "default_location": "New York",
    "temperature_units": "celsius",  # or "fahrenheit"
    "update_interval": 3600  # seconds
}

# Outfit Suggestion Rules
OUTFIT_RULES = {
    "weather_mapping": {
        "temperature_ranges": {
            "hot": {"min": 25, "max": 50},      # Celsius
            "warm": {"min": 18, "max": 25},
            "mild": {"min": 10, "max": 18},
            "cool": {"min": 0, "max": 10},
            "cold": {"min": -20, "max": 0}
        }
    },
    "formality_scale": {
        "very_casual": {"min": 1, "max": 3},
        "casual": {"min": 3, "max": 5},
        "smart_casual": {"min": 5, "max": 7},
        "formal": {"min": 7, "max": 9},
        "very_formal": {"min": 9, "max": 10}
    }
}

# Clothing Categories and Attributes
CLOTHING_CATEGORIES = {
    "tops": ["t-shirt", "hoodie", "sweater", "jacket", "blazer", "shirt"],
    "bottoms": ["jeans", "shorts", "pants", "skirt", "leggings"],
    "dresses": ["dress", "gown", "sundress"],
    "shoes": ["sneakers", "boots", "sandals", "heels", "flats"],
    "accessories": ["hat", "scarf", "belt", "jewelry", "bag"]
}

# Style Definitions
STYLE_DEFINITIONS = {
    "casual": {
        "description": "Relaxed, comfortable, everyday wear",
        "keywords": ["comfortable", "relaxed", "everyday", "laid-back"],
        "typical_items": ["jeans", "t-shirt", "sneakers", "hoodie"]
    },
    "formal": {
        "description": "Professional, business, elegant attire",
        "keywords": ["professional", "business", "elegant", "sophisticated"],
        "typical_items": ["suit", "dress shirt", "dress pants", "dress shoes"]
    },
    "trendy": {
        "description": "Fashion-forward, stylish, contemporary",
        "keywords": ["fashionable", "stylish", "modern", "hip"],
        "typical_items": ["designer pieces", "statement items", "current trends"]
    },
    "sporty": {
        "description": "Athletic, active, performance-oriented",
        "keywords": ["athletic", "active", "performance", "gym"],
        "typical_items": ["activewear", "sneakers", "tracksuit", "sports bra"]
    }
}

# Color Coordination Rules
COLOR_RULES = {
    "complementary_colors": {
        "blue": ["white", "cream", "gray", "navy"],
        "black": ["white", "gray", "red", "pink"],
        "white": ["any"],  # White goes with everything
        "gray": ["blue", "pink", "yellow", "green"],
        "brown": ["cream", "beige", "orange", "green"]
    },
    "seasonal_colors": {
        "spring": ["pastels", "light green", "pink", "yellow"],
        "summer": ["bright", "white", "light blue", "coral"],
        "fall": ["warm tones", "orange", "brown", "burgundy"],
        "winter": ["dark colors", "black", "navy", "deep red"]
    }
}

# Database Configuration (for future data persistence)
DATABASE_CONFIG = {
    "type": "sqlite",  # or "postgresql", "mysql"
    "path": "./clothing_data.db",
    "tables": {
        "wardrobe": "user_wardrobe",
        "outfits": "saved_outfits",
        "preferences": "user_preferences"
    }
}

# Logging Configuration
LOGGING_CONFIG = {
    "level": "INFO",  # DEBUG, INFO, WARNING, ERROR
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "./logs/clothing_ai.log"
}

# Feature Flags
FEATURES = {
    "natural_language_processing": True,
    "weather_integration": False,  # Enable when weather API is configured
    "color_coordination": True,
    "seasonal_suggestions": True,
    "user_preferences": True,
    "outfit_history": True
}