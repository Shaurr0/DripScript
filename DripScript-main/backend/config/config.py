"""
Configuration settings for DripScript
"""

# Weather API Configuration
WEATHER_CONFIG = {
    "default_location": "New York",
    "temperature_units": "celsius",
    "update_interval": 3600
}

# Outfit Suggestion Rules
OUTFIT_RULES = {
    "weather_mapping": {
        "temperature_ranges": {
            "hot": {"min": 25, "max": 50},
            "warm": {"min": 18, "max": 25},
            "mild": {"min": 10, "max": 18},
            "cool": {"min": 0, "max": 10},
            "cold": {"min": -20, "max": 0}
        }
    }
}

# Clothing Categories
CLOTHING_CATEGORIES = {
    "tops": ["t-shirt", "hoodie", "sweater", "jacket", "blazer", "shirt"],
    "bottoms": ["jeans", "shorts", "pants", "skirt", "leggings"],
    "dresses": ["dress", "gown", "sundress"],
    "shoes": ["sneakers", "boots", "sandals", "heels", "flats"],
    "accessories": ["hat", "scarf", "belt", "jewelry", "bag"]
}

# Color Coordination Rules
COLOR_RULES = {
    "complementary_colors": {
        "blue": ["white", "cream", "gray", "navy"],
        "black": ["white", "gray", "red", "pink"],
        "white": ["any"],
        "gray": ["blue", "pink", "yellow", "green"],
        "brown": ["cream", "beige", "orange", "green"]
    }
}
