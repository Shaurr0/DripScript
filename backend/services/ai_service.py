"""
AI Service for Clothing Analysis and Outfit Recommendations
Uses Cohere API for text-based AI analysis and BLIP for image captioning
"""

import os
import requests
import json
import re
import random
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from typing import Dict, Any, List, Optional
import logging

from services import fashionclip_service
from services import style_scoring

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _get_filename_from_url(url: str) -> str:
    if not url:
        return ""
    # Extract last segment
    segment = url.split('/')[-1]
    # Remove query parameters
    segment = segment.split('?')[0]
    # Decode URL-encoded characters (like %20 for spaces)
    from urllib.parse import unquote
    segment = unquote(segment)
    # Remove timestamp prefix (digits followed by underscore)
    cleaned = re.sub(r'^\d+_', '', segment)
    return cleaned.lower()

def _hamming_distance(hash1: str, hash2: str) -> int:
    if not hash1 or not hash2 or len(hash1) != len(hash2):
        return 999
    return sum(c1 != c2 for c1, c2 in zip(hash1, hash2))

# --- BLIP Model (loaded once globally) ---
_blip_processor = None
_blip_model = None

# --- Fashion Classifier (dima806/clothes_image_detection, loaded once globally) ---
_fashion_classifier_pipeline = None
_fashion_classifier_load_attempted = False

FASHION_CLASSIFIER_MODEL = "dima806/clothes_image_detection"
FASHION_CLASSIFIER_CONFIDENCE_THRESHOLD = 0.55
LIGHT_SUGGESTION_CONFIDENCE_THRESHOLD = 0.6
LIGHT_SUGGESTION_TIMEOUT_SECONDS = 4.0

FASHION_LABEL_TO_CATEGORY = {
    "T-shirt/top": "tops",
    "Trouser": "bottoms",
    "Pullover": "tops",
    "Dress": "dresses",
    "Coat": "tops",
    "Sandal": "shoes",
    "Shirt": "tops",
    "Sneaker": "shoes",
    "Bag": "accessories",
    "Ankle boot": "shoes",
}

FASHION_LABEL_TO_SUBTYPE = {
    "T-shirt/top": "t-shirt",
    "Trouser": "trousers",
    "Pullover": "sweater",
    "Dress": "dress",
    "Coat": "coat",
    "Sandal": "sandals",
    "Shirt": "shirt",
    "Sneaker": "sneakers",
    "Bag": "bag",
    "Ankle boot": "boots",
}

TARGET_CATEGORIES = ["tops", "bottoms", "shoes", "dresses", "accessories"]
STANDARD_COLOR_KEYWORDS = {
    "black": ["black"],
    "white": ["white", "ivory", "cream"],
    "red": ["red", "maroon", "burgundy", "crimson"],
    "blue": ["blue", "navy", "teal"],
    "green": ["green", "olive"],
    "yellow": ["yellow", "mustard", "gold"],
    "purple": ["purple", "violet", "lavender"],
    "pink": ["pink", "rose", "magenta"],
    "brown": ["brown", "beige", "tan", "khaki", "camel"],
    "gray": ["gray", "grey", "charcoal", "silver"],
    "orange": ["orange", "coral", "peach"],
}
SUBTYPE_KEYWORDS = [
    ("t-shirt", ["t shirt", "t-shirt", "tshirt", "tee"]),
    ("shirt", ["shirt", "button down", "button-down", "blouse"]),
    ("jeans", ["jeans", "jean", "denim"]),
    ("trousers", ["trousers", "trouser"]),
    ("pants", ["pants", "pant"]),
    ("shorts", ["shorts"]),
]
SUBTYPE_DISPLAY = {
    "t-shirt": "T-Shirt",
    "shirt": "Shirt",
    "jeans": "Jeans",
    "trousers": "Trousers",
    "pants": "Pants",
    "shorts": "Shorts",
}
SUBTYPE_CATEGORY = {
    "t-shirt": "tops",
    "shirt": "tops",
    "jeans": "bottoms",
    "trousers": "bottoms",
    "pants": "bottoms",
    "shorts": "bottoms",
}
CATEGORY_KEYWORDS = {
    "tops": ["shirt", "t shirt", "t-shirt", "tee", "blouse", "top", "hoodie", "sweater",
             "jacket", "coat", "cardigan", "polo", "tank top", "vest"],
    "bottoms": ["pants", "jeans", "trousers", "shorts", "skirt", "leggings"],
    "dresses": ["dress", "gown", "romper", "jumpsuit"],
    "shoes": ["shoes", "sneakers", "boots", "sandals", "heels", "loafers", "flats"],
    "accessories": ["hat", "cap", "scarf", "belt", "bag", "watch", "sunglasses", "tie"],
}

def _load_blip_model():
    """Load BLIP model and processor once. Called on first use."""
    global _blip_processor, _blip_model
    if _blip_processor is not None and _blip_model is not None:
        return

    try:
        from transformers import BlipProcessor, BlipForConditionalGeneration
        import torch

        logger.info("Loading BLIP model (Salesforce/blip-image-captioning-base)...")
        _blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        _blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
        _blip_model.eval()
        logger.info("BLIP model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load BLIP model: {e}")
        _blip_processor = None
        _blip_model = None


def _load_fashion_classifier():
    """Load the fashion image classifier once. Called on first use."""
    global _fashion_classifier_pipeline, _fashion_classifier_load_attempted
    if _fashion_classifier_load_attempted:
        return
    _fashion_classifier_load_attempted = True

    try:
        from transformers import pipeline
        import torch

        device = -1  # CPU only
        logger.info("Loading fashion classifier (%s)...", FASHION_CLASSIFIER_MODEL)
        _fashion_classifier_pipeline = pipeline(
            "image-classification",
            model=FASHION_CLASSIFIER_MODEL,
            device=device,
        )
        logger.info("Fashion classifier loaded successfully")
    except Exception as e:
        logger.error("Failed to load fashion classifier: %s", e)
        _fashion_classifier_pipeline = None


def classify_with_fashion_model(image_path: str) -> Dict[str, Any]:
    """
    Run the fashion classifier on an image and return structured predictions.

    Returns:
        Dict with keys: label, confidence, category, subtype, source
        Returns None-like dict if classifier unavailable or fails.
    """
    _load_fashion_classifier()

    if _fashion_classifier_pipeline is None:
        logger.warning("[fashion-classifier] Pipeline not available")
        return {"label": None, "confidence": 0.0, "category": "unknown", "subtype": "unknown", "source": "none"}

    try:
        from PIL import Image

        image = Image.open(image_path).convert("RGB")
        predictions = _fashion_classifier_pipeline(image)

        if not predictions:
            logger.info("[fashion-classifier] No predictions returned")
            return {"label": None, "confidence": 0.0, "category": "unknown", "subtype": "unknown", "source": "none"}

        top_pred = predictions[0]
        label = top_pred["label"]
        confidence = top_pred["score"]

        category = FASHION_LABEL_TO_CATEGORY.get(label, "unknown")
        subtype = FASHION_LABEL_TO_SUBTYPE.get(label, "unknown")

        logger.info("[fashion-classifier] Image: %s", image_path)
        logger.info("[fashion-classifier] Top prediction: label=%s, confidence=%.3f", label, confidence)
        logger.info("[fashion-classifier] All predictions: %s", [(p["label"], round(p["score"], 3)) for p in predictions[:5]])
        logger.info("[fashion-classifier] Mapped -> category=%s, subtype=%s", category, subtype)

        return {
            "label": label,
            "confidence": confidence,
            "category": category,
            "subtype": subtype,
            "source": "fashion-classifier",
            "all_predictions": predictions[:5],
        }

    except FileNotFoundError:
        logger.error("[fashion-classifier] Image file not found: %s", image_path)
        return {"label": None, "confidence": 0.0, "category": "unknown", "subtype": "unknown", "source": "none"}
    except Exception as e:
        logger.error("[fashion-classifier] Error classifying image: %s", e)
        return {"label": None, "confidence": 0.0, "category": "unknown", "subtype": "unknown", "source": "none"}


def merge_analysis_results(
    classifier_result: Dict[str, Any],
    blip_result: Dict[str, Any],
    filename_hints: Dict[str, str],
) -> Dict[str, Any]:
    """
    Merge outputs from the fashion classifier, BLIP captioning, and filename parsing.

    Priority order:
        1. Fashion classifier -> category/subtype (if confidence >= threshold)
        2. BLIP -> contextual captions, color, pattern, sleeve, category/subtype fallback
        3. Filename parsing -> final fallback only

    Returns a merged metadata dict with source attribution for each field.
    """
    merged = {
        "category": "unknown",
        "category_source": "none",
        "subtype": "unknown",
        "subtype_source": "none",
        "color": "unknown",
        "color_source": "none",
        "pattern": "solid",
        "sleeve_length": "unknown",
        "caption": "",
        "all_captions": [],
        "confidence": 0.0,
    }

    classifier_confidence = classifier_result.get("confidence", 0.0)
    classifier_is_strong = classifier_confidence >= FASHION_CLASSIFIER_CONFIDENCE_THRESHOLD

    # --- Category resolution ---
    if classifier_is_strong and classifier_result.get("category", "unknown") != "unknown":
        merged["category"] = classifier_result["category"]
        merged["category_source"] = f"fashion-classifier (conf={classifier_confidence:.3f})"
    elif blip_result.get("category", "unknown") != "unknown":
        merged["category"] = blip_result["category"]
        merged["category_source"] = "blip"
    elif filename_hints.get("category"):
        merged["category"] = filename_hints["category"]
        merged["category_source"] = "filename"

    # --- Subtype resolution ---
    if classifier_is_strong and classifier_result.get("subtype", "unknown") != "unknown":
        merged["subtype"] = classifier_result["subtype"]
        merged["subtype_source"] = f"fashion-classifier (conf={classifier_confidence:.3f})"
    elif blip_result.get("subtype", "unknown") != "unknown":
        merged["subtype"] = blip_result.get("subtype", "unknown")
        merged["subtype_source"] = "blip"

    # --- Color resolution (BLIP is primary for color, classifier doesn't provide it) ---
    if blip_result.get("color", "unknown") != "unknown":
        merged["color"] = blip_result["color"]
        merged["color_source"] = "blip"
    elif filename_hints.get("color"):
        merged["color"] = filename_hints["color"]
        merged["color_source"] = "filename"

    # --- Pattern and sleeve from BLIP ---
    merged["pattern"] = blip_result.get("pattern", "solid")
    merged["sleeve_length"] = blip_result.get("sleeve_length", "unknown")

    # --- Captions from BLIP ---
    merged["caption"] = blip_result.get("caption", "")
    merged["all_captions"] = blip_result.get("all_captions", [])

    # --- Confidence: use classifier confidence if strong, else BLIP-derived ---
    if classifier_is_strong:
        merged["confidence"] = classifier_confidence
    else:
        merged["confidence"] = blip_result.get("confidence", 0.0)

    logger.info("[merge] Classifier strong=%s (conf=%.3f, threshold=%.2f)",
                classifier_is_strong, classifier_confidence, FASHION_CLASSIFIER_CONFIDENCE_THRESHOLD)
    logger.info("[merge] Final -> category=%s (src=%s), subtype=%s (src=%s), color=%s (src=%s)",
                merged["category"], merged["category_source"],
                merged["subtype"], merged["subtype_source"],
                merged["color"], merged["color_source"])

    return merged


