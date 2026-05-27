"""
Tests for the Style Scoring Service.
Validates per-item scoring, strict filtering, and outfit-level validation.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.style_scoring import (
    compute_item_style_scores,
    filter_wardrobe_by_style,
    score_outfit_style_coherence,
    validate_outfits_style,
    compute_color_compatibility,
    _is_hard_blocked_for_formal,
    STYLE_THRESHOLDS,
)


# --- Test Items ---

BLAZER = {"name": "Black Blazer", "category": "tops", "color": "black", "vibe": "formal", "tags": ["blazer", "structured"], "_outfit_role": "layer"}
DRESS_SHIRT = {"name": "White Dress Shirt", "category": "tops", "color": "white", "vibe": "formal", "tags": ["shirt", "button-down"], "_outfit_role": "top"}
TROUSERS = {"name": "Gray Trousers", "category": "bottoms", "color": "gray", "vibe": "formal", "tags": ["trousers", "tailored"], "_outfit_role": "bottom"}
LOAFERS = {"name": "Brown Loafers", "category": "shoes", "color": "brown", "vibe": "formal", "tags": ["loafers", "leather"], "_outfit_role": "shoes"}
OXFORD_SHOES = {"name": "Black Oxford Shoes", "category": "shoes", "color": "black", "vibe": "formal", "tags": ["oxford", "dress shoes"], "_outfit_role": "shoes"}

GRAPHIC_TEE = {"name": "Graphic Tee", "category": "tops", "color": "black", "vibe": "casual", "tags": ["graphic", "cotton"], "_outfit_role": "top"}
RIPPED_JEANS = {"name": "Ripped Blue Jeans", "category": "bottoms", "color": "blue", "vibe": "casual", "tags": ["ripped", "denim"], "_outfit_role": "bottom"}
SNEAKERS = {"name": "White Sneakers", "category": "shoes", "color": "white", "vibe": "casual", "tags": ["sneakers", "comfortable"], "_outfit_role": "shoes"}
SHORTS = {"name": "Khaki Shorts", "category": "bottoms", "color": "brown", "vibe": "casual", "tags": ["shorts", "summer"], "_outfit_role": "bottom"}

HOODIE = {"name": "Oversized Black Hoodie", "category": "tops", "color": "black", "vibe": "trendy", "tags": ["hoodie", "oversized", "streetwear"], "_outfit_role": "top"}
CARGO_PANTS = {"name": "Black Cargo Pants", "category": "bottoms", "color": "black", "vibe": "trendy", "tags": ["cargo", "urban"], "_outfit_role": "bottom"}
BOMBER_JACKET = {"name": "Green Bomber Jacket", "category": "tops", "color": "green", "vibe": "trendy", "tags": ["bomber", "layered"], "_outfit_role": "layer"}
HIGH_TOPS = {"name": "Black High-Tops", "category": "shoes", "color": "black", "vibe": "trendy", "tags": ["high-tops", "sneakers"], "_outfit_role": "shoes"}

PLAIN_TEE = {"name": "White T-Shirt", "category": "tops", "color": "white", "vibe": "casual", "tags": ["tee", "basic"], "_outfit_role": "top"}
CHINOS = {"name": "Navy Chinos", "category": "bottoms", "color": "navy", "vibe": "casual", "tags": ["chinos", "cotton"], "_outfit_role": "bottom"}


class TestItemStyleScores:
    """Test per-item style affinity scoring."""

    def test_formal_item_scores_high_formal(self):
        scores = compute_item_style_scores(BLAZER)
        assert scores["formal"] >= 0.5
        assert scores["formal"] > scores["streetwear"]

    def test_formal_item_dress_shirt(self):
        scores = compute_item_style_scores(DRESS_SHIRT)
        assert scores["formal"] >= 0.4

    def test_casual_item_scores_high_casual(self):
        scores = compute_item_style_scores(PLAIN_TEE)
        assert scores["casual"] >= 0.4
        assert scores["casual"] > scores["formal"]

    def test_streetwear_item_scores_high_streetwear(self):
        scores = compute_item_style_scores(HOODIE)
        assert scores["streetwear"] >= 0.5
        assert scores["streetwear"] > scores["formal"]

    def test_sneakers_score_low_formal(self):
        scores = compute_item_style_scores(SNEAKERS)
        assert scores["formal"] < scores["casual"]

    def test_shorts_score_low_formal(self):
        scores = compute_item_style_scores(SHORTS)
        assert scores["formal"] < 0.3

    def test_monochrome_black_item_scores_high(self):
        scores = compute_item_style_scores({"name": "Black Pants", "color": "black", "category": "bottoms", "_outfit_role": "bottom"})
        assert scores["monochrome"] >= 0.8

    def test_monochrome_colorful_item_scores_lower(self):
        scores = compute_item_style_scores({"name": "Red Dress", "color": "red", "category": "dresses", "_outfit_role": "top"})
        assert scores["monochrome"] <= 0.5

    def test_multiple_keywords_increase_confidence(self):
        item_many_keywords = {"name": "Tailored Formal Blazer Vest", "category": "tops", "color": "black", "vibe": "formal", "tags": ["blazer", "vest", "structured", "formal"], "_outfit_role": "layer"}
        scores = compute_item_style_scores(item_many_keywords)
        assert scores["formal"] >= 0.7

    def test_conflicting_keywords_reduce_score(self):
        item_conflict = {"name": "Casual Hoodie Blazer", "category": "tops", "color": "gray", "vibe": "casual", "tags": ["hoodie", "blazer"], "_outfit_role": "top"}
        scores = compute_item_style_scores(item_conflict)
        # Should not be extremely high for either
        assert scores["formal"] < 0.8
        assert scores["streetwear"] < 0.8

    def test_unknown_item_gets_low_confidence(self):
        item_unknown = {"name": "Mystery Item", "category": "accessories", "color": "unknown", "vibe": "", "tags": [], "_outfit_role": "accessory"}
        scores = compute_item_style_scores(item_unknown)
        assert all(s <= 0.5 for s in scores.values())

    def test_scores_normalized_between_0_and_1(self):
        for item in [BLAZER, GRAPHIC_TEE, HOODIE, SNEAKERS, SHORTS, LOAFERS]:
            scores = compute_item_style_scores(item)
            for style, score in scores.items():
                assert 0.0 <= score <= 1.0, f"{item['name']} has {style}={score} out of range"


class TestHardBlocking:
    """Test hard-block rules for formal mode."""

    def test_shorts_hard_blocked_for_formal(self):
        assert _is_hard_blocked_for_formal(SHORTS) is True

    def test_sneakers_hard_blocked_for_formal(self):
        assert _is_hard_blocked_for_formal(SNEAKERS) is True

    def test_hoodie_hard_blocked_for_formal(self):
        assert _is_hard_blocked_for_formal(HOODIE) is True

    def test_ripped_jeans_hard_blocked_for_formal(self):
        assert _is_hard_blocked_for_formal(RIPPED_JEANS) is True

    def test_cargo_hard_blocked_for_formal(self):
        assert _is_hard_blocked_for_formal(CARGO_PANTS) is True

    def test_blazer_not_blocked_for_formal(self):
        assert _is_hard_blocked_for_formal(BLAZER) is False

    def test_trousers_not_blocked_for_formal(self):
        assert _is_hard_blocked_for_formal(TROUSERS) is False

    def test_loafers_not_blocked_for_formal(self):
        assert _is_hard_blocked_for_formal(LOAFERS) is False

    def test_dress_shirt_not_blocked_for_formal(self):
        assert _is_hard_blocked_for_formal(DRESS_SHIRT) is False


class TestWardrobeFiltering:
    """Test wardrobe filtering by style."""

    def test_formal_filter_rejects_casual_items(self):
        wardrobe = [BLAZER, DRESS_SHIRT, TROUSERS, LOAFERS, SHORTS, SNEAKERS, HOODIE, GRAPHIC_TEE]
        accepted, rejected = filter_wardrobe_by_style(wardrobe, "formal")

        accepted_names = {item["name"] for item in accepted}
        rejected_names = {item["name"] for item in rejected}

        assert "Black Blazer" in accepted_names
        assert "White Dress Shirt" in accepted_names
        assert "Gray Trousers" in accepted_names
        assert "Brown Loafers" in accepted_names

        assert "Khaki Shorts" in rejected_names
        assert "White Sneakers" in rejected_names
        assert "Oversized Black Hoodie" in rejected_names

    def test_streetwear_filter_accepts_streetwear_items(self):
        wardrobe = [HOODIE, CARGO_PANTS, HIGH_TOPS, BOMBER_JACKET, BLAZER, TROUSERS]
        accepted, rejected = filter_wardrobe_by_style(wardrobe, "streetwear")

        accepted_names = {item["name"] for item in accepted}
        assert "Oversized Black Hoodie" in accepted_names
        assert "Black Cargo Pants" in accepted_names
        assert "Black High-Tops" in accepted_names

    def test_casual_filter_is_permissive(self):
        wardrobe = [PLAIN_TEE, CHINOS, SNEAKERS, HOODIE, SHORTS]
        accepted, rejected = filter_wardrobe_by_style(wardrobe, "casual")
        # Casual should accept most items
        assert len(accepted) >= 4

    def test_monochrome_filter_prefers_neutral_colors(self):
        wardrobe = [
            {"name": "Black Shirt", "color": "black", "category": "tops", "_outfit_role": "top"},
            {"name": "Black Pants", "color": "black", "category": "bottoms", "_outfit_role": "bottom"},
            {"name": "Red Dress", "color": "red", "category": "dresses", "_outfit_role": "top"},
        ]
        accepted, rejected = filter_wardrobe_by_style(wardrobe, "monochrome")
        accepted_names = {item["name"] for item in accepted}
        assert "Black Shirt" in accepted_names
        assert "Black Pants" in accepted_names

    def test_filter_fallback_when_too_aggressive(self):
        # Only 1 item would pass strict threshold — should relax
        wardrobe = [
            {"name": "Casual Tee", "color": "white", "category": "tops", "vibe": "casual", "_outfit_role": "top"},
            {"name": "Jeans", "color": "blue", "category": "bottoms", "vibe": "casual", "_outfit_role": "bottom"},
        ]
        accepted, rejected = filter_wardrobe_by_style(wardrobe, "formal")
        # Should still return something usable (relaxed threshold)
        assert len(accepted) + len(rejected) == 2

    def test_style_scores_attached_to_items(self):
        wardrobe = [BLAZER, SNEAKERS]
        accepted, rejected = filter_wardrobe_by_style(wardrobe, "formal")
        for item in accepted + rejected:
            assert "_style_scores" in item
            assert "formal" in item["_style_scores"]
            assert "casual" in item["_style_scores"]
            assert "streetwear" in item["_style_scores"]
            assert "monochrome" in item["_style_scores"]


class TestOutfitStyleCoherence:
    """Test outfit-level style coherence scoring."""

    def test_formal_outfit_passes(self):
        wardrobe = [DRESS_SHIRT, TROUSERS, LOAFERS]
        for item in wardrobe:
            item["_style_scores"] = compute_item_style_scores(item)

        wardrobe_lookup = {item["name"].lower(): item for item in wardrobe}
        result = score_outfit_style_coherence(
            ["White Dress Shirt", "Gray Trousers", "Brown Loafers"],
            "formal",
            wardrobe_lookup,
        )
        assert result["aggregate_score"] > 0.3
        assert len(result["rejection_reasons"]) == 0

    def test_casual_items_in_formal_outfit_fail(self):
        wardrobe = [GRAPHIC_TEE, SHORTS, SNEAKERS]
        for item in wardrobe:
            item["_style_scores"] = compute_item_style_scores(item)

        wardrobe_lookup = {item["name"].lower(): item for item in wardrobe}
        result = score_outfit_style_coherence(
            ["Graphic Tee", "Khaki Shorts", "White Sneakers"],
            "formal",
            wardrobe_lookup,
        )
        assert len(result["rejection_reasons"]) > 0
        assert result["passes_threshold"] is False

    def test_streetwear_outfit_passes_streetwear(self):
        wardrobe = [HOODIE, CARGO_PANTS, HIGH_TOPS]
        for item in wardrobe:
            item["_style_scores"] = compute_item_style_scores(item)

        wardrobe_lookup = {item["name"].lower(): item for item in wardrobe}
        result = score_outfit_style_coherence(
            ["Oversized Black Hoodie", "Black Cargo Pants", "Black High-Tops"],
            "streetwear",
            wardrobe_lookup,
        )
        assert result["aggregate_score"] > 0.3


class TestOutfitValidation:
    """Test batch outfit validation."""

    def test_valid_formal_outfits_pass(self):
        wardrobe = [DRESS_SHIRT, TROUSERS, LOAFERS, BLAZER, OXFORD_SHOES]
        for item in wardrobe:
            item["_style_scores"] = compute_item_style_scores(item)

        outfits = [
            {"items": ["White Dress Shirt", "Gray Trousers", "Brown Loafers"]},
            {"items": ["Black Blazer", "Gray Trousers", "Black Oxford Shoes"]},
        ]
        result = validate_outfits_style(outfits, "formal", wardrobe)
        assert len(result) >= 1

    def test_invalid_outfits_filtered_with_fallback(self):
        wardrobe = [GRAPHIC_TEE, SHORTS, SNEAKERS]
        for item in wardrobe:
            item["_style_scores"] = compute_item_style_scores(item)

        outfits = [
            {"items": ["Graphic Tee", "Khaki Shorts", "White Sneakers"]},
        ]
        result = validate_outfits_style(outfits, "formal", wardrobe)
        # Should still return something (fallback)
        assert len(result) >= 1


class TestColorCompatibility:
    """Test color compatibility validation."""

    def test_monochrome_same_color_valid(self):
        wardrobe_lookup = {
            "black shirt": {"name": "Black Shirt", "color": "black"},
            "black pants": {"name": "Black Pants", "color": "black"},
            "black shoes": {"name": "Black Shoes", "color": "black"},
        }
        result = compute_color_compatibility(
            ["Black Shirt", "Black Pants", "Black Shoes"],
            "monochrome",
            wardrobe_lookup,
        )
        assert result["valid"] is True
        assert result["score"] >= 0.8

    def test_monochrome_mixed_colors_invalid(self):
        wardrobe_lookup = {
            "red shirt": {"name": "Red Shirt", "color": "red"},
            "blue pants": {"name": "Blue Pants", "color": "blue"},
            "green shoes": {"name": "Green Shoes", "color": "green"},
        }
        result = compute_color_compatibility(
            ["Red Shirt", "Blue Pants", "Green Shoes"],
            "monochrome",
            wardrobe_lookup,
        )
        assert result["valid"] is False

    def test_casual_compatible_colors(self):
        wardrobe_lookup = {
            "white shirt": {"name": "White Shirt", "color": "white"},
            "blue jeans": {"name": "Blue Jeans", "color": "blue"},
        }
        result = compute_color_compatibility(
            ["White Shirt", "Blue Jeans"],
            "casual",
            wardrobe_lookup,
        )
        assert result["valid"] is True

    def test_no_colors_detected_is_valid(self):
        wardrobe_lookup = {
            "item a": {"name": "Item A", "color": "unknown"},
        }
        result = compute_color_compatibility(["Item A"], "casual", wardrobe_lookup)
        assert result["valid"] is True


class TestIntegrationScenarios:
    """End-to-end scenarios testing the full filtering pipeline."""

    def test_formal_recommendation_excludes_streetwear(self):
        """Formal mode should never include streetwear-heavy items."""
        wardrobe = [BLAZER, DRESS_SHIRT, TROUSERS, LOAFERS, HOODIE, CARGO_PANTS, SNEAKERS, HIGH_TOPS]
        accepted, rejected = filter_wardrobe_by_style(wardrobe, "formal")

        accepted_names = {item["name"] for item in accepted}
        # Streetwear items must be rejected
        assert "Oversized Black Hoodie" not in accepted_names
        assert "Black Cargo Pants" not in accepted_names
        assert "White Sneakers" not in accepted_names
        assert "Black High-Tops" not in accepted_names

    def test_streetwear_recommendation_reduces_formal(self):
        """Streetwear mode should deprioritize formal-only items."""
        wardrobe = [BLAZER, DRESS_SHIRT, TROUSERS, LOAFERS, HOODIE, CARGO_PANTS, HIGH_TOPS, BOMBER_JACKET]
        accepted, rejected = filter_wardrobe_by_style(wardrobe, "streetwear")

        accepted_names = {item["name"] for item in accepted}
        # Streetwear items should be accepted
        assert "Oversized Black Hoodie" in accepted_names
        assert "Black Cargo Pants" in accepted_names
        assert "Black High-Tops" in accepted_names

    def test_full_pipeline_formal_outfit_quality(self):
        """A formal-filtered wardrobe should produce coherent formal outfits."""
        wardrobe = [BLAZER, DRESS_SHIRT, TROUSERS, LOAFERS, OXFORD_SHOES,
                    HOODIE, CARGO_PANTS, SNEAKERS, SHORTS, GRAPHIC_TEE]

        accepted, _ = filter_wardrobe_by_style(wardrobe, "formal")
        for item in accepted:
            item["_style_scores"] = compute_item_style_scores(item)

        # Build an outfit from accepted items only
        outfit_items = [item["name"] for item in accepted[:3]]
        wardrobe_lookup = {item["name"].lower(): item for item in accepted}

        coherence = score_outfit_style_coherence(outfit_items, "formal", wardrobe_lookup)
        assert coherence["aggregate_score"] >= STYLE_THRESHOLDS["formal"]
