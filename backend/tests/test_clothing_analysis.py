"""
Structured test suite for the DripScript clothing analysis pipeline.

Tests cover:
- BLIP caption extraction accuracy
- Metadata normalization (category, color, type, vibe)
- Filename fallback parsing
- Edge cases (folded, mannequin, blurry, transparent, multi-item, mirror, hanging)
- Confidence scoring
- Consistency across repeated calls with different inputs

Run with: python -m pytest backend/tests/test_clothing_analysis.py -v
"""

import os
import sys
import json
import tempfile
import logging
from unittest.mock import patch, MagicMock
from typing import Dict, Any

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.ai_service import (
    _extract_color,
    _extract_category,
    _extract_pattern,
    _extract_sleeve_length,
    _extract_subtype,
    _parse_blip_caption,
    _format_clean_item_name,
    _normalize_caption_text,
    compute_confidence,
    merge_analysis_results,
    classify_with_fashion_model,
    RealAIService,
    analyze_clothing,
    STANDARD_COLOR_KEYWORDS,
    CATEGORY_KEYWORDS,
    TARGET_CATEGORIES,
    FASHION_CLASSIFIER_CONFIDENCE_THRESHOLD,
    FASHION_LABEL_TO_CATEGORY,
    FASHION_LABEL_TO_SUBTYPE,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def ai_service():
    """Create an AI service instance without requiring API keys."""
    with patch.dict(os.environ, {"COHERE_API_KEY": ""}):
        return RealAIService()


@pytest.fixture
def ai_service_with_cohere():
    """Create an AI service instance with a mock Cohere key."""
    with patch.dict(os.environ, {"COHERE_API_KEY": "test-key"}):
        return RealAIService()


def _create_test_image(color=(0, 0, 0), size=(224, 224)):
    """Create a temporary test image file."""
    try:
        from PIL import Image
    except ImportError:
        pytest.skip("Pillow not installed")

    img = Image.new("RGB", size, color)
    tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    img.save(tmp.name)
    return tmp.name


# ============================================================
# CATEGORY EXTRACTION TESTS
# ============================================================

class TestCategoryExtraction:
    """Test that clothing categories are correctly extracted from captions."""

    @pytest.mark.parametrize("caption,expected", [
        ("a photo of a man wearing a white t-shirt", "tops"),
        ("a woman in a blue blouse", "tops"),
        ("black hoodie on a hanger", "tops"),
        ("gray sweater folded on table", "tops"),
        ("red jacket hanging on rack", "tops"),
        ("a polo shirt in navy", "tops"),
        ("cotton tank top", "tops"),
        ("a vest on a mannequin", "tops"),
    ])
    def test_tops_detection(self, caption, expected):
        result = _extract_category(caption)
        assert result == expected, f"Caption '{caption}' -> got '{result}', expected '{expected}'"

    @pytest.mark.parametrize("caption,expected", [
        ("a pair of black pants", "bottoms"),
        ("blue jeans on white background", "bottoms"),
        ("khaki trousers folded", "bottoms"),
        ("denim shorts on a mannequin", "bottoms"),
        ("a woman wearing a plaid skirt", "bottoms"),
        ("gray leggings", "bottoms"),
    ])
    def test_bottoms_detection(self, caption, expected):
        result = _extract_category(caption)
        assert result == expected, f"Caption '{caption}' -> got '{result}', expected '{expected}'"

    @pytest.mark.parametrize("caption,expected", [
        ("a red dress on a hanger", "dresses"),
        ("black evening gown", "dresses"),
        ("floral romper", "dresses"),
        ("a jumpsuit in olive green", "dresses"),
    ])
    def test_dresses_detection(self, caption, expected):
        result = _extract_category(caption)
        assert result == expected, f"Caption '{caption}' -> got '{result}', expected '{expected}'"

    @pytest.mark.parametrize("caption,expected", [
        ("white sneakers on floor", "shoes"),
        ("black leather boots", "shoes"),
        ("brown sandals", "shoes"),
        ("red heels on display", "shoes"),
        ("casual loafers", "shoes"),
    ])
    def test_shoes_detection(self, caption, expected):
        result = _extract_category(caption)
        assert result == expected, f"Caption '{caption}' -> got '{result}', expected '{expected}'"

    @pytest.mark.parametrize("caption,expected", [
        ("a black leather belt", "accessories"),
        ("sunglasses on a table", "accessories"),
        ("a wool scarf", "accessories"),
        ("baseball cap in red", "accessories"),
    ])
    def test_accessories_detection(self, caption, expected):
        result = _extract_category(caption)
        assert result == expected, f"Caption '{caption}' -> got '{result}', expected '{expected}'"

    def test_unknown_category(self):
        result = _extract_category("a photo of a person standing")
        assert result == "unknown"


# ============================================================
# COLOR EXTRACTION TESTS
# ============================================================

class TestColorExtraction:
    """Test that colors are correctly extracted from captions."""

    @pytest.mark.parametrize("caption,expected", [
        ("a black t-shirt", "black"),
        ("white cotton shirt", "white"),
        ("cream colored blouse", "white"),
        ("ivory dress", "white"),
        ("beige trousers", "brown"),
        ("navy blue jacket", "blue"),
        ("olive green pants", "green"),
        ("gray hoodie", "gray"),
        ("charcoal sweater", "gray"),
        ("red dress", "red"),
        ("burgundy coat", "red"),
        ("maroon jacket", "red"),
        ("pink blouse", "pink"),
        ("purple scarf", "purple"),
        ("lavender top", "purple"),
        ("orange shorts", "orange"),
        ("coral dress", "orange"),
        ("brown leather belt", "brown"),
        ("tan chinos", "brown"),
        ("khaki pants", "brown"),
        ("yellow raincoat", "yellow"),
        ("mustard sweater", "yellow"),
    ])
    def test_color_detection(self, caption, expected):
        result = _extract_color(caption)
        assert result == expected, f"Caption '{caption}' -> got '{result}', expected '{expected}'"

    def test_unknown_color(self):
        result = _extract_color("a photo of clothing on a hanger")
        assert result == "unknown"

    def test_multicolor_returns_first_match(self):
        result = _extract_color("black and white striped shirt")
        assert result in ["black", "white"]


# ============================================================
# PATTERN EXTRACTION TESTS
# ============================================================

class TestPatternExtraction:
    """Test pattern/print detection from captions."""

    @pytest.mark.parametrize("caption,expected", [
        ("a striped blue shirt", "striped"),
        ("plaid flannel shirt", "plaid"),
        ("floral summer dress", "floral"),
        ("polka dot blouse", "polka dot"),
        ("camouflage jacket", "camouflage"),
        ("geometric print top", "geometric"),
        ("plain black t-shirt", "solid"),
    ])
    def test_pattern_detection(self, caption, expected):
        result = _extract_pattern(caption)
        assert result == expected, f"Caption '{caption}' -> got '{result}', expected '{expected}'"

    def test_default_solid(self):
        result = _extract_pattern("a simple cotton shirt")
        assert result == "solid"


# ============================================================
# SLEEVE LENGTH EXTRACTION TESTS
# ============================================================

class TestSleeveLengthExtraction:
    """Test sleeve length detection from captions."""

    @pytest.mark.parametrize("caption,expected", [
        ("long sleeve black shirt", "long"),
        ("short sleeve polo", "short"),
        ("sleeveless tank top", "sleeveless"),
        ("3/4 sleeve blouse", "three-quarter"),
    ])
    def test_sleeve_detection(self, caption, expected):
        result = _extract_sleeve_length(caption)
        assert result == expected

    def test_unknown_sleeve(self):
        result = _extract_sleeve_length("a pair of jeans")
        assert result == "unknown"


# ============================================================
# SUBTYPE EXTRACTION TESTS
# ============================================================

class TestSubtypeExtraction:
    """Test clothing subtype detection."""

    @pytest.mark.parametrize("caption,expected", [
        ("a white t-shirt", "t-shirt"),
        ("blue button down shirt", "shirt"),
        ("dark denim jeans", "jeans"),
        ("black trousers", "trousers"),
        ("khaki pants", "pants"),
        ("summer shorts", "shorts"),
    ])
    def test_subtype_detection(self, caption, expected):
        result = _extract_subtype(caption)
        assert result == expected

    def test_unknown_subtype(self):
        result = _extract_subtype("a photo of a person")
        assert result == "unknown"


# ============================================================
# ITEM NAME FORMATTING TESTS
# ============================================================

class TestItemNameFormatting:
    """Test clean item name generation."""

    @pytest.mark.parametrize("color,subtype,expected", [
        ("black", "jeans", "Black Jeans"),
        ("white", "t-shirt", "White T-Shirt"),
        ("blue", "shirt", "Blue Shirt"),
        ("unknown", "pants", "Pants"),
        ("red", "unknown", "Red Item"),
        ("unknown", "unknown", "Stylish Item"),
    ])
    def test_name_formatting(self, color, subtype, expected):
        result = _format_clean_item_name(color, subtype)
        assert result == expected


# ============================================================
# BLIP CAPTION PARSING TESTS
# ============================================================

class TestBlipCaptionParsing:
    """Test full caption parsing pipeline."""

    @pytest.mark.parametrize("caption,expected_name,expected_category,expected_color", [
        ("a photo of a black t-shirt", "Black T-Shirt", "tops", "black"),
        ("blue denim jeans on white background", "Blue Jeans", "bottoms", "blue"),
        ("a pair of khaki pants", "Brown Pants", "bottoms", "brown"),
        ("white cotton shirt", "White Shirt", "tops", "white"),
        ("black trousers folded", "Black Trousers", "bottoms", "black"),
    ])
    def test_caption_parsing(self, caption, expected_name, expected_category, expected_color):
        result = _parse_blip_caption(caption)
        assert result["name"] == expected_name, f"Name: got '{result['name']}', expected '{expected_name}'"
        assert result["category"] == expected_category, f"Category: got '{result['category']}', expected '{expected_category}'"
        assert result["color"] == expected_color, f"Color: got '{result['color']}', expected '{expected_color}'"


# ============================================================
# FILENAME EXTRACTION TESTS
# ============================================================

class TestFilenameExtraction:
    """Test filename-based metadata extraction as fallback."""

    @pytest.fixture
    def service(self, ai_service):
        return ai_service

    @pytest.mark.parametrize("filename,expected_color,expected_category", [
        ("black-tshirt-cotton.jpg", "black", "tops"),
        ("navy-chinos-slim.webp", "blue", "bottoms"),
        ("white-sneakers-nike.png", "white", "shoes"),
        ("red-dress-summer.jpg", "red", "dresses"),
        ("olive-jacket-military.webp", "green", "tops"),
        ("beige-trousers-formal.jpg", "brown", "bottoms"),
        ("gray-hoodie-oversized.png", "gray", "tops"),
        ("pluschinostrtp-black-2.webp", "black", "bottoms"),
        ("MCT00025CLOUD_4_6bd5de0b.webp", None, None),
    ])
    def test_filename_extraction(self, service, filename, expected_color, expected_category):
        result = service._extract_from_filename(filename)
        logger.info("Filename: %s -> %s", filename, result)

        if expected_color:
            assert result.get("color") == expected_color, f"Color: got '{result.get('color')}', expected '{expected_color}'"
        if expected_category:
            assert result.get("category") == expected_category, f"Category: got '{result.get('category')}', expected '{expected_category}'"

    def test_filename_does_not_dominate(self, service):
        """Verify that filename is only used as fallback, not primary source."""
        # Simulate BLIP returning valid data - filename should not override
        mock_blip = {
            "caption": "a photo of blue denim jeans",
            "color": "blue",
            "category": "bottoms",
            "pattern": "solid",
            "sleeve_length": "unknown",
            "all_captions": ["a photo of blue denim jeans"],
        }

        with patch("services.ai_service.analyze_clothing", return_value=mock_blip):
            result = service.classify_clothing_image(
                "", image_path="/fake/path.jpg", filename="red-shirt-cotton.jpg"
            )

        # BLIP says blue jeans/bottoms - filename says red/tops
        # BLIP should win since it has valid data
        assert result["category"] == "bottoms", "BLIP category should take priority over filename"
        assert result["color"] == "blue", "BLIP color should take priority over filename"


# ============================================================
# BUILD ITEM NAME TESTS
# ============================================================

class TestBuildItemName:
    """Test the _build_item_name helper."""

    @pytest.fixture
    def service(self, ai_service):
        return ai_service

    @pytest.mark.parametrize("color,category,filename,expected", [
        ("black", "bottoms", "chinos-black.jpg", "Black Chinos"),
        ("white", "tops", "tshirt-white.jpg", "White T-Shirt"),
        ("blue", "bottoms", "jeans-slim.jpg", "Blue Jeans"),
        ("", "tops", "hoodie-oversized.jpg", "Hoodie"),
        ("gray", "tops", "random-image.jpg", "Gray Top"),
        ("black", "shoes", "sneaker-black.jpg", "Black Sneakers"),
    ])
    def test_build_item_name(self, service, color, category, filename, expected):
        result = service._build_item_name(color, category, filename)
        assert result == expected, f"Got '{result}', expected '{expected}'"


# ============================================================
# CLOTHING TYPE TEST CASES
# ============================================================

class TestClothingTypes:
    """Test classification for specific clothing types."""

    @pytest.fixture
    def service(self, ai_service):
        return ai_service

    @pytest.mark.parametrize("caption,expected_category", [
        # T-shirts
        ("a white t-shirt on white background", "tops"),
        ("black cotton tee", "tops"),
        # Hoodies
        ("gray oversized hoodie", "tops"),
        ("navy zip-up hoodie", "tops"),
        # Jackets
        ("black leather jacket", "tops"),
        ("olive bomber jacket", "tops"),
        # Jeans
        ("blue skinny jeans", "bottoms"),
        ("black ripped jeans", "bottoms"),
        # Chinos / Trousers
        ("beige chino pants", "bottoms"),
        ("navy trousers", "bottoms"),
        # Shorts
        ("khaki cargo shorts", "bottoms"),
        ("black athletic shorts", "bottoms"),
        # Dresses
        ("red cocktail dress", "dresses"),
        ("floral maxi dress", "dresses"),
        # Skirts
        ("black pleated skirt", "bottoms"),
        ("denim mini skirt", "bottoms"),
    ])
    def test_clothing_type_category(self, caption, expected_category):
        result = _extract_category(caption)
        assert result == expected_category, f"Caption '{caption}' -> got '{result}', expected '{expected_category}'"


# ============================================================
# EDGE CASE TESTS
# ============================================================

class TestEdgeCases:
    """Test edge cases that commonly cause misclassification."""

    def test_vague_caption_uses_filename(self, ai_service):
        """When BLIP returns a vague caption, filename should fill the gaps."""
        mock_blip = {
            "caption": "a photo of a person standing",
            "color": "unknown",
            "category": "unknown",
            "pattern": "solid",
            "sleeve_length": "unknown",
            "all_captions": ["a photo of a person standing"],
        }

        with patch("services.ai_service.analyze_clothing", return_value=mock_blip):
            result = ai_service.classify_clothing_image(
                "", image_path="/fake/path.jpg", filename="black-jeans-slim.webp"
            )

        assert result["color"] == "black"
        assert result["category"] == "bottoms"
        logger.info("Vague caption + filename -> %s", result)

    def test_no_blip_no_cohere_uses_filename(self, ai_service):
        """When both BLIP and Cohere fail, filename is the last resort."""
        mock_blip = {
            "caption": "",
            "color": "unknown",
            "category": "unknown",
            "pattern": "solid",
            "sleeve_length": "unknown",
            "error": "BLIP model not available",
        }

        with patch("services.ai_service.analyze_clothing", return_value=mock_blip):
            result = ai_service.classify_clothing_image(
                "", image_path="/fake/path.jpg", filename="navy-hoodie-winter.jpg"
            )

        assert result["color"] == "blue"
        assert result["category"] == "tops"
        assert "Hoodie" in result["name"]
        logger.info("No BLIP + no Cohere + filename -> %s", result)

    def test_white_clothing_not_defaulting_to_gray(self, ai_service):
        """White clothing should be classified as white, not gray."""
        mock_blip = {
            "caption": "a white shirt on white background",
            "color": "white",
            "category": "tops",
            "pattern": "solid",
            "sleeve_length": "unknown",
            "all_captions": ["a white shirt on white background"],
        }

        with patch("services.ai_service.analyze_clothing", return_value=mock_blip):
            result = ai_service.classify_clothing_image(
                "", image_path="/fake/path.jpg", filename="white-shirt.jpg"
            )

        assert result["color"] == "white", f"Expected 'white', got '{result['color']}'"

    def test_pants_not_classified_as_tops(self, ai_service):
        """Pants/jeans/trousers must never be classified as tops."""
        mock_blip = {
            "caption": "a pair of black pants",
            "color": "black",
            "category": "bottoms",
            "pattern": "solid",
            "sleeve_length": "unknown",
            "all_captions": ["a pair of black pants"],
        }

        with patch("services.ai_service.analyze_clothing", return_value=mock_blip):
            result = ai_service.classify_clothing_image(
                "", image_path="/fake/path.jpg", filename="pants-black.jpg"
            )

        assert result["category"] == "bottoms", f"Expected 'bottoms', got '{result['category']}'"

    def test_different_inputs_produce_different_outputs(self, ai_service):
        """Different images/filenames must produce different classification results."""
        mock_blip_shirt = {
            "caption": "a white cotton shirt",
            "color": "white",
            "category": "tops",
            "pattern": "solid",
            "sleeve_length": "long",
            "all_captions": ["a white cotton shirt"],
        }
        mock_blip_jeans = {
            "caption": "blue denim jeans",
            "color": "blue",
            "category": "bottoms",
            "pattern": "solid",
            "sleeve_length": "unknown",
            "all_captions": ["blue denim jeans"],
        }

        with patch("services.ai_service.analyze_clothing", return_value=mock_blip_shirt):
            result1 = ai_service.classify_clothing_image(
                "", image_path="/fake/shirt.jpg", filename="white-shirt.jpg"
            )

        with patch("services.ai_service.analyze_clothing", return_value=mock_blip_jeans):
            result2 = ai_service.classify_clothing_image(
                "", image_path="/fake/jeans.jpg", filename="blue-jeans.jpg"
            )

        assert result1 != result2, "Different inputs must produce different outputs"
        assert result1["category"] != result2["category"]
        assert result1["color"] != result2["color"]
        logger.info("Result 1: %s", result1)
        logger.info("Result 2: %s", result2)

    @pytest.mark.parametrize("scenario,caption,filename", [
        ("folded_clothes", "a folded piece of clothing", "black-tshirt.jpg"),
        ("mannequin", "a mannequin wearing clothes", "red-dress-display.jpg"),
        ("blurry", "a blurry image", "navy-jacket.webp"),
        ("transparent_png", "an image with transparent background", "white-sneakers.png"),
        ("multiple_items", "several pieces of clothing on a bed", "outfit-casual.jpg"),
        ("mirror_selfie", "a person taking a selfie in a mirror", "ootd-black-jeans.jpg"),
        ("hanging", "clothes hanging on a rack", "gray-hoodie-rack.jpg"),
        ("wardrobe_photo", "an open wardrobe with many clothes", "closet-photo.jpg"),
    ])
    def test_edge_case_scenarios(self, ai_service, scenario, caption, filename):
        """Edge cases should still produce reasonable output using filename fallback."""
        mock_blip = {
            "caption": caption,
            "color": "unknown",
            "category": "unknown",
            "pattern": "solid",
            "sleeve_length": "unknown",
            "all_captions": [caption],
        }

        with patch("services.ai_service.analyze_clothing", return_value=mock_blip):
            result = ai_service.classify_clothing_image(
                "", image_path="/fake/path.jpg", filename=filename
            )

        logger.info("[%s] caption='%s', filename='%s' -> %s", scenario, caption, filename, result)

        # Should never return the old generic defaults
        assert result["name"] != "Stylish Item", f"[{scenario}] Got generic 'Stylish Item'"
        assert result["category"] in TARGET_CATEGORIES, f"[{scenario}] Invalid category: {result['category']}"


# ============================================================
# CONFIDENCE SCORING TESTS
# ============================================================

class TestConfidenceScoring:
    """Test that confidence levels are correctly assessed."""

    def test_high_confidence_blip_match(self):
        """BLIP caption with clear clothing keywords = high confidence."""
        caption = "a black leather jacket on a hanger"
        color = _extract_color(caption)
        category = _extract_category(caption)
        subtype = _extract_subtype(caption)

        confidence = compute_confidence(color, category, subtype)
        assert confidence >= 0.7, f"Expected high confidence, got {confidence}"

    def test_low_confidence_vague_caption(self):
        """Vague caption with no clothing keywords = low confidence."""
        caption = "a photo of something on a table"
        color = _extract_color(caption)
        category = _extract_category(caption)
        subtype = _extract_subtype(caption)

        confidence = compute_confidence(color, category, subtype)
        assert confidence <= 0.4, f"Expected low confidence, got {confidence}"

    def test_medium_confidence_partial_match(self):
        """Caption with some but not all attributes = medium confidence."""
        caption = "a pair of pants"
        color = _extract_color(caption)
        category = _extract_category(caption)
        subtype = _extract_subtype(caption)

        confidence = compute_confidence(color, category, subtype)
        assert 0.3 <= confidence <= 0.7, f"Expected medium confidence, got {confidence}"


# ============================================================
# NORMALIZATION CONSISTENCY TESTS
# ============================================================

class TestNormalizationConsistency:
    """Test that normalization produces consistent outputs."""

    def test_category_always_in_target_set(self, ai_service):
        """Category must always be one of the TARGET_CATEGORIES."""
        filenames = [
            "black-shirt.jpg", "blue-jeans.webp", "red-dress.png",
            "white-sneakers.jpg", "gold-watch.jpg", "random-file.jpg",
        ]
        for fn in filenames:
            hints = ai_service._extract_from_filename(fn)
            if "category" in hints:
                assert hints["category"] in TARGET_CATEGORIES, f"'{fn}' -> invalid category '{hints['category']}'"

    def test_color_always_in_standard_set(self, ai_service):
        """Color must always be one of the STANDARD_COLOR_KEYWORDS keys or empty."""
        valid_colors = set(STANDARD_COLOR_KEYWORDS.keys()) | {"", "unknown"}
        filenames = [
            "black-shirt.jpg", "navy-pants.webp", "olive-jacket.png",
            "beige-chinos.jpg", "random.jpg",
        ]
        for fn in filenames:
            hints = ai_service._extract_from_filename(fn)
            color = hints.get("color", "")
            assert color in valid_colors, f"'{fn}' -> invalid color '{color}'"

    def test_caption_normalization_strips_noise(self):
        """Caption normalization should strip punctuation and extra spaces."""
        raw = "A Photo of a  Black T-Shirt!!!"
        normalized = _normalize_caption_text(raw)
        assert normalized == "a photo of a black t shirt"


class TestFullPipeline:
    """Integration tests for the complete classify_clothing_image flow."""

    @pytest.fixture
    def service(self, ai_service):
        return ai_service

    @pytest.mark.parametrize("blip_caption,filename,exp_category,exp_color", [
        ("a photo of a man in black pants", "chinos-black.webp", "bottoms", "black"),
        ("a white t-shirt on a hanger", "white-tee.jpg", "tops", "white"),
        ("blue denim jeans", "jeans-blue-slim.webp", "bottoms", "blue"),
        ("a red dress on a mannequin", "red-cocktail-dress.jpg", "dresses", "red"),
        ("gray hoodie", "hoodie-gray-oversized.png", "tops", "gray"),
        ("olive green jacket", "olive-bomber.webp", "tops", "green"),
    ])
    def test_full_pipeline(self, service, blip_caption, filename, exp_category, exp_color):
        mock_blip = {
            "caption": blip_caption,
            "color": _extract_color(blip_caption),
            "category": _extract_category(blip_caption),
            "pattern": _extract_pattern(blip_caption),
            "sleeve_length": _extract_sleeve_length(blip_caption),
            "all_captions": [blip_caption],
        }

        with patch("services.ai_service.analyze_clothing", return_value=mock_blip):
            result = service.classify_clothing_image(
                "", image_path="/fake/path.jpg", filename=filename
            )

        logger.info("[pipeline] caption='%s', filename='%s' -> %s", blip_caption, filename, result)

        assert result["category"] == exp_category, f"Category: got '{result['category']}', expected '{exp_category}'"
        assert result["color"] == exp_color, f"Color: got '{result['color']}', expected '{exp_color}'"
        assert result["name"] != "Stylish Item", "Should not return generic name"
        assert result["name"] != "Clothing Item", "Should not return generic name"


# ============================================================
# DEBUG LOGGING VERIFICATION
# ============================================================

class TestDebugLogging:
    """Verify that debug logging is emitted at key pipeline stages."""

    def test_logging_on_classify(self, ai_service, caplog):
        """Classification should emit structured log messages."""
        mock_blip = {
            "caption": "a black jacket",
            "color": "black",
            "category": "tops",
            "pattern": "solid",
            "sleeve_length": "unknown",
            "all_captions": ["a black jacket"],
        }

        with caplog.at_level(logging.INFO):
            with patch("services.ai_service.analyze_clothing", return_value=mock_blip):
                ai_service.classify_clothing_image(
                    "", image_path="/fake/path.jpg", filename="black-jacket.jpg"
                )

        log_text = caplog.text
        assert "[classify]" in log_text, "Should have [classify] prefix in logs"
        assert "filename" in log_text.lower() or "Filename" in log_text, "Should log filename"


# ============================================================
# MULTI-MODEL MERGE LOGIC TESTS
# ============================================================

class TestMergeAnalysisResults:
    """Test the merge_analysis_results function that combines classifier + BLIP + filename."""

    def test_strong_classifier_wins_category(self):
        """When classifier confidence is above threshold, it determines category."""
        classifier = {"label": "Trouser", "confidence": 0.92, "category": "bottoms", "subtype": "trousers", "source": "fashion-classifier"}
        blip = {"color": "black", "category": "tops", "subtype": "unknown", "pattern": "solid", "sleeve_length": "unknown", "caption": "a person wearing clothes", "all_captions": [], "confidence": 0.4}
        filename = {"color": "black", "category": "tops"}

        merged = merge_analysis_results(classifier, blip, filename)
        assert merged["category"] == "bottoms", "Strong classifier should override BLIP category"
        assert merged["category_source"].startswith("fashion-classifier")

    def test_strong_classifier_wins_subtype(self):
        """When classifier confidence is above threshold, it determines subtype."""
        classifier = {"label": "Sneaker", "confidence": 0.88, "category": "shoes", "subtype": "sneakers", "source": "fashion-classifier"}
        blip = {"color": "white", "category": "shoes", "subtype": "unknown", "pattern": "solid", "sleeve_length": "unknown", "caption": "white shoes", "all_captions": [], "confidence": 0.75}
        filename = {}

        merged = merge_analysis_results(classifier, blip, filename)
        assert merged["subtype"] == "sneakers"
        assert merged["subtype_source"].startswith("fashion-classifier")

    def test_weak_classifier_falls_back_to_blip(self):
        """When classifier confidence is below threshold, BLIP takes priority."""
        classifier = {"label": "T-shirt/top", "confidence": 0.35, "category": "tops", "subtype": "t-shirt", "source": "fashion-classifier"}
        blip = {"color": "blue", "category": "bottoms", "subtype": "jeans", "pattern": "solid", "sleeve_length": "unknown", "caption": "blue jeans", "all_captions": [], "confidence": 0.75}
        filename = {}

        merged = merge_analysis_results(classifier, blip, filename)
        assert merged["category"] == "bottoms", "Weak classifier should NOT override BLIP"
        assert merged["category_source"] == "blip"
        assert merged["subtype"] == "jeans"
        assert merged["subtype_source"] == "blip"

    def test_blip_color_always_primary(self):
        """Color always comes from BLIP (classifier doesn't provide color)."""
        classifier = {"label": "Shirt", "confidence": 0.90, "category": "tops", "subtype": "shirt", "source": "fashion-classifier"}
        blip = {"color": "red", "category": "tops", "subtype": "shirt", "pattern": "striped", "sleeve_length": "long", "caption": "red striped shirt", "all_captions": [], "confidence": 0.75}
        filename = {"color": "blue"}

        merged = merge_analysis_results(classifier, blip, filename)
        assert merged["color"] == "red"
        assert merged["color_source"] == "blip"

    def test_filename_fallback_for_color(self):
        """When BLIP can't detect color, filename provides it."""
        classifier = {"label": "Coat", "confidence": 0.80, "category": "tops", "subtype": "coat", "source": "fashion-classifier"}
        blip = {"color": "unknown", "category": "tops", "subtype": "unknown", "pattern": "solid", "sleeve_length": "long", "caption": "a coat", "all_captions": [], "confidence": 0.4}
        filename = {"color": "black", "category": "tops"}

        merged = merge_analysis_results(classifier, blip, filename)
        assert merged["color"] == "black"
        assert merged["color_source"] == "filename"

    def test_filename_fallback_for_category(self):
        """When both classifier and BLIP fail category, filename provides it."""
        classifier = {"label": None, "confidence": 0.0, "category": "unknown", "subtype": "unknown", "source": "none"}
        blip = {"color": "unknown", "category": "unknown", "subtype": "unknown", "pattern": "solid", "sleeve_length": "unknown", "caption": "", "all_captions": [], "confidence": 0.0}
        filename = {"color": "navy", "category": "bottoms"}

        merged = merge_analysis_results(classifier, blip, filename)
        assert merged["category"] == "bottoms"
        assert merged["category_source"] == "filename"

    def test_all_sources_empty(self):
        """When all sources fail, defaults are returned."""
        classifier = {"label": None, "confidence": 0.0, "category": "unknown", "subtype": "unknown", "source": "none"}
        blip = {"color": "unknown", "category": "unknown", "subtype": "unknown", "pattern": "solid", "sleeve_length": "unknown", "caption": "", "all_captions": [], "confidence": 0.0}
        filename = {}

        merged = merge_analysis_results(classifier, blip, filename)
        assert merged["category"] == "unknown"
        assert merged["color"] == "unknown"
        assert merged["subtype"] == "unknown"

    def test_confidence_threshold_boundary(self):
        """Classifier at exactly the threshold should be considered strong."""
        threshold = FASHION_CLASSIFIER_CONFIDENCE_THRESHOLD
        classifier = {"label": "Dress", "confidence": threshold, "category": "dresses", "subtype": "dress", "source": "fashion-classifier"}
        blip = {"color": "red", "category": "tops", "subtype": "unknown", "pattern": "floral", "sleeve_length": "short", "caption": "red floral top", "all_captions": [], "confidence": 0.6}
        filename = {}

        merged = merge_analysis_results(classifier, blip, filename)
        assert merged["category"] == "dresses", "At-threshold classifier should win"

    def test_just_below_threshold_uses_blip(self):
        """Classifier just below threshold should defer to BLIP."""
        threshold = FASHION_CLASSIFIER_CONFIDENCE_THRESHOLD
        classifier = {"label": "Dress", "confidence": threshold - 0.01, "category": "dresses", "subtype": "dress", "source": "fashion-classifier"}
        blip = {"color": "red", "category": "tops", "subtype": "shirt", "pattern": "solid", "sleeve_length": "short", "caption": "red shirt", "all_captions": [], "confidence": 0.6}
        filename = {}

        merged = merge_analysis_results(classifier, blip, filename)
        assert merged["category"] == "tops", "Below-threshold classifier should defer to BLIP"
        assert merged["subtype"] == "shirt"


# ============================================================
# CLASSIFIER + BLIP INTEGRATION IN CLASSIFY METHOD
# ============================================================

class TestMultiModelClassify:
    """Test the full classify_clothing_image with mocked classifier + BLIP."""

    @pytest.fixture
    def service(self, ai_service):
        return ai_service

    def test_strong_classifier_overrides_blip_category(self, service):
        """Strong classifier prediction should override BLIP for category."""
        mock_blip = {
            "caption": "a person wearing something",
            "color": "black",
            "category": "unknown",
            "pattern": "solid",
            "sleeve_length": "unknown",
            "all_captions": ["a person wearing something"],
        }
        mock_classifier = {
            "label": "Trouser",
            "confidence": 0.91,
            "category": "bottoms",
            "subtype": "trousers",
            "source": "fashion-classifier",
            "all_predictions": [{"label": "Trouser", "score": 0.91}],
        }

        with patch("services.ai_service.analyze_clothing", return_value=mock_blip):
            with patch("services.ai_service.classify_with_fashion_model", return_value=mock_classifier):
                result = service.classify_clothing_image("", image_path="/fake/path.jpg", filename="pants.jpg")

        assert result["category"] == "bottoms"

    def test_weak_classifier_does_not_override_blip(self, service):
        """Weak classifier should NOT override a clear BLIP signal."""
        mock_blip = {
            "caption": "blue denim jeans on white background",
            "color": "blue",
            "category": "bottoms",
            "pattern": "solid",
            "sleeve_length": "unknown",
            "all_captions": ["blue denim jeans on white background"],
        }
        mock_classifier = {
            "label": "T-shirt/top",
            "confidence": 0.30,
            "category": "tops",
            "subtype": "t-shirt",
            "source": "fashion-classifier",
            "all_predictions": [{"label": "T-shirt/top", "score": 0.30}],
        }

        with patch("services.ai_service.analyze_clothing", return_value=mock_blip):
            with patch("services.ai_service.classify_with_fashion_model", return_value=mock_classifier):
                result = service.classify_clothing_image("", image_path="/fake/path.jpg", filename="jeans.jpg")

        assert result["category"] == "bottoms", "Weak classifier must not override strong BLIP"
        assert result["color"] == "blue"

    def test_classifier_unavailable_falls_back_gracefully(self, service):
        """When classifier fails, pipeline still works with BLIP + filename."""
        mock_blip = {
            "caption": "a red dress on a hanger",
            "color": "red",
            "category": "dresses",
            "pattern": "solid",
            "sleeve_length": "sleeveless",
            "all_captions": ["a red dress on a hanger"],
        }
        mock_classifier = {
            "label": None,
            "confidence": 0.0,
            "category": "unknown",
            "subtype": "unknown",
            "source": "none",
        }

        with patch("services.ai_service.analyze_clothing", return_value=mock_blip):
            with patch("services.ai_service.classify_with_fashion_model", return_value=mock_classifier):
                result = service.classify_clothing_image("", image_path="/fake/path.jpg", filename="red-dress.jpg")

        assert result["category"] == "dresses"
        assert result["color"] == "red"

    def test_classifier_result_attached_to_output(self, service):
        """Classifier prediction metadata should be included in the result."""
        mock_blip = {
            "caption": "white sneakers",
            "color": "white",
            "category": "shoes",
            "pattern": "solid",
            "sleeve_length": "unknown",
            "all_captions": ["white sneakers"],
        }
        mock_classifier = {
            "label": "Sneaker",
            "confidence": 0.95,
            "category": "shoes",
            "subtype": "sneakers",
            "source": "fashion-classifier",
            "all_predictions": [{"label": "Sneaker", "score": 0.95}],
        }

        with patch("services.ai_service.analyze_clothing", return_value=mock_blip):
            with patch("services.ai_service.classify_with_fashion_model", return_value=mock_classifier):
                result = service.classify_clothing_image("", image_path="/fake/path.jpg", filename="sneakers.jpg")

        assert "classifier_prediction" in result
        assert result["classifier_prediction"]["label"] == "Sneaker"
        assert result["classifier_prediction"]["confidence"] == 0.95

    def test_analysis_sources_attached(self, service):
        """Result should include source attribution for each field."""
        mock_blip = {
            "caption": "black hoodie",
            "color": "black",
            "category": "tops",
            "pattern": "solid",
            "sleeve_length": "long",
            "all_captions": ["black hoodie"],
        }
        mock_classifier = {
            "label": "Pullover",
            "confidence": 0.85,
            "category": "tops",
            "subtype": "sweater",
            "source": "fashion-classifier",
            "all_predictions": [{"label": "Pullover", "score": 0.85}],
        }

        with patch("services.ai_service.analyze_clothing", return_value=mock_blip):
            with patch("services.ai_service.classify_with_fashion_model", return_value=mock_classifier):
                result = service.classify_clothing_image("", image_path="/fake/path.jpg", filename="hoodie.jpg")

        assert "analysis_sources" in result
        assert "category_source" in result["analysis_sources"]
        assert "color_source" in result["analysis_sources"]


# ============================================================
# WHITE BACKGROUND / PRODUCT IMAGE TESTS
# ============================================================

class TestWhiteBackgroundImages:
    """Test that white-background ecommerce images don't corrupt color detection."""

    def test_white_bg_does_not_override_clothing_color(self):
        """White background mention should be filtered from color extraction."""
        caption = "a black t-shirt isolated on white background"
        color = _extract_color(caption)
        assert color == "black", f"Expected 'black', got '{color}' — white bg leaked"

    def test_white_backdrop_filtered(self):
        """'white backdrop' should not count as clothing color."""
        caption = "red dress on white backdrop"
        color = _extract_color(caption)
        assert color == "red", f"Expected 'red', got '{color}'"

    def test_isolated_on_white_filtered(self):
        """'isolated on white' should not count as clothing color."""
        caption = "blue jeans isolated on white"
        color = _extract_color(caption)
        assert color == "blue", f"Expected 'blue', got '{color}'"

    def test_actual_white_clothing_detected(self):
        """Actual white clothing should still be detected as white."""
        caption = "a white cotton shirt"
        color = _extract_color(caption)
        assert color == "white"

    def test_white_sneakers_on_white_bg(self):
        """White sneakers on white background — clothing color should be white."""
        caption = "white sneakers on white background"
        color = _extract_color(caption)
        assert color == "white"

    def test_product_image_full_pipeline(self, ai_service):
        """Full pipeline with a typical product image caption."""
        mock_blip = {
            "caption": "a navy blue polo shirt isolated on white background",
            "color": "blue",
            "category": "tops",
            "pattern": "solid",
            "sleeve_length": "short",
            "all_captions": ["a navy blue polo shirt isolated on white background"],
        }
        mock_classifier = {
            "label": "Shirt",
            "confidence": 0.78,
            "category": "tops",
            "subtype": "shirt",
            "source": "fashion-classifier",
            "all_predictions": [{"label": "Shirt", "score": 0.78}],
        }

        with patch("services.ai_service.analyze_clothing", return_value=mock_blip):
            with patch("services.ai_service.classify_with_fashion_model", return_value=mock_classifier):
                result = ai_service.classify_clothing_image("", image_path="/fake/path.jpg", filename="polo-navy.jpg")

        assert result["color"] == "blue"
        assert result["category"] == "tops"


# ============================================================
# MIRROR SELFIE / REAL WARDROBE PHOTO TESTS
# ============================================================

class TestRealWorldPhotos:
    """Test with captions typical of mirror selfies and real wardrobe photos."""

    def test_mirror_selfie_with_classifier(self, ai_service):
        """Mirror selfie where BLIP is vague but classifier is confident."""
        mock_blip = {
            "caption": "a man standing in front of a mirror",
            "color": "unknown",
            "category": "unknown",
            "pattern": "solid",
            "sleeve_length": "unknown",
            "all_captions": ["a man standing in front of a mirror"],
        }
        mock_classifier = {
            "label": "T-shirt/top",
            "confidence": 0.82,
            "category": "tops",
            "subtype": "t-shirt",
            "source": "fashion-classifier",
            "all_predictions": [{"label": "T-shirt/top", "score": 0.82}],
        }

        with patch("services.ai_service.analyze_clothing", return_value=mock_blip):
            with patch("services.ai_service.classify_with_fashion_model", return_value=mock_classifier):
                result = ai_service.classify_clothing_image("", image_path="/fake/path.jpg", filename="ootd-black-tee.jpg")

        assert result["category"] == "tops"
        assert result["color"] == "black"  # from filename fallback

    def test_wardrobe_rack_photo(self, ai_service):
        """Photo of clothes on a rack — BLIP vague, classifier + filename help."""
        mock_blip = {
            "caption": "clothes hanging on a rack",
            "color": "unknown",
            "category": "unknown",
            "pattern": "solid",
            "sleeve_length": "unknown",
            "all_captions": ["clothes hanging on a rack"],
        }
        mock_classifier = {
            "label": "Coat",
            "confidence": 0.60,
            "category": "tops",
            "subtype": "coat",
            "source": "fashion-classifier",
            "all_predictions": [{"label": "Coat", "score": 0.60}],
        }

        with patch("services.ai_service.analyze_clothing", return_value=mock_blip):
            with patch("services.ai_service.classify_with_fashion_model", return_value=mock_classifier):
                result = ai_service.classify_clothing_image("", image_path="/fake/path.jpg", filename="gray-coat-winter.jpg")

        assert result["category"] == "tops"
        assert result["color"] == "gray"

    def test_flat_lay_photo(self, ai_service):
        """Flat lay photo where both models agree."""
        mock_blip = {
            "caption": "a pair of black shorts on a bed",
            "color": "black",
            "category": "bottoms",
            "pattern": "solid",
            "sleeve_length": "unknown",
            "all_captions": ["a pair of black shorts on a bed"],
        }
        mock_classifier = {
            "label": "Trouser",
            "confidence": 0.65,
            "category": "bottoms",
            "subtype": "trousers",
            "source": "fashion-classifier",
            "all_predictions": [{"label": "Trouser", "score": 0.65}],
        }

        with patch("services.ai_service.analyze_clothing", return_value=mock_blip):
            with patch("services.ai_service.classify_with_fashion_model", return_value=mock_classifier):
                result = ai_service.classify_clothing_image("", image_path="/fake/path.jpg", filename="black-shorts.jpg")

        assert result["category"] == "bottoms"
        assert result["color"] == "black"


# ============================================================
# FASHION CLASSIFIER LABEL MAPPING TESTS
# ============================================================

class TestFashionClassifierMappings:
    """Test that all fashion classifier labels map correctly."""

    @pytest.mark.parametrize("label,expected_category", [
        ("T-shirt/top", "tops"),
        ("Trouser", "bottoms"),
        ("Pullover", "tops"),
        ("Dress", "dresses"),
        ("Coat", "tops"),
        ("Sandal", "shoes"),
        ("Shirt", "tops"),
        ("Sneaker", "shoes"),
        ("Bag", "accessories"),
        ("Ankle boot", "shoes"),
    ])
    def test_label_to_category_mapping(self, label, expected_category):
        assert FASHION_LABEL_TO_CATEGORY[label] == expected_category

    @pytest.mark.parametrize("label,expected_subtype", [
        ("T-shirt/top", "t-shirt"),
        ("Trouser", "trousers"),
        ("Pullover", "sweater"),
        ("Dress", "dress"),
        ("Coat", "coat"),
        ("Sandal", "sandals"),
        ("Shirt", "shirt"),
        ("Sneaker", "sneakers"),
        ("Bag", "bag"),
        ("Ankle boot", "boots"),
    ])
    def test_label_to_subtype_mapping(self, label, expected_subtype):
        assert FASHION_LABEL_TO_SUBTYPE[label] == expected_subtype


# ============================================================
# LOGGING VERIFICATION FOR MULTI-MODEL PIPELINE
# ============================================================

class TestMultiModelLogging:
    """Verify structured logging across the multi-model pipeline."""

    def test_classifier_logged(self, ai_service, caplog):
        """Classifier predictions should be logged."""
        mock_blip = {
            "caption": "a black shirt",
            "color": "black",
            "category": "tops",
            "pattern": "solid",
            "sleeve_length": "long",
            "all_captions": ["a black shirt"],
        }
        mock_classifier = {
            "label": "Shirt",
            "confidence": 0.88,
            "category": "tops",
            "subtype": "shirt",
            "source": "fashion-classifier",
            "all_predictions": [{"label": "Shirt", "score": 0.88}],
        }

        with caplog.at_level(logging.INFO):
            with patch("services.ai_service.analyze_clothing", return_value=mock_blip):
                with patch("services.ai_service.classify_with_fashion_model", return_value=mock_classifier):
                    ai_service.classify_clothing_image("", image_path="/fake/path.jpg", filename="shirt.jpg")

        log_text = caplog.text
        assert "[classify]" in log_text
        assert "multi-model" in log_text.lower() or "Merged" in log_text or "merged" in log_text

    def test_merge_sources_logged(self, ai_service, caplog):
        """Merge source attribution should appear in logs."""
        mock_blip = {
            "caption": "red dress",
            "color": "red",
            "category": "dresses",
            "pattern": "solid",
            "sleeve_length": "sleeveless",
            "all_captions": ["red dress"],
        }
        mock_classifier = {
            "label": "Dress",
            "confidence": 0.92,
            "category": "dresses",
            "subtype": "dress",
            "source": "fashion-classifier",
            "all_predictions": [{"label": "Dress", "score": 0.92}],
        }

        with caplog.at_level(logging.INFO):
            with patch("services.ai_service.analyze_clothing", return_value=mock_blip):
                with patch("services.ai_service.classify_with_fashion_model", return_value=mock_classifier):
                    ai_service.classify_clothing_image("", image_path="/fake/path.jpg", filename="dress.jpg")

        log_text = caplog.text
        assert "category" in log_text.lower()
        assert "src=" in log_text or "source" in log_text.lower()


class TestWardrobeDeduplication:
    """Test duplicate detection and sanitization in the backend."""

    def test_sanitize_wardrobe_deduplicates_exact_url(self, ai_service):
        wardrobe = [
            {"name": "Black Jeans", "category": "bottoms", "image": "http://localhost:8000/uploads/user1/123_jeans.jpg"},
            {"name": "Duplicate Black Jeans", "category": "bottoms", "image": "http://localhost:8000/uploads/user1/123_jeans.jpg"}
        ]
        sanitized = ai_service._sanitize_wardrobe(wardrobe)
        assert len(sanitized) == 1
        assert sanitized[0]["name"] == "Black Jeans"

    def test_sanitize_wardrobe_deduplicates_filename(self, ai_service):
        wardrobe = [
            {"name": "Black Jeans", "category": "bottoms", "image": "http://localhost:8000/uploads/user1/123_jeans.jpg"},
            {"name": "Another Black Jeans", "category": "bottoms", "image": "http://localhost:8000/uploads/user1/456_jeans.jpg"}
        ]
        sanitized = ai_service._sanitize_wardrobe(wardrobe)
        assert len(sanitized) == 1
        assert sanitized[0]["name"] == "Black Jeans"

    def test_sanitize_wardrobe_deduplicates_visual_similarity(self, ai_service):
        # Hamming distance <= 8 should be deduplicated
        wardrobe = [
            {"name": "Black Jeans", "category": "bottoms", "image": "http://localhost:8000/uploads/user1/123_jeans.jpg", "imageHash": "1111111100000000"},
            {"name": "Similar Jeans", "category": "bottoms", "image": "http://localhost:8000/uploads/user1/456_other.jpg", "imageHash": "1111111100000001"} # diff = 1
        ]
        sanitized = ai_service._sanitize_wardrobe(wardrobe)
        assert len(sanitized) == 1

    def test_sanitize_wardrobe_keeps_different_items(self, ai_service):
        wardrobe = [
            {"name": "Black Jeans", "category": "bottoms", "image": "http://localhost:8000/uploads/user1/123_jeans.jpg", "imageHash": "1111111100000000"},
            {"name": "White Shirt", "category": "tops", "image": "http://localhost:8000/uploads/user1/456_shirt.jpg", "imageHash": "0000000011111111"} # diff = 16
        ]
        sanitized = ai_service._sanitize_wardrobe(wardrobe)
        assert len(sanitized) == 2