def analyze_clothing(image_path: str) -> Dict[str, Any]:
    """
    Analyze a clothing image using BLIP captioning and extract attributes.

    Args:
        image_path: Absolute or relative path to the clothing image file.

    Returns:
        Dict with keys: caption, color, category, pattern, sleeve_length
    """
    _load_blip_model()

    if _blip_processor is None or _blip_model is None:
        return {
            "caption": "",
            "color": "unknown",
            "category": "unknown",
            "pattern": "solid",
            "sleeve_length": "unknown",
            "error": "BLIP model not available"
        }

    try:
        from PIL import Image
        import torch

        image = Image.open(image_path).convert("RGB")

        # Use multiple prompts to get richer captions
        prompts = [
            "a photo of",
            "this is a clothing item:",
            "the color of this clothing is",
            "this is a piece of clothing called",
        ]

        captions = []
        for prompt in prompts:
            inputs = _blip_processor(image, text=prompt, return_tensors="pt")
            with torch.no_grad():
                output = _blip_model.generate(**inputs, max_new_tokens=50)
            caption = _blip_processor.decode(output[0], skip_special_tokens=True).strip()
            captions.append(caption)

        # Also generate an unconditional caption
        inputs = _blip_processor(image, return_tensors="pt")
        with torch.no_grad():
            output = _blip_model.generate(**inputs, max_new_tokens=50)
        unconditional = _blip_processor.decode(output[0], skip_special_tokens=True).strip()
        captions.append(unconditional)

        # Combine all captions for richer extraction
        combined_text = " | ".join(captions)
        primary_caption = captions[0]

        logger.info("[BLIP] Image: %s", image_path)
        logger.info("[BLIP] Captions generated: %s", captions)

        # Extract attributes from the combined text for better accuracy
        color = _extract_color(combined_text)
        category = _extract_category(combined_text)
        pattern = _extract_pattern(combined_text)
        sleeve_length = _extract_sleeve_length(combined_text)
        subtype = _extract_subtype(combined_text)
        confidence = compute_confidence(color, category, subtype)

        logger.info("[BLIP] Extracted -> color: %s, category: %s, pattern: %s, sleeve: %s, confidence: %s",
                    color, category, pattern, sleeve_length, confidence)

        return {
            "caption": primary_caption,
            "all_captions": captions,
            "color": color,
            "category": category,
            "pattern": pattern,
            "sleeve_length": sleeve_length,
            "confidence": confidence,
        }

    except FileNotFoundError:
        logger.error(f"Image file not found: {image_path}")
        return {
            "caption": "",
            "color": "unknown",
            "category": "unknown",
            "pattern": "solid",
            "sleeve_length": "unknown",
            "error": f"File not found: {image_path}"
        }
    except Exception as e:
        logger.error(f"Error analyzing clothing image: {e}")
        return {
            "caption": "",
            "color": "unknown",
            "category": "unknown",
            "pattern": "solid",
            "sleeve_length": "unknown",
            "error": str(e)
        }


def _normalize_caption_text(caption: str) -> str:
    normalized = caption.lower().replace("-", " ")
    normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
    return " ".join(normalized.split())


def _keyword_in_caption(normalized: str, keyword: str) -> bool:
    return re.search(rf"\b{re.escape(keyword)}\b", normalized) is not None


def _find_first_keyword(normalized: str, keywords: List[str]) -> Optional[str]:
    for keyword in keywords:
        if _keyword_in_caption(normalized, keyword):
            return keyword
    return None


def _run_with_timeout(fn, timeout_seconds: float):
    """Run a callable with a timeout, returning None on timeout or error."""
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(fn)
        try:
            return future.result(timeout=timeout_seconds)
        except FuturesTimeout:
            logger.warning("[light-suggest] Timed out after %.2fs", timeout_seconds)
            return None
        except Exception as exc:
            logger.error("[light-suggest] Error running suggestion task: %s", exc)
            return None


def _extract_subtype_from_filename(filename: str) -> str:
    normalized = filename.lower().replace('_', ' ').replace('-', ' ')
    normalized = re.sub(r'\.\w+$', '', normalized)
    for subtype, keywords in SUBTYPE_KEYWORDS:
        if _find_first_keyword(normalized, keywords):
            return subtype
    return "unknown"


def _extract_color(caption: str) -> str:
    """Extract the dominant color from a BLIP caption. Returns the earliest-occurring color."""
    normalized = _normalize_caption_text(caption)

    # Filter out background-related color mentions
    # e.g. "on white background", "white backdrop", "isolated on white"
    bg_patterns = [
        r"\bon\s+\w*\s*background\b",
        r"\bisolated\s+on\s+\w+\b",
        r"\b\w+\s+backdrop\b",
    ]
    cleaned = normalized
    for pattern in bg_patterns:
        cleaned = re.sub(pattern, "", cleaned)

    # Find the earliest color match by position
    earliest_pos = len(cleaned) + 1
    earliest_color = "unknown"

    for color, keywords in STANDARD_COLOR_KEYWORDS.items():
        for keyword in keywords:
            match = re.search(rf"\b{re.escape(keyword)}\b", cleaned)
            if match and match.start() < earliest_pos:
                earliest_pos = match.start()
                earliest_color = color

    return earliest_color


def _extract_subtype(caption: str) -> str:
    """Extract clothing subtype from a BLIP caption."""
    normalized = _normalize_caption_text(caption)
    for subtype, keywords in SUBTYPE_KEYWORDS:
        if _find_first_keyword(normalized, keywords):
            return subtype
    return "unknown"


def _extract_category(caption: str) -> str:
    """Extract clothing category from a BLIP caption."""
    normalized = _normalize_caption_text(caption)
    for category, keywords in CATEGORY_KEYWORDS.items():
        if _find_first_keyword(normalized, keywords):
            return category
    return "unknown"


def _format_clean_item_name(color: str, subtype: str) -> str:
    color_part = color.title() if color and color != "unknown" else ""
    subtype_part = SUBTYPE_DISPLAY.get(subtype, subtype.title()) if subtype and subtype != "unknown" else ""

    if color_part and subtype_part:
        return f"{color_part} {subtype_part}"
    if subtype_part:
        return subtype_part
    if color_part:
        return f"{color_part} Item"
    return "Stylish Item"


def _extract_clean_name_from_caption(caption: str, color: str = "", category: str = "") -> str:
    """Extract a short, clean clothing item name from a BLIP caption."""
    if not caption:
        return ""

    text = caption.lower().strip()

    # Strip common BLIP prefixes
    prefixes_to_strip = [
        "a photo of ", "a picture of ", "a close up of ",
        "a man wearing ", "a woman wearing ", "a person wearing ",
        "a man in ", "a woman in ", "a person in ",
        "a man with ", "a woman with ", "a person with ",
        "a young man wearing ", "a young woman wearing ",
        "a young man in ", "a young woman in ",
        "this is a clothing item: ", "this is a piece of clothing called ",
        "the color of this clothing is ",
    ]
    for prefix in prefixes_to_strip:
        if text.startswith(prefix):
            text = text[len(prefix):]
            break

    # Strip leading articles
    for article in ["a ", "an ", "the "]:
        if text.startswith(article):
            text = text[len(article):]
            break

    # Known clothing keywords to look for
    clothing_types = {
        "t-shirt": "T-Shirt", "t shirt": "T-Shirt", "tee": "T-Shirt", "tee shirt": "T-Shirt",
        "shirt": "Shirt", "dress shirt": "Dress Shirt", "button up": "Button-Up Shirt",
        "hoodie": "Hoodie", "sweatshirt": "Sweatshirt", "sweater": "Sweater",
        "jacket": "Jacket", "blazer": "Blazer", "coat": "Coat", "parka": "Parka",
        "vest": "Vest", "cardigan": "Cardigan", "polo": "Polo",
        "tank top": "Tank Top", "crop top": "Crop Top", "blouse": "Blouse",
        "jeans": "Jeans", "pants": "Pants", "trousers": "Trousers",
        "shorts": "Shorts", "skirt": "Skirt", "chinos": "Chinos", "joggers": "Joggers",
        "leggings": "Leggings", "cargo pants": "Cargo Pants",
        "dress": "Dress", "gown": "Gown", "jumpsuit": "Jumpsuit", "romper": "Romper",
        "sneakers": "Sneakers", "boots": "Boots", "sandals": "Sandals",
        "loafers": "Loafers", "heels": "Heels", "shoes": "Shoes",
        "hat": "Hat", "cap": "Cap", "beanie": "Beanie",
        "scarf": "Scarf", "belt": "Belt", "watch": "Watch",
        "bag": "Bag", "backpack": "Backpack", "sunglasses": "Sunglasses",
    }

    # Find the clothing type in the text
    matched_type = ""
    for keyword, display in sorted(clothing_types.items(), key=lambda x: -len(x[0])):
        if keyword in text:
            matched_type = display
            break

    # Build the clean name: Color + Type
    color_part = color.title() if color and color != "unknown" else ""

    if matched_type:
        if color_part:
            return f"{color_part} {matched_type}"
        return matched_type

    # Fallback: use category as the type
    category_display = {
        "tops": "Top", "bottoms": "Pants", "dresses": "Dress",
        "shoes": "Shoes", "accessories": "Accessory",
    }
    type_from_cat = category_display.get(category, "")
    if color_part and type_from_cat:
        return f"{color_part} {type_from_cat}"
    if type_from_cat:
        return type_from_cat

    return ""


def compute_confidence(color: str, category: str, subtype: str) -> float:
    """
    Compute a confidence score based on how many attributes were successfully extracted.
    Score: 0.0 (nothing found) to 1.0 (all attributes clear).
    """
    score = 0.0
    if color and color != "unknown":
        score += 0.35
    if category and category != "unknown":
        score += 0.40
    if subtype and subtype != "unknown":
        score += 0.25
    return round(score, 2)


def _parse_blip_caption(caption: str) -> Dict[str, str]:
    """Parse BLIP caption into normalized name, category, color, and subtype."""
    color = _extract_color(caption)
    subtype = _extract_subtype(caption)
    category = SUBTYPE_CATEGORY.get(subtype) or _extract_category(caption)
    name = _format_clean_item_name(color, subtype)

    return {
        "name": name,
        "category": category,
        "color": color,
        "subtype": subtype,
    }


def _extract_pattern(caption: str) -> str:
    """Extract pattern/print from a BLIP caption."""
    caption_lower = caption.lower()
    patterns = [
        "striped", "plaid", "checkered", "floral", "polka dot", "printed",
        "graphic", "camouflage", "paisley", "abstract", "geometric", "solid"
    ]
    for pattern in patterns:
        if pattern in caption_lower:
            return pattern
    return "solid"


def _extract_sleeve_length(caption: str) -> str:
    """Extract sleeve length from a BLIP caption."""
    caption_lower = caption.lower()
    if "long sleeve" in caption_lower or "long-sleeve" in caption_lower:
        return "long"
    if "short sleeve" in caption_lower or "short-sleeve" in caption_lower:
        return "short"
    if "sleeveless" in caption_lower or "tank" in caption_lower:
        return "sleeveless"
    if "half sleeve" in caption_lower or "3/4" in caption_lower:
        return "three-quarter"
    return "unknown"


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

    def classify_clothing_image(self, image_data: str, image_path: str = None, filename: str = "") -> Dict[str, Any]:
        """
        Classify a clothing image using the multi-model pipeline.

        Priority order:
            1. Fashion classifier (dima806/clothes_image_detection) -> category/subtype
            2. BLIP captioning -> color, pattern, sleeve, contextual tags
            3. Filename parsing -> final fallback only

        If classifier confidence is below threshold, BLIP extraction takes priority
        for category/subtype.
        """
        try:
            logger.info("[classify] === Starting multi-model classification ===")
            logger.info("[classify] filename: %s, has_image_path: %s", filename, bool(image_path))

            # --- Step 1: Run fashion classifier ---
            classifier_result = {"label": None, "confidence": 0.0, "category": "unknown", "subtype": "unknown", "source": "none"}
            if image_path:
                classifier_result = classify_with_fashion_model(image_path)

            # --- Step 2: Run BLIP captioning ---
            blip_metadata = None
            if image_path:
                blip_metadata = analyze_clothing(image_path)
                if blip_metadata.get("error"):
                    logger.warning("[classify] BLIP analysis failed: %s", blip_metadata['error'])
                    blip_metadata = None
                else:
                    logger.info("[classify] BLIP caption: %s", blip_metadata.get("caption"))
                    logger.info("[classify] BLIP extracted -> color: %s, category: %s, pattern: %s, subtype: %s",
                               blip_metadata.get("color"), blip_metadata.get("category"),
                               blip_metadata.get("pattern"), _extract_subtype(blip_metadata.get("caption", "")))

            # --- Step 3: Extract filename hints (last resort) ---
            filename_hints = self._extract_from_filename(filename) if filename else {}
            if filename_hints:
                logger.info("[classify] Filename hints: %s", filename_hints)

            # --- Step 4: Merge results using priority logic ---
            blip_for_merge = {}
            if blip_metadata:
                blip_for_merge = {
                    "color": blip_metadata.get("color", "unknown"),
                    "category": blip_metadata.get("category", "unknown"),
                    "subtype": _extract_subtype(blip_metadata.get("caption", "")),
                    "pattern": blip_metadata.get("pattern", "solid"),
                    "sleeve_length": blip_metadata.get("sleeve_length", "unknown"),
                    "caption": blip_metadata.get("caption", ""),
                    "all_captions": blip_metadata.get("all_captions", []),
                    "confidence": blip_metadata.get("confidence", 0.0),
                }

            merged = merge_analysis_results(classifier_result, blip_for_merge, filename_hints)

            merged_color = merged["color"]
            merged_category = merged["category"]
            merged_subtype = merged["subtype"]

            logger.info("[classify] Merged result -> category=%s (src=%s), color=%s (src=%s), subtype=%s (src=%s)",
                        merged_category, merged["category_source"],
                        merged_color, merged["color_source"],
                        merged_subtype, merged["subtype_source"])

            # --- Step 5: Use Cohere for final naming/tagging if available ---
            if blip_metadata and blip_metadata.get("caption"):
                cleaned_caption = " ".join(blip_metadata["caption"].split())
                safe_caption = json.dumps(cleaned_caption)

                all_captions = blip_metadata.get("all_captions", [])
                extra_context = ""
                if len(all_captions) > 1:
                    extra_context = f"\nAdditional vision model outputs: {json.dumps(all_captions[1:])}\n"

                classifier_context = ""
                if classifier_result.get("label"):
                    classifier_context = (
                        f"\nFashion classifier prediction: {classifier_result['label']} "
                        f"(confidence: {classifier_result['confidence']:.2f})\n"
                    )

                base_prompt = (
                    "You are an expert e-commerce fashion cataloging assistant. You will be given a raw text "
                    "description generated by a vision model. Your job is to extract clean metadata and return "
                    "a strict JSON object. "
                    "CRITICAL NAME REQUIREMENT: The 'name' property must be strictly formatted as "
                    "'[Main Color] [Specific Item Type]' (for example: 'Blue Pants', 'Black Jeans', "
                    "'White T-Shirt', 'Gray Hoodie'). Strip out all conversational filler words like "
                    "'a photo of', 'an image of', 'isolated on', 'pair of', or 'looking clean'. Do not write full sentences.\n\n"
                    "Example 1: Input Caption: \"a photo of a blue pair of loose fitting trousers\" -> "
                    "Output JSON: {\"name\": \"Blue Trousers\", \"category\": \"bottoms\", \"color\": \"blue\", "
                    "\"vibe\": \"casual\", \"tags\": [\"trousers\", \"loose\", \"blue\"]}\n"
                    "Example 2: Input Caption: \"black cotton casual t-shirt isolated on white background\" -> "
                    "Output JSON: {\"name\": \"Black T-Shirt\", \"category\": \"tops\", \"color\": \"black\", "
                    "\"vibe\": \"casual\", \"tags\": [\"cotton\", \"minimal\", \"everyday\"]}\n"
                    "Example 3: Input Caption: \"a man wearing black pants\" -> "
                    "Output JSON: {\"name\": \"Black Pants\", \"category\": \"bottoms\", \"color\": \"black\", "
                    "\"vibe\": \"casual\", \"tags\": [\"pants\", \"classic\", \"versatile\"]}\n\n"
                )
                classify_prompt = (
                    f"{base_prompt}"
                    f"Input Caption: {safe_caption}\n"
                    f"{extra_context}"
                    f"{classifier_context}"
                    f"Detected attributes - Color: {merged_color}, "
                    f"Category: {merged_category}, "
                    f"Subtype: {merged_subtype}, "
                    f"Pattern: {merged['pattern']}, "
                    f"Sleeve length: {merged['sleeve_length']}.\n"
                )
                if filename:
                    classify_prompt += f"Original filename (use as hint): \"{filename}\"\n"
                classify_prompt += (
                    "\nReturn ONLY a JSON object with these fields: "
                    "name, category (one of: tops/bottoms/dresses/shoes/accessories), "
                    "color (single main color as plain text), "
                    "vibe (one of: casual/formal/sporty/trendy/vintage), "
                    "tags (array of 3 descriptive words)."
                )
            else:
                classify_prompt = (
                    "You are an expert e-commerce fashion cataloging assistant. "
                    "Based on the filename and any available hints, infer the clothing item details.\n\n"
                    f"Filename: \"{filename}\"\n"
                    f"Detected color hint: {merged_color}\n"
                    f"Detected category hint: {merged_category}\n"
                    f"Detected subtype hint: {merged_subtype}\n\n"
                    "Return ONLY a JSON object with these fields: "
                    "name (format: '[Color] [Item Type]'), "
                    "category (one of: tops/bottoms/dresses/shoes/accessories), "
                    "color (single main color as plain text), "
                    "vibe (one of: casual/formal/sporty/trendy/vintage), "
                    "tags (array of 3 descriptive words)."
                )

            if self.cohere_api_key:
                result_text = self._query_cohere(classify_prompt)
                if result_text:
                    json_start = result_text.find('{')
                    json_end = result_text.rfind('}') + 1
                    if json_start != -1 and json_end > json_start:
                        parsed = json.loads(result_text[json_start:json_end])
                        parsed = parsed if isinstance(parsed, dict) else {}

                        cohere_category = (parsed.get("category", "") or "").strip().lower()
                        cohere_color = (parsed.get("color", "") or "").strip().lower()

                        # Validate category — merged pipeline result takes precedence over invalid Cohere output
                        if cohere_category not in TARGET_CATEGORIES:
                            cohere_category = merged_category if merged_category != "unknown" else "tops"

                        # Validate color
                        valid_colors = set(STANDARD_COLOR_KEYWORDS.keys())
                        if cohere_color not in valid_colors:
                            cohere_color = merged_color if merged_color != "unknown" else ""

                        result = {
                            "name": parsed.get("name", ""),
                            "category": cohere_category,
                            "color": cohere_color,
                            "vibe": (parsed.get("vibe", "casual") or "casual").strip().lower(),
                            "tags": parsed.get("tags", []) if isinstance(parsed.get("tags", []), list) else [],
                        }

                        if not result["name"] or result["name"] == "Stylish Item":
                            result["name"] = self._build_item_name(result["color"], result["category"], filename)

                        # Use merged subtype for better naming
                        if merged_subtype != "unknown":
                            built_name = _format_clean_item_name(
                                result["color"] or merged_color,
                                merged_subtype
                            )
                            if built_name != "Stylish Item":
                                result["name"] = built_name
                        elif blip_metadata:
                            parsed_caption = _parse_blip_caption(blip_metadata["caption"])
                            if parsed_caption["subtype"] != "unknown":
                                built_name = _format_clean_item_name(
                                    result["color"] or parsed_caption["color"],
                                    parsed_caption["subtype"]
                                )
                                if built_name != "Stylish Item":
                                    result["name"] = built_name

                        # Attach pipeline metadata
                        if blip_metadata:
                            result["blip_caption"] = blip_metadata["caption"]
                            result["blip_attributes"] = {
                                "color": blip_metadata["color"],
                                "category": blip_metadata["category"],
                                "pattern": blip_metadata["pattern"],
                                "sleeve_length": blip_metadata["sleeve_length"],
                            }
                        if classifier_result.get("label"):
                            result["classifier_prediction"] = {
                                "label": classifier_result["label"],
                                "confidence": classifier_result["confidence"],
                                "category": classifier_result["category"],
                                "subtype": classifier_result["subtype"],
                            }
                        result["analysis_sources"] = {
                            "category_source": merged["category_source"],
                            "color_source": merged["color_source"],
                            "subtype_source": merged["subtype_source"],
                        }

                        logger.info("[classify] Final result (Cohere enriched): %s", result)
                        return result

            # --- Fallback: no Cohere, use merged pipeline directly ---
            final_category = merged_category if merged_category != "unknown" else "tops"
            final_color = merged_color if merged_color != "unknown" else ""

            # Build name from merged subtype
            if merged_subtype != "unknown":
                final_name = _format_clean_item_name(final_color, merged_subtype)
            elif blip_metadata and blip_metadata.get("caption"):
                parsed_caption = _parse_blip_caption(blip_metadata["caption"])
                final_name = parsed_caption["name"]
            else:
                final_name = "Stylish Item"

            if final_name == "Stylish Item":
                final_name = self._build_item_name(final_color, final_category, filename)

            result = {
                "name": final_name,
                "category": final_category,
                "color": final_color,
                "vibe": "casual",
                "tags": [merged["pattern"], merged["sleeve_length"], "ai-detected"],
            }
            if blip_metadata:
                result["blip_caption"] = blip_metadata.get("caption", "")
                result["blip_attributes"] = {
                    "color": blip_metadata["color"],
                    "category": blip_metadata["category"],
                    "pattern": blip_metadata["pattern"],
                    "sleeve_length": blip_metadata["sleeve_length"],
                }
            if classifier_result.get("label"):
                result["classifier_prediction"] = {
                    "label": classifier_result["label"],
                    "confidence": classifier_result["confidence"],
                    "category": classifier_result["category"],
                    "subtype": classifier_result["subtype"],
                }
            result["analysis_sources"] = {
                "category_source": merged["category_source"],
                "color_source": merged["color_source"],
                "subtype_source": merged["subtype_source"],
            }

            logger.info("[classify] Final result (pipeline fallback, no Cohere): %s", result)
            return result

        except Exception as e:
            logger.error("[classify] Error in classify_clothing_image: %s", e)
            if filename:
                hints = self._extract_from_filename(filename)
                return {
                    "name": self._build_item_name(hints.get("color", ""), hints.get("category", ""), filename),
                    "category": hints.get("category", "tops"),
                    "color": hints.get("color", ""),
                    "vibe": "casual",
                    "tags": ["uploaded", "wardrobe", "clothing"],
                }
            return {
                "name": "Clothing Item",
                "category": "tops",
                "color": "",
                "vibe": "casual",
                "tags": ["uploaded", "wardrobe", "clothing"],
            }

    def suggest_clothing_lightweight(self, image_path: str = None, filename: str = "") -> Dict[str, Any]:
        """Return AI suggestions using fashion classifier, filename hints, and BLIP fallback."""
        suggestions = {"name": "", "category": "", "color": "", "vibe": "", "tags": []}
        sources: Dict[str, str] = {}
        confidence = 0.0
        timed_out = False

        filename_hints = self._extract_from_filename(filename) if filename else {}
        subtype_hint = _extract_subtype_from_filename(filename) if filename else "unknown"

        classifier_result = None
        if image_path:
            classifier_result = _run_with_timeout(
                lambda: classify_with_fashion_model(image_path),
                LIGHT_SUGGESTION_TIMEOUT_SECONDS,
            )
            if classifier_result is None:
                timed_out = True

        candidate = {"name": "", "category": "", "color": "", "vibe": "", "tags": []}
        candidate_sources: Dict[str, str] = {}

        if classifier_result and classifier_result.get("confidence", 0.0) >= LIGHT_SUGGESTION_CONFIDENCE_THRESHOLD:
            confidence = float(classifier_result.get("confidence", 0.0))
            category = classifier_result.get("category", "unknown")
            subtype = classifier_result.get("subtype", "unknown")
            if subtype != "unknown":
                category = SUBTYPE_CATEGORY.get(subtype, category)
            if category in TARGET_CATEGORIES:
                candidate["category"] = category
                candidate_sources["category"] = "fashion-classifier"
            if filename_hints.get("color"):
                candidate["color"] = filename_hints["color"]
                candidate_sources["color"] = "filename"
            if subtype != "unknown":
                candidate["tags"] = [subtype]
                candidate_sources["tags"] = "fashion-classifier"
                candidate["name"] = _format_clean_item_name(candidate["color"], subtype)
                candidate_sources["name"] = "fashion-classifier"
        elif subtype_hint != "unknown":
            confidence = 0.65
            category = SUBTYPE_CATEGORY.get(subtype_hint, filename_hints.get("category", ""))
            if category in TARGET_CATEGORIES:
                candidate["category"] = category
                candidate_sources["category"] = "filename"
            if filename_hints.get("color"):
                candidate["color"] = filename_hints["color"]
                candidate_sources["color"] = "filename"
            candidate["tags"] = [subtype_hint]
            candidate_sources["tags"] = "filename"
            candidate["name"] = _format_clean_item_name(candidate["color"], subtype_hint)
            candidate_sources["name"] = "filename"
        elif filename_hints.get("category") and filename_hints.get("color"):
            confidence = 0.6
            category = filename_hints.get("category")
            if category in TARGET_CATEGORIES:
                candidate["category"] = category
                candidate_sources["category"] = "filename"
            candidate["color"] = filename_hints["color"]
            candidate_sources["color"] = "filename"

        low_confidence = confidence < LIGHT_SUGGESTION_CONFIDENCE_THRESHOLD

        # BLIP fallback: if classifier and filename didn't produce confident results, use BLIP
        if low_confidence and image_path:
            try:
                blip_result = analyze_clothing(image_path)
                if blip_result and not blip_result.get("error"):
                    blip_confidence = blip_result.get("confidence", 0.0)
                    blip_category = blip_result.get("category", "unknown")
                    blip_color = blip_result.get("color", "unknown")
                    blip_caption = blip_result.get("caption", "")

                    if blip_category != "unknown" and blip_category in TARGET_CATEGORIES:
                        candidate["category"] = blip_category
                        candidate_sources["category"] = "blip"
                    if blip_color != "unknown":
                        candidate["color"] = blip_color
                        candidate_sources["color"] = "blip"
                    if blip_caption:
                        name = _extract_clean_name_from_caption(blip_caption, blip_color, blip_category)
                        if name:
                            candidate["name"] = name
                            candidate_sources["name"] = "blip"

                    pattern = blip_result.get("pattern", "solid")
                    if pattern and pattern != "solid":
                        candidate["tags"] = candidate.get("tags", []) + [pattern]
                        candidate_sources["tags"] = "blip"

                    # Infer vibe from category
                    vibe_map = {"dresses": "trendy", "accessories": "trendy", "shoes": "casual"}
                    if candidate["category"]:
                        candidate["vibe"] = vibe_map.get(candidate["category"], "casual")
                        candidate_sources["vibe"] = "inferred"

                    confidence = max(confidence, blip_confidence if blip_confidence else 0.6)
                    low_confidence = confidence < LIGHT_SUGGESTION_CONFIDENCE_THRESHOLD
            except Exception as e:
                logger.warning("[suggest-clothing] BLIP fallback failed: %s", e)

        if not low_confidence:
            suggestions = candidate
            sources = candidate_sources

        return {
            "suggestions": suggestions,
            "confidence": confidence,
            "timed_out": timed_out,
            "low_confidence": low_confidence,
            "sources": sources,
        }

    # --- Internal Outfit Role Normalization ---

    OUTFIT_ROLE_MAP = {
        # Category-based mapping
        "tops": "top",
        "bottoms": "bottom",
        "dresses": "top",
        "shoes": "shoes",
        "accessories": "accessory",
    }

    LAYER_KEYWORDS = ["jacket", "coat", "blazer", "cardigan", "hoodie", "parka", "puffer",
                      "windbreaker", "overshirt", "bomber", "vest", "fleece", "denim jacket"]

    NAME_TO_ROLE = {
        "top": ["shirt", "tshirt", "t-shirt", "tee", "top", "blouse", "polo", "tank",
                "crop top", "henley", "tunic", "camisole", "sweater", "sweatshirt", "pullover"],
        "bottom": ["jeans", "pants", "trousers", "shorts", "skirt", "chinos", "joggers",
                   "leggings", "cargo", "culottes", "slacks"],
        "shoes": ["sneakers", "boots", "sandals", "loafers", "heels", "shoes", "shoe",
                  "trainers", "slides", "mules", "oxfords", "flats", "espadrilles"],
        "layer": ["jacket", "coat", "blazer", "cardigan", "hoodie", "parka", "puffer",
                  "windbreaker", "overshirt", "bomber", "vest", "fleece", "denim jacket",
                  "trench", "overcoat", "anorak"],
        "accessory": ["hat", "cap", "beanie", "scarf", "belt", "watch", "bag", "backpack",
                      "sunglasses", "bracelet", "necklace", "ring", "tie", "bow tie",
                      "gloves", "earrings"],
    }

    def _resolve_outfit_role(self, item: Dict) -> str:
        """Resolve an item's internal outfit role from its category and name."""
        name = (item.get('name') or '').lower()
        category = (item.get('category') or '').lower()

        # Check name against layer keywords first (layers are often stored as "tops")
        for kw in self.LAYER_KEYWORDS:
            if kw in name:
                return "layer"

        # Check name against all role keywords
        for role, keywords in self.NAME_TO_ROLE.items():
            for kw in keywords:
                if kw in name:
                    return role

        # Fall back to category mapping
        return self.OUTFIT_ROLE_MAP.get(category, "accessory")

    def _sanitize_wardrobe(self, wardrobe: List[Dict]) -> List[Dict]:
        """Filter out malformed items and normalize categories internally."""
        sanitized = []
        seen_urls = set()
        seen_filenames = set()
        seen_hashes = set()

        for item in wardrobe:
            if not isinstance(item, dict):
                continue
            name = item.get('name', '').strip()
            if not name:
                continue

            # Check duplicates
            image_url = item.get('image', '')
            image_hash = item.get('imageHash', '')

            is_duplicate = False
            if image_url:
                if image_url in seen_urls:
                    is_duplicate = True
                
                filename = _get_filename_from_url(image_url)
                if filename and filename in seen_filenames:
                    is_duplicate = True

            if not is_duplicate and image_hash:
                for seen_hash in seen_hashes:
                    if _hamming_distance(image_hash, seen_hash) <= 8:
                        is_duplicate = True
                        break

            if is_duplicate:
                logger.info(
                    "[sanitize_wardrobe] Skipping duplicate wardrobe item: name=%s, image=%s, imageHash=%s",
                    name, image_url, image_hash
                )
                continue

            # Record as seen
            if image_url:
                seen_urls.add(image_url)
                filename = _get_filename_from_url(image_url)
                if filename:
                    seen_filenames.add(filename)
            if image_hash:
                seen_hashes.add(image_hash)

            # Must have at least a name to be usable
            sanitized_item = dict(item)
            sanitized_item['_outfit_role'] = self._resolve_outfit_role(item)

            # Auto-fix obvious category mismatches
            role = sanitized_item['_outfit_role']
            stored_cat = (item.get('category') or '').lower()
            role_to_category = {
                "top": "tops", "bottom": "bottoms", "shoes": "shoes",
                "layer": "tops", "accessory": "accessories",
            }
            expected_cat = role_to_category.get(role, "accessories")
            if stored_cat not in ["tops", "bottoms", "dresses", "shoes", "accessories"]:
                sanitized_item['category'] = expected_cat

            sanitized.append(sanitized_item)
        return sanitized

    def _analyze_wardrobe_health(self, wardrobe: List[Dict]) -> Dict[str, Any]:
        """Analyze wardrobe completeness for outfit generation."""
        roles = {"top": [], "bottom": [], "shoes": [], "layer": [], "accessory": []}
        for item in wardrobe:
            role = item.get('_outfit_role', self._resolve_outfit_role(item))
            if role in roles:
                roles[role].append(item.get('name', ''))

        warnings = []
        if not roles["top"]:
            warnings.append("No tops found — add shirts, tees, or sweaters for complete outfits.")
        if not roles["bottom"]:
            warnings.append("No bottoms found — add pants, jeans, or shorts for complete outfits.")
        if not roles["shoes"]:
            warnings.append("No shoes found — add sneakers, boots, or sandals to complete your looks.")

        total_items = sum(len(v) for v in roles.values())
        if total_items < 4:
            warnings.append("Low wardrobe diversity — add more items for better outfit variety.")

        can_generate = bool(roles["top"]) and bool(roles["bottom"])

        return {
            "warnings": warnings,
            "can_generate": can_generate,
            "counts": {role: len(items) for role, items in roles.items()},
        }

    def _repair_outfit_roles(self, items: List[str], wardrobe_roles: Dict[str, str]) -> Optional[List[str]]:
        """Keep only the first item per strict role (top/bottom/shoes). Allow 1 layer, unlimited accessories."""
        seen_strict = {}
        layer_count = 0
        repaired = []
        for item_name in items:
            role = wardrobe_roles.get(item_name.lower(), 'accessory')
            if role == 'accessory':
                repaired.append(item_name)
            elif role == 'layer':
                if layer_count < 1:
                    repaired.append(item_name)
                    layer_count += 1
            else:
                if role not in seen_strict:
                    seen_strict[role] = item_name
                    repaired.append(item_name)
        return repaired if len(repaired) >= 2 else None

    def _validate_outfit_completeness(self, outfits: List[Dict], wardrobe: List[Dict]) -> List[Dict]:
        """Ensure each outfit has valid role composition: max 1 top, 1 bottom, 1 shoes."""
        wardrobe_roles = {}
        for item in wardrobe:
            name = item.get('name', '')
            role = item.get('_outfit_role', self._resolve_outfit_role(item))
            wardrobe_roles[name.lower()] = role

        valid_outfits = []
        for outfit in outfits:
            items = outfit.get('items', [])
            if len(items) < 2:
                continue

            # Count items per role
            role_counts = Counter()
            for item_name in items:
                role = wardrobe_roles.get(item_name.lower(), 'accessory')
                role_counts[role] += 1

            # Enforce strict limits: max 1 top, max 1 bottom, max 1 shoes
            if role_counts.get('top', 0) > 1 or role_counts.get('bottom', 0) > 1 or role_counts.get('shoes', 0) > 1:
                repaired = self._repair_outfit_roles(items, wardrobe_roles)
                if repaired:
                    outfit = dict(outfit)
                    outfit['items'] = repaired
                    # Recount after repair
                    role_counts = Counter()
                    for item_name in repaired:
                        role = wardrobe_roles.get(item_name.lower(), 'accessory')
                        role_counts[role] += 1
                else:
                    continue

            # Must have top (or layer as substitute) AND bottom
            has_top = role_counts.get('top', 0) >= 1 or role_counts.get('layer', 0) >= 1
            has_bottom = role_counts.get('bottom', 0) >= 1

            if has_top and has_bottom:
                valid_outfits.append(outfit)

        return valid_outfits if valid_outfits else outfits[:1]

    # --- Personalization Memory ---

    def _compute_user_preferences(self, saved_outfits: List[Dict], wardrobe: List[Dict], occasion: str) -> Dict[str, Any]:
        """Derive user preferences from saved outfit history."""
        if not saved_outfits:
            return {
                "favorite_colors": [],
                "preferred_occasion": occasion,
                "overused_items": [],
                "underused_items": [item.get('name', '') for item in wardrobe],
                "color_affinity": {},
                "total_saves": 0,
                "recent_combos": [],
            }

        # Count item usage across all saved outfits
        item_counts = Counter()
        for outfit in saved_outfits:
            items = outfit.get('items', [])
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, str):
                        item_counts[item] += 1

        # Count occasion preferences
        occasion_counts = Counter()
        for outfit in saved_outfits:
            occ = outfit.get('occasion', '')
            if occ:
                occasion_counts[occ] += 1

        # Favorite colors from wardrobe items that appear in saved outfits
        wardrobe_lookup = {item.get('name', '').lower(): item for item in wardrobe}
        color_counts = Counter()
        for item_name, count in item_counts.items():
            item_data = wardrobe_lookup.get(item_name.lower())
            if item_data:
                color = (item_data.get('color') or '').lower()
                if color and color != 'unknown':
                    color_counts[color] += count

        favorite_colors = [color for color, _ in color_counts.most_common(3)]

        # Overused items (appear in 3+ saved outfits)
        overused_items = [name for name, count in item_counts.items() if count >= 3]

        # Underused items (never appear in any saved outfit)
        all_used_items = set(item_counts.keys())
        underused_items = [item.get('name', '') for item in wardrobe
                          if item.get('name', '') and item.get('name', '') not in all_used_items]

        # Color affinity by family
        color_family_map = {
            "black": "neutrals", "white": "neutrals", "gray": "neutrals",
            "grey": "neutrals", "beige": "neutrals", "cream": "neutrals",
            "navy": "neutrals", "brown": "neutrals", "tan": "neutrals",
            "red": "warm", "orange": "warm", "yellow": "warm",
            "coral": "warm", "burgundy": "warm", "rust": "warm", "gold": "warm",
            "blue": "cool", "green": "cool", "purple": "cool",
            "teal": "cool", "lavender": "cool", "mint": "cool",
            "olive": "earth", "khaki": "earth", "camel": "earth", "forest": "earth",
        }
        family_counts = Counter()
        total_color_refs = 0
        for color, count in color_counts.items():
            family = color_family_map.get(color, "other")
            family_counts[family] += count
            total_color_refs += count

        color_affinity = {}
        if total_color_refs > 0:
            for family, count in family_counts.items():
                color_affinity[family] = round(count / total_color_refs, 2)

        # Preferred occasion
        preferred_occasion = occasion_counts.most_common(1)[0][0] if occasion_counts else occasion

        # Recent combos (for current occasion, last 5)
        recent_combos = []
        for outfit in saved_outfits:
            if outfit.get('occasion', '') == occasion:
                items = outfit.get('items', [])
                if isinstance(items, list) and items:
                    recent_combos.append(items)
        recent_combos = recent_combos[:5]

        return {
            "favorite_colors": favorite_colors,
            "preferred_occasion": preferred_occasion,
            "overused_items": overused_items,
            "underused_items": underused_items,
            "color_affinity": color_affinity,
            "total_saves": len(saved_outfits),
            "recent_combos": recent_combos,
        }

    def _build_personalization_context(self, preferences: Dict[str, Any]) -> str:
        """Generate prompt section from user preferences."""
        if preferences.get('total_saves', 0) == 0:
            return "- This is a new user — surprise them with creative, varied combinations"

        lines = ["USER STYLE PREFERENCES (learned from saved outfits):"]

        if preferences.get('favorite_colors'):
            lines.append(f"- Favorite colors: {', '.join(preferences['favorite_colors'])}")

        if preferences.get('preferred_occasion'):
            lines.append(f"- Tends toward: {preferences['preferred_occasion']} style")

        if preferences.get('overused_items'):
            overused = preferences['overused_items'][:4]
            lines.append(f"- Overused items (use sparingly, try alternatives): {', '.join(overused)}")

        if preferences.get('underused_items'):
            underused = preferences['underused_items'][:4]
            lines.append(f"- Underused items (try incorporating these): {', '.join(underused)}")

        lines.append("- Balance familiar favorites with fresh combinations to keep things interesting")

        # Exclusion from recent combos
        if preferences.get('recent_combos'):
            recent_str = "; ".join([", ".join(items[:3]) for items in preferences['recent_combos'][:5]])
            lines.append(f"- AVOID repeating these recent saves: [{recent_str}]")

        return '\n'.join(lines)

    def _score_and_rank_outfits(self, outfits: List[Dict], preferences: Dict[str, Any], wardrobe: List[Dict]) -> List[Dict]:
        """Score outfits based on personalization and sort by score."""
        if not outfits or preferences.get('total_saves', 0) == 0:
            return outfits

        wardrobe_lookup = {item.get('name', '').lower(): item for item in wardrobe}
        overused = set(name.lower() for name in preferences.get('overused_items', []))
        underused = set(name.lower() for name in preferences.get('underused_items', []))
        fav_colors = set(preferences.get('favorite_colors', []))
        recent_combos = preferences.get('recent_combos', [])

        scored = []
        for outfit in outfits:
            score = 5.0
            items = outfit.get('items', [])

            for item_name in items:
                item_lower = item_name.lower()
                # Freshness
                if item_lower in underused:
                    score += 1.5
                if item_lower in overused:
                    score -= 1.0

                # Color affinity
                item_data = wardrobe_lookup.get(item_lower)
                if item_data:
                    color = (item_data.get('color') or '').lower()
                    if color in fav_colors:
                        score += 0.5

            # Variety penalty: penalize high overlap with recent saves
            for recent in recent_combos:
                recent_set = set(r.lower() for r in recent)
                outfit_set = set(i.lower() for i in items)
                if recent_set and outfit_set:
                    overlap = len(recent_set & outfit_set) / max(len(outfit_set), 1)
                    if overlap >= 0.8:
                        score -= 2.0
                        break
                    elif overlap >= 0.5:
                        score -= 0.5

            # Completeness bonus
            roles_in_outfit = set()
            for item_name in items:
                item_data = wardrobe_lookup.get(item_name.lower())
                if item_data:
                    role = item_data.get('_outfit_role', self._resolve_outfit_role(item_data))
                    roles_in_outfit.add(role)
            if len(roles_in_outfit) >= 4:
                score += 1.0
            elif len(roles_in_outfit) >= 3:
                score += 0.5

            outfit['_score'] = round(score, 1)
            scored.append(outfit)

        scored.sort(key=lambda x: -x.get('_score', 0))
        return scored

    def generate_outfit_recommendation(self, wardrobe: List[Dict], weather: Dict, occasion: str, saved_outfits: List[Dict] = None) -> Dict[str, Any]:
        """Generate AI-powered outfit recommendations (3 outfits) with diversity and personalization."""
        try:
            if not wardrobe:
                return {"error": "No wardrobe items available"}

            # Sanitize and normalize wardrobe
            wardrobe = self._sanitize_wardrobe(wardrobe)
            if not wardrobe:
                return {"error": "No valid wardrobe items found"}

            # Wardrobe health check
            health = self._analyze_wardrobe_health(wardrobe)
            if not health["can_generate"]:
                return {
                    "error": "Insufficient wardrobe items for outfit generation",
                    "warnings": health["warnings"],
                    "health": health,
                }

            # --- STYLE SCORING: Filter wardrobe BEFORE generation ---
            logger.info("[style-scoring] Computing style scores for %d items, occasion=%s",
                        len(wardrobe), occasion)
            style_accepted, style_rejected = style_scoring.filter_wardrobe_by_style(wardrobe, occasion)

            if style_accepted:
                # Use only style-compatible items for generation
                filtered_wardrobe = style_accepted
                if style_rejected:
                    rejected_names = [item.get("name", "?") for item in style_rejected]
                    logger.info("[style-scoring] Filtered out %d items: %s",
                                len(style_rejected), rejected_names[:10])
                    health.setdefault("warnings", [])
                    if len(style_rejected) > 3:
                        health["warnings"].append(
                            f"{len(style_rejected)} items filtered out as incompatible with {occasion} style."
                        )
            else:
                # Fallback: use full wardrobe if filtering removes everything
                logger.warning("[style-scoring] All items filtered out — using full wardrobe as fallback")
                filtered_wardrobe = wardrobe

            # Compute personalization preferences
            preferences = self._compute_user_preferences(saved_outfits or [], wardrobe, occasion)

            wardrobe_context = self._prepare_wardrobe_for_recommendation(filtered_wardrobe)
            color_context = self._compute_color_context(filtered_wardrobe)
            weather_rules = self._get_weather_rules(weather)
            personalization_context = self._build_personalization_context(preferences)

            style_guidance = {
                "casual": (
                    "Relaxed, comfortable everyday looks. Prioritize clean basics, soft textures, "
                    "and effortless layering. Prefer sneakers or loafers over formal shoes. "
                    "Avoid structured blazers or stiff fabrics. Mix one interesting piece with "
                    "simple basics. Think weekend brunch, coffee run, casual hangout."
                ),
                "formal": (
                    "Polished, structured outfits for professional or dressy events. Prioritize "
                    "tailored fits, refined color palettes, and clean lines. Prefer leather shoes "
                    "or heels. Avoid graphic tees, sneakers, oversized items, or athletic wear. "
                    "Think business meeting, dinner reservation, gallery opening."
                ),
                "streetwear": (
                    "Bold, urban-inspired outfits with statement pieces. Mix oversized silhouettes "
                    "with fitted items. Layer aggressively. Prefer sneakers, graphic elements, "
                    "and bold accessories. Combine high and low pieces. Avoid conservative or "
                    "matchy-matchy pairings. Think hype culture, skate park, concert."
                ),
                "monochrome": (
                    "Outfits built around a SINGLE color family or tonal palette. Every piece "
                    "must be the same color or a shade/tint of it. Use different textures and "
                    "materials to create visual depth within the same hue. Avoid contrasting "
                    "colors entirely. Think tonal dressing, editorial, minimalist."
                ),
            }

            style_desc = style_guidance.get(occasion, f"Outfits suited for a {occasion} setting.")

            recommendation_prompt = (
                f"You are a professional fashion stylist creating {occasion} outfits.\n\n"
                f"WARDROBE (grouped by category):\n{wardrobe_context}\n\n"
                f"COLOR PALETTE AVAILABLE:\n{color_context}\n\n"
                f"STYLE DIRECTION ({occasion}):\n{style_desc}\n\n"
                f"WEATHER CONSIDERATION:\n{weather_rules}\n\n"
                f"{personalization_context}\n\n"
                f"DIVERSITY REQUIREMENTS:\n"
                f"- Each outfit MUST use different key pieces — do NOT repeat the same top or bottom across outfits\n"
                f"- Vary the color stories across all 3 outfits\n"
                f"- Each outfit should feel like a distinct look, not a minor variation\n\n"
                f"RULES:\n"
                f"- ONLY use exact item names from the wardrobe above\n"
                f"- NEVER include 2 items of the same type (no pants+shorts, no 2 shoes, no 2 shirts)\n"
                f"- Each outfit: exactly 1 top, exactly 1 bottom, exactly 1 pair of shoes, optionally 1 layer and accessories\n"
                f"- Add accessories or layers when they enhance the look\n"
                f"- Make each outfit distinctly different in mood, color palette, and silhouette\n\n"
                f"Return EXACTLY 3 outfits as a JSON array:\n"
                f'[{{"items":["exact name 1","exact name 2",...],"styling_tip":"one actionable styling tip","color_story":"describe the color harmony and why these colors work together","why_it_works":"explain how this fits {occasion} style and the current weather"}}]'
            )

            if self.cohere_api_key:
                result = self._query_cohere(recommendation_prompt)
                if result:
                    try:
                        arr_start = result.find('[')
                        arr_end = result.rfind(']') + 1
                        if arr_start != -1 and arr_end > arr_start:
                            parsed_result = json.loads(result[arr_start:arr_end])
                            if isinstance(parsed_result, list):
                                validated = self._validate_outfits(parsed_result, filtered_wardrobe)
                                diverse = self._ensure_diversity(validated, filtered_wardrobe)
                                complete = self._validate_outfit_completeness(diverse, filtered_wardrobe)
                                style_valid = style_scoring.validate_outfits_style(complete, occasion, filtered_wardrobe)
                                ranked = self._score_and_rank_outfits(style_valid, preferences, filtered_wardrobe)
                                ranked = fashionclip_service.rank_outfits(ranked, occasion, filtered_wardrobe)
                                self._log_outfit_style_debug(ranked, occasion, filtered_wardrobe)
                                return {"outfits": ranked, "warnings": health.get("warnings", [])}

                        json_start = result.find('{')
                        json_end = result.rfind('}') + 1
                        if json_start != -1 and json_end > json_start:
                            parsed_result = json.loads(result[json_start:json_end])
                            if isinstance(parsed_result, dict) and isinstance(parsed_result.get("outfits"), list):
                                validated = self._validate_outfits(parsed_result["outfits"], filtered_wardrobe)
                                diverse = self._ensure_diversity(validated, filtered_wardrobe)
                                complete = self._validate_outfit_completeness(diverse, filtered_wardrobe)
                                style_valid = style_scoring.validate_outfits_style(complete, occasion, filtered_wardrobe)
                                ranked = self._score_and_rank_outfits(style_valid, preferences, filtered_wardrobe)
                                ranked = fashionclip_service.rank_outfits(ranked, occasion, filtered_wardrobe)
                                self._log_outfit_style_debug(ranked, occasion, filtered_wardrobe)
                                return {"outfits": ranked, "warnings": health.get("warnings", [])}
                    except json.JSONDecodeError:
                        logger.error("Failed to parse outfit recommendation JSON")

            fallback = self._fallback_outfit_recommendation(filtered_wardrobe, weather, occasion, preferences)
            fallback["warnings"] = health.get("warnings", [])
            fallback["outfits"] = style_scoring.validate_outfits_style(
                fallback.get("outfits", []), occasion, filtered_wardrobe
            )
            fallback["outfits"] = fashionclip_service.rank_outfits(
                fallback.get("outfits", []), occasion, filtered_wardrobe
            )
            self._log_outfit_style_debug(fallback.get("outfits", []), occasion, filtered_wardrobe)
            return fallback

        except Exception as e:
            logger.error(f"Error generating outfit recommendation: {e}")
            fallback = self._fallback_outfit_recommendation(wardrobe, weather, occasion)
            fallback["outfits"] = fashionclip_service.rank_outfits(
                fallback.get("outfits", []), occasion, wardrobe
            )
            return fallback

    def _log_outfit_style_debug(self, outfits: List[Dict], occasion: str, wardrobe: List[Dict]) -> None:
        """Log detailed style scoring debug info for final outfits."""
        wardrobe_lookup = {item.get("name", "").lower(): item for item in wardrobe}

        logger.info("[style-debug] === Final Outfit Style Report (occasion=%s) ===", occasion)
        for idx, outfit in enumerate(outfits):
            items = outfit.get("items", [])
            coherence_info = outfit.get("_style_coherence", {})
            aggregate = coherence_info.get("aggregate_score", "N/A")

            logger.info("[style-debug] Outfit #%d: items=%s", idx + 1, items)
            logger.info("[style-debug]   aggregate_style_score=%s", aggregate)

            per_item = coherence_info.get("per_item_scores", {})
            for item_name, score_info in per_item.items():
                logger.info("[style-debug]   - '%s': %s_score=%.3f",
                            item_name, occasion, score_info.get("score", 0.0))

            # Color compatibility check
            color_compat = style_scoring.compute_color_compatibility(
                items, occasion, wardrobe_lookup
            )
            logger.info("[style-debug]   color_compatibility: valid=%s, reason=%s, score=%s",
                        color_compat.get("valid"), color_compat.get("reason"),
                        color_compat.get("score", "N/A"))

            fashionclip_score = outfit.get("fashionclip_score", {})
            if fashionclip_score:
                logger.info("[style-debug]   fashionclip: total=%.3f, coherence=%.3f, occasion_fit=%.3f",
                            fashionclip_score.get("total", 0),
                            fashionclip_score.get("coherence", 0),
                            fashionclip_score.get("occasion_fit", 0))

        logger.info("[style-debug] === End Style Report ===")

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
                "temperature": 0.7,
                "preamble": "You are a creative fashion AI stylist. Always respond with valid JSON only, no extra text. Prioritize variety and distinctiveness in your outfit suggestions."
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
        """Legacy method — delegates to new grouped format."""
        return self._prepare_wardrobe_for_recommendation(wardrobe)

    def _prepare_wardrobe_for_recommendation(self, wardrobe: List[Dict]) -> str:
        """Format wardrobe grouped by outfit role with shuffled order for diversity."""
        roles = {"top": [], "bottom": [], "layer": [], "shoes": [], "accessory": []}

        for item in wardrobe:
            role = item.get('_outfit_role', self._resolve_outfit_role(item))
            if role not in roles:
                role = 'accessory'
            roles[role].append(item)

        for role_items in roles.values():
            random.shuffle(role_items)

        lines = []
        role_labels = {
            "top": "TOPS (shirts, tees, sweaters, polos, blouses)",
            "bottom": "BOTTOMS (pants, jeans, shorts, skirts)",
            "layer": "LAYERS (jackets, coats, hoodies, blazers, cardigans)",
            "shoes": "SHOES (sneakers, boots, heels, sandals, loafers)",
            "accessory": "ACCESSORIES (bags, hats, jewelry, belts, scarves)",
        }

        for role, label in role_labels.items():
            items = roles[role]
            if not items:
                continue
            lines.append(f"\n{label}:")
            for item in items:
                entry = f"  - {item.get('name', 'Unknown')} ({item.get('color', 'unknown')} color, {item.get('vibe', 'casual')} style)"
                pattern = item.get('pattern') or (item.get('blip_attributes') or {}).get('pattern', '')
                if pattern and pattern != 'solid':
                    entry += f" [pattern: {pattern}]"
                lines.append(entry)

        return '\n'.join(lines)

    def _compute_color_context(self, wardrobe: List[Dict]) -> str:
        """Analyze wardrobe colors and identify available harmonies."""
        color_families = {
            "neutrals": ["black", "white", "gray", "grey", "beige", "cream", "tan", "brown", "navy"],
            "warm": ["red", "orange", "yellow", "coral", "burgundy", "rust", "terracotta", "gold", "maroon"],
            "cool": ["blue", "green", "purple", "teal", "lavender", "mint", "sage", "violet"],
            "earth": ["olive", "khaki", "camel", "chocolate", "forest", "moss"],
        }

        found_colors = {}
        for item in wardrobe:
            color = (item.get('color') or 'unknown').lower()
            if color == 'unknown':
                continue
            if color not in found_colors:
                found_colors[color] = []
            found_colors[color].append(item.get('name', 'Item'))

        family_summary = {}
        for family, members in color_families.items():
            matched = [c for c in found_colors if c in members]
            if matched:
                family_summary[family] = matched

        lines = []
        if family_summary.get("neutrals"):
            lines.append(f"Neutral base: {', '.join(family_summary['neutrals'])}")
        if family_summary.get("warm"):
            lines.append(f"Warm tones: {', '.join(family_summary['warm'])}")
        if family_summary.get("cool"):
            lines.append(f"Cool tones: {', '.join(family_summary['cool'])}")
        if family_summary.get("earth"):
            lines.append(f"Earth tones: {', '.join(family_summary['earth'])}")

        complementary_pairs = [
            ("navy", "rust"), ("black", "cream"), ("olive", "burgundy"),
            ("blue", "orange"), ("green", "red"), ("purple", "yellow"),
            ("gray", "yellow"), ("brown", "blue"), ("white", "black"),
        ]
        available_pairs = []
        for c1, c2 in complementary_pairs:
            if c1 in found_colors and c2 in found_colors:
                available_pairs.append(f"{c1} + {c2}")

        if available_pairs:
            lines.append(f"Complementary pairings available: {', '.join(available_pairs[:4])}")

        return '\n'.join(lines) if lines else "Mixed color palette available."

    def _get_weather_rules(self, weather: Dict) -> str:
        """Convert weather data into actionable styling rules."""
        temp = weather.get('temperature', 20)
        condition = weather.get('condition', 'clear')

        if temp >= 30:
            temp_rule = "Hot weather — minimal layers, light colors preferred, breathable fabrics only. Avoid jackets, sweaters, or heavy materials."
        elif temp >= 20:
            temp_rule = "Warm weather — light single layers work well. Short sleeves fine. Optional light jacket for evening."
        elif temp >= 10:
            temp_rule = "Mild/cool weather — layering recommended. Include a jacket or sweater. Long sleeves preferred."
        else:
            temp_rule = "Cold weather — heavy layers required. Prioritize warmth: coats, sweaters, boots. Avoid exposed skin."

        condition_rule = ""
        if 'rain' in condition.lower():
            condition_rule = " Rain expected — suggest water-resistant outerwear or darker colors that hide water marks."
        elif 'snow' in condition.lower():
            condition_rule = " Snow — boots recommended, avoid suede or delicate materials."
        elif 'wind' in condition.lower():
            condition_rule = " Windy — fitted layers over loose ones to avoid billowing."

        return f"Temperature: {temp}°C, Condition: {condition}\n{temp_rule}{condition_rule}"

    def _build_exclusion_context(self, recent_items: List[List[str]] = None) -> str:
        """Build exclusion instructions from recently generated outfits."""
        if not recent_items:
            return "- Surprise me with unexpected but coherent combinations"

        recent_str = "; ".join([", ".join(items[:3]) for items in recent_items[:5]])
        return f"- AVOID repeating these recent combinations: [{recent_str}]\n- Use different key pieces than previously suggested"

    def _validate_outfits(self, outfits: List[Dict], wardrobe: List[Dict]) -> List[Dict]:
        """Validate outfit items exist in wardrobe and enforce role limits."""
        wardrobe_names = {item.get('name', '').lower(): item.get('name', '') for item in wardrobe}
        wardrobe_roles = {}
        for item in wardrobe:
            name = item.get('name', '')
            role = item.get('_outfit_role', self._resolve_outfit_role(item))
            wardrobe_roles[name.lower()] = role

        validated = []
        for outfit in outfits:
            if not isinstance(outfit, dict):
                continue
            items = outfit.get('items', [])
            if not isinstance(items, list):
                continue

            valid_items = []
            for item_name in items:
                if not isinstance(item_name, str):
                    continue
                if item_name.lower() in wardrobe_names:
                    valid_items.append(wardrobe_names[item_name.lower()])
                else:
                    for wn_lower, wn_original in wardrobe_names.items():
                        if item_name.lower() in wn_lower or wn_lower in item_name.lower():
                            valid_items.append(wn_original)
                            break

            if len(valid_items) < 2:
                continue

            # Enforce role limits: max 1 top, 1 bottom, 1 shoes
            role_counts = Counter()
            for item_name in valid_items:
                role = wardrobe_roles.get(item_name.lower(), 'accessory')
                role_counts[role] += 1

            if role_counts.get('top', 0) > 1 or role_counts.get('bottom', 0) > 1 or role_counts.get('shoes', 0) > 1:
                valid_items = self._repair_outfit_roles(valid_items, wardrobe_roles)
                if not valid_items:
                    continue

            outfit = dict(outfit)
            outfit['items'] = valid_items
            validated.append(outfit)

        return validated if validated else outfits[:3]

    def _ensure_diversity(self, outfits: List[Dict], wardrobe: List[Dict]) -> List[Dict]:
        """Ensure the 3 outfits don't over-share items."""
        if len(outfits) <= 1:
            return outfits

        item_usage = {}
        for outfit in outfits:
            for item in outfit.get('items', []):
                item_usage[item] = item_usage.get(item, 0) + 1

        overused = [item for item, count in item_usage.items() if count >= len(outfits)]
        if not overused:
            return outfits

        wardrobe_by_cat = {}
        for item in wardrobe:
            cat = item.get('category', 'accessories')
            if cat not in wardrobe_by_cat:
                wardrobe_by_cat[cat] = []
            wardrobe_by_cat[cat].append(item)

        wardrobe_lookup = {item.get('name', '').lower(): item for item in wardrobe}

        for overused_name in overused:
            item_data = wardrobe_lookup.get(overused_name.lower())
            if not item_data:
                continue
            cat = item_data.get('category', 'accessories')
            alternatives = [i.get('name', '') for i in wardrobe_by_cat.get(cat, [])
                           if i.get('name', '') != overused_name]
            if not alternatives:
                continue

            replaced = False
            for outfit in outfits[1:]:
                if replaced:
                    break
                items = outfit.get('items', [])
                if overused_name in items:
                    replacement = random.choice(alternatives)
                    items[items.index(overused_name)] = replacement
                    replaced = True

        return outfits

    def _extract_from_filename(self, filename: str) -> Dict[str, str]:
        """Extract color and category hints from the filename."""
        filename_lower = filename.lower().replace('_', ' ').replace('-', ' ')
        # Remove file extension
        filename_lower = re.sub(r'\.\w+$', '', filename_lower)

        hints = {}

        # Detect color from filename
        color_keywords = {
            'black': ['black'],
            'white': ['white', 'cream', 'ivory'],
            'red': ['red', 'maroon', 'burgundy', 'crimson'],
            'blue': ['blue', 'navy', 'denim', 'indigo'],
            'green': ['green', 'olive', 'khaki'],
            'yellow': ['yellow', 'mustard', 'gold'],
            'purple': ['purple', 'violet', 'lavender'],
            'pink': ['pink', 'rose', 'magenta'],
            'brown': ['brown', 'tan', 'beige', 'camel'],
            'gray': ['gray', 'grey', 'charcoal'],
            'orange': ['orange', 'coral', 'peach'],
        }
        for color, keywords in color_keywords.items():
            if any(kw in filename_lower for kw in keywords):
                hints["color"] = color
                break

        # Detect category from filename
        if any(w in filename_lower for w in ['shirt', 'tee', 't shirt', 'top', 'blouse', 'hoodie', 'sweater', 'jacket', 'coat', 'polo', 'vest']):
            hints["category"] = "tops"
        elif any(w in filename_lower for w in ['pant', 'jean', 'trouser', 'chino', 'short', 'skirt', 'legging', 'jogger']):
            hints["category"] = "bottoms"
        elif any(w in filename_lower for w in ['dress', 'gown', 'romper', 'jumpsuit']):
            hints["category"] = "dresses"
        elif any(w in filename_lower for w in ['shoe', 'boot', 'sneaker', 'sandal', 'heel', 'loafer']):
            hints["category"] = "shoes"
        elif any(w in filename_lower for w in ['hat', 'cap', 'belt', 'bag', 'watch', 'scarf', 'tie', 'bracelet']):
            hints["category"] = "accessories"

        return hints

    def _build_item_name(self, color: str, category: str, filename: str = "") -> str:
        """Build a readable item name from color, category, and filename."""
        # Map category to a generic item type name
        category_type_map = {
            "tops": "Top",
            "bottoms": "Pants",
            "dresses": "Dress",
            "shoes": "Shoes",
            "accessories": "Accessory",
        }

        # Try to get a more specific type from filename
        specific_type = ""
        if filename:
            fn_lower = filename.lower().replace('_', ' ').replace('-', ' ')
            type_keywords = [
                ("T-Shirt", ["tshirt", "t shirt", "tee"]),
                ("Shirt", ["shirt"]),
                ("Hoodie", ["hoodie"]),
                ("Sweater", ["sweater"]),
                ("Jacket", ["jacket"]),
                ("Coat", ["coat"]),
                ("Jeans", ["jean"]),
                ("Chinos", ["chino"]),
                ("Trousers", ["trouser"]),
                ("Pants", ["pant"]),
                ("Shorts", ["short"]),
                ("Skirt", ["skirt"]),
                ("Dress", ["dress"]),
                ("Sneakers", ["sneaker"]),
                ("Boots", ["boot"]),
            ]
            for type_name, keywords in type_keywords:
                if any(kw in fn_lower for kw in keywords):
                    specific_type = type_name
                    break

        item_type = specific_type or category_type_map.get(category, "Item")
        color_part = color.title() if color and color != "unknown" else ""

        if color_part:
            return f"{color_part} {item_type}"
        return item_type

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

    def _fallback_outfit_recommendation(self, wardrobe: List[Dict], weather: Dict, occasion: str, preferences: Dict[str, Any] = None) -> Dict[str, Any]:
        """Fallback rule-based outfit recommendation — style-aware, deduplicated, role-based, personalized."""
        temperature = weather.get('temperature', 20)
        preferences = preferences or {}

        # Freshness-based prioritization
        overused = set(name.lower() for name in preferences.get('overused_items', []))

        def prioritize_fresh(items):
            fresh = [i for i in items if i.get('name', '').lower() not in overused]
            stale = [i for i in items if i.get('name', '').lower() in overused]
            random.shuffle(fresh)
            random.shuffle(stale)
            return fresh + stale

        color_family_map = {
            "black": "black", "charcoal": "black", "dark": "black",
            "white": "white", "cream": "white", "ivory": "white",
            "gray": "gray", "grey": "gray", "silver": "gray",
            "blue": "blue", "navy": "blue", "denim": "blue", "teal": "blue", "indigo": "blue",
            "green": "green", "olive": "green", "khaki": "green", "forest": "green", "sage": "green", "moss": "green",
            "brown": "brown", "tan": "brown", "beige": "brown", "camel": "brown", "chocolate": "brown",
            "red": "red", "burgundy": "red", "maroon": "red", "crimson": "red",
            "pink": "pink", "rose": "pink", "magenta": "pink",
            "purple": "purple", "violet": "purple", "lavender": "purple",
            "orange": "orange", "coral": "orange", "rust": "orange",
            "yellow": "yellow", "gold": "yellow", "mustard": "yellow",
        }

        def get_color_family(item):
            color = (item.get('color') or '').lower()
            return color_family_map.get(color, color)

        # Group items by outfit role
        by_role = {"top": [], "bottom": [], "layer": [], "shoes": [], "accessory": []}
        for item in wardrobe:
            role = item.get('_outfit_role', self._resolve_outfit_role(item))
            if role not in by_role:
                role = 'accessory'
            by_role[role].append(item)

        # Weather filtering
        def is_weather_ok(item):
            name = (item.get('name') or '').lower()
            if temperature >= 28:
                if any(w in name for w in ['coat', 'parka', 'puffer', 'wool', 'sweater']):
                    return False
            if temperature < 10:
                if any(w in name for w in ['tank', 'shorts', 'sandal', 'crop']):
                    return False
            return True

        for role in by_role:
            by_role[role] = [i for i in by_role[role] if is_weather_ok(i)] or by_role[role]

        # Style-aware filtering (uses _style_scores attached by upstream filter)
        def filter_by_occasion(items, occasion):
            if not items:
                return items
            scored = []
            for item in items:
                style_scores = item.get("_style_scores")
                if style_scores:
                    score = style_scores.get(occasion, 0.3)
                else:
                    vibe_scores = {
                        "casual": {"casual": 3, "sporty": 2, "trendy": 2, "vintage": 1, "formal": 0},
                        "formal": {"formal": 3, "trendy": 1, "vintage": 1, "casual": 0, "sporty": 0},
                        "streetwear": {"trendy": 3, "sporty": 2, "casual": 1, "vintage": 2, "formal": 0},
                        "monochrome": {"casual": 1, "formal": 1, "sporty": 1, "trendy": 1, "vintage": 1},
                    }
                    scores = vibe_scores.get(occasion, vibe_scores["casual"])
                    score = scores.get(item.get('vibe', 'casual'), 1)
                scored.append((item, score))
            scored.sort(key=lambda x: -x[1])
            filtered = [item for item, score in scored if score > 0]
            return filtered if filtered else items

        # Monochrome: group by color family
        def get_monochrome_items():
            all_items = []
            for role_items in by_role.values():
                all_items.extend(role_items)

            color_groups = {}
            for item in all_items:
                family = get_color_family(item)
                if family not in color_groups:
                    color_groups[family] = []
                color_groups[family].append(item)

            best_family = None
            best_score = 0
            for family, items in color_groups.items():
                roles_covered = set(i.get('_outfit_role', self._resolve_outfit_role(i)) for i in items)
                score = len(roles_covered) * 10 + len(items)
                if score > best_score:
                    best_score = score
                    best_family = family

            neutral_families = ["black", "white", "gray"]
            results = []
            if best_family:
                results.append((best_family, color_groups[best_family]))
            for nf in neutral_families:
                if nf != best_family and nf in color_groups:
                    results.append((nf, color_groups[nf]))
            return results[:3]

        outfits = []
        seen_combos = set()

        if occasion == "monochrome":
            mono_groups = get_monochrome_items()
            for family_name, family_items in mono_groups:
                family_by_role = {"top": [], "bottom": [], "layer": [], "shoes": [], "accessory": []}
                for item in family_items:
                    role = item.get('_outfit_role', self._resolve_outfit_role(item))
                    if role in family_by_role:
                        family_by_role[role].append(item)

                outfit_items = []
                if family_by_role["top"]:
                    outfit_items.append(family_by_role["top"][0].get('name'))
                elif family_by_role["layer"]:
                    outfit_items.append(family_by_role["layer"][0].get('name'))

                if family_by_role["bottom"]:
                    outfit_items.append(family_by_role["bottom"][0].get('name'))

                if family_by_role["shoes"]:
                    outfit_items.append(family_by_role["shoes"][0].get('name'))
                elif by_role["shoes"]:
                    neutral_shoes = [s for s in by_role["shoes"] if get_color_family(s) in ["black", "white", "gray"]]
                    if neutral_shoes:
                        outfit_items.append(neutral_shoes[0].get('name'))
                    else:
                        outfit_items.append(by_role["shoes"][0].get('name'))

                if family_by_role["accessory"]:
                    outfit_items.append(family_by_role["accessory"][0].get('name'))

                outfit_items = [i for i in outfit_items if i]
                combo_key = tuple(sorted(outfit_items))

                if len(outfit_items) >= 2 and combo_key not in seen_combos:
                    seen_combos.add(combo_key)
                    outfits.append({
                        'items': outfit_items,
                        'styling_tip': f"Keep everything in the {family_name} family for tonal depth.",
                        'color_story': f"A full {family_name} tonal palette — different textures create visual interest within one hue.",
                        'why_it_works': f"Monochrome {family_name} creates a sleek, editorial look that's effortlessly cohesive."
                    })

                if len(outfits) >= 3:
                    break
        else:
            # Non-monochrome: style-aware outfit building using roles
            filtered_tops = filter_by_occasion(by_role["top"] + by_role["layer"], occasion)
            filtered_bottoms = filter_by_occasion(by_role["bottom"], occasion)
            filtered_shoes = filter_by_occasion(by_role["shoes"], occasion)

            filtered_tops = prioritize_fresh(filtered_tops)
            filtered_bottoms = prioritize_fresh(filtered_bottoms)
            filtered_shoes = prioritize_fresh(filtered_shoes)

            num_tops = len(filtered_tops)
            num_bottoms = len(filtered_bottoms)
            num_shoes = len(filtered_shoes)

            max_combos = max(num_tops, 1) * max(num_bottoms, 1)
            for i in range(min(3, max_combos)):
                outfit_items = []

                if filtered_tops:
                    outfit_items.append(filtered_tops[i % num_tops].get('name'))
                if filtered_bottoms:
                    outfit_items.append(filtered_bottoms[i % num_bottoms].get('name'))
                if filtered_shoes:
                    outfit_items.append(filtered_shoes[i % num_shoes].get('name'))

                # Add a layer for streetwear/cold weather
                if by_role["layer"] and (occasion == "streetwear" or temperature < 15):
                    layer = by_role["layer"][i % len(by_role["layer"])]
                    layer_name = layer.get('name')
                    if layer_name not in outfit_items:
                        outfit_items.append(layer_name)

                # Add accessory for variety
                if by_role["accessory"]:
                    outfit_items.append(by_role["accessory"][i % len(by_role["accessory"])].get('name'))

                outfit_items = [item for item in outfit_items if item]
                combo_key = tuple(sorted(outfit_items))

                if len(outfit_items) >= 2 and combo_key not in seen_combos:
                    seen_combos.add(combo_key)

                    colors_used = [item.get('color', '') for item in wardrobe if item.get('name') in outfit_items]
                    color_desc = " and ".join(filter(None, set(colors_used))) or "complementary tones"

                    occasion_tips = {
                        "casual": [
                            "Keep it relaxed — roll sleeves and leave layers open.",
                            "Pair with minimal accessories for an effortless everyday look.",
                            "Let the fit do the talking — comfort meets style.",
                        ],
                        "formal": [
                            "Tuck in and keep lines clean for a polished silhouette.",
                            "Stick to structured pieces — tailoring elevates everything.",
                            "Less is more — one statement piece, everything else understated.",
                        ],
                        "streetwear": [
                            "Go oversized on top, fitted on bottom for contrast.",
                            "Layer boldly — the more dimension, the better.",
                            "Let one statement piece anchor the whole fit.",
                        ],
                    }
                    tips = occasion_tips.get(occasion, occasion_tips["casual"])

                    outfits.append({
                        'items': outfit_items,
                        'styling_tip': tips[len(outfits) % len(tips)],
                        'color_story': f"A {occasion} palette built on {color_desc}.",
                        'why_it_works': f"Curated for {occasion} style at {temperature}°C — each piece earns its place."
                    })

                if len(outfits) >= 3:
                    break

        # If wardrobe is too small for distinct outfits, don't pad with duplicates
        if not outfits:
            outfit_items = []
            if by_role["top"]:
                outfit_items.append(by_role["top"][0].get('name'))
            elif by_role["layer"]:
                outfit_items.append(by_role["layer"][0].get('name'))
            if by_role["bottom"]:
                outfit_items.append(by_role["bottom"][0].get('name'))
            if by_role["shoes"]:
                outfit_items.append(by_role["shoes"][0].get('name'))
            outfit_items = [i for i in outfit_items if i]
            if outfit_items:
                outfits.append({
                    'items': outfit_items,
                    'styling_tip': f'The best {occasion} look from your current wardrobe.',
                    'color_story': 'Work with what you have — these pieces complement each other.',
                    'why_it_works': f'Styled for {occasion} with your available pieces. Add more items for more variety!'
                })

        return {'outfits': outfits}


ai_service = RealAIService()
