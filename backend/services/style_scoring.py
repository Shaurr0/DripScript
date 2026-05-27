"""
Style Scoring Service for Outfit Recommendations.

Computes per-item style affinity scores (formal, casual, streetwear, monochrome)
and enforces strict filtering before outfit generation.
"""

import logging
import re
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)

# --- Style Affinity Keywords ---

FORMAL_POSITIVE = [
    "blazer", "suit", "trousers", "slacks", "dress shirt", "button-up",
    "button up", "button-down", "button down", "oxford", "loafers", "derby",
    "brogues", "dress shoes", "heels", "pumps", "pencil skirt", "tie",
    "bow tie", "vest", "waistcoat", "chinos", "polo", "cardigan",
    "turtleneck", "blouse", "silk", "wool", "linen shirt", "cufflinks",
    "dress pants", "formal", "tailored", "structured",
]

FORMAL_NEGATIVE = [
    "shorts", "sneakers", "hoodie", "graphic tee", "graphic t-shirt",
    "ripped", "distressed", "cargo", "oversized", "tank top", "tank",
    "crop top", "joggers", "sweatpants", "flip flops", "slides",
    "bomber", "beanie", "cap", "backpack", "trainers", "high-tops",
    "basketball", "skateboard", "streetwear", "sporty",
]

CASUAL_POSITIVE = [
    "t-shirt", "tee", "jeans", "sneakers", "hoodie", "shorts",
    "polo", "chinos", "sandals", "loafers", "cardigan", "sweater",
    "sweatshirt", "joggers", "canvas", "denim", "relaxed", "everyday",
    "casual", "comfortable", "cotton", "flannel", "henley",
]

CASUAL_NEGATIVE = [
    "blazer", "suit", "tie", "bow tie", "cufflinks", "formal",
    "tuxedo", "gown", "evening", "cocktail",
]

STREETWEAR_POSITIVE = [
    "hoodie", "cargo", "sneakers", "oversized", "bomber", "graphic",
    "joggers", "high-tops", "trainers", "cap", "beanie", "layered",
    "puffer", "windbreaker", "track", "basketball", "skateboard",
    "denim jacket", "chain", "bucket hat", "crossbody", "backpack",
    "streetwear", "urban", "bold", "statement", "chunky",
]

STREETWEAR_NEGATIVE = [
    "blazer", "suit", "loafers", "oxford", "dress shoes", "tie",
    "bow tie", "formal", "tailored", "pencil skirt", "pumps",
    "cufflinks", "silk blouse", "structured",
]

MONOCHROME_HIGH_COLORS = ["black", "white", "gray", "grey", "charcoal", "cream", "ivory"]
MONOCHROME_MEDIUM_COLORS = ["navy", "brown", "beige", "tan", "khaki", "olive"]
MONOCHROME_LOW_COLORS = ["red", "orange", "yellow", "pink", "purple", "green", "blue", "coral", "teal"]

# --- Hard-block lists for strict filtering ---

FORMAL_HARD_BLOCK = [
    "shorts", "sneakers", "trainers", "high-tops", "hoodie", "joggers",
    "sweatpants", "cargo pants", "cargo shorts", "flip flops", "slides",
    "tank top", "crop top", "graphic tee", "graphic t-shirt", "bomber",
    "puffer", "windbreaker", "backpack", "beanie", "cap", "bucket hat",
]

FORMAL_HARD_BLOCK_PATTERNS = [
    r"\bripped\b", r"\bdistressed\b", r"\boversized\b",
    r"\bgraphic\b", r"\bcargo\b",
]

# --- Thresholds ---

STYLE_THRESHOLDS = {
    "formal": 0.30,
    "casual": 0.15,
    "streetwear": 0.20,
    "monochrome": 0.25,
}

OUTFIT_STYLE_COHERENCE_THRESHOLD = 0.35


def compute_item_style_scores(item: Dict) -> Dict[str, float]:
    """
    Compute style affinity scores for a single wardrobe item.

    Returns dict with keys: formal, casual, streetwear, monochrome (each 0.0-1.0)
    """
    name = (item.get("name") or "").lower()
    category = (item.get("category") or "").lower()
    color = (item.get("color") or "").lower()
    vibe = (item.get("vibe") or "").lower()
    tags = [t.lower() for t in (item.get("tags") or []) if isinstance(t, str)]
    role = (item.get("_outfit_role") or "").lower()

    searchable = f"{name} {category} {' '.join(tags)} {vibe} {role}"

    formal_score = _compute_single_style_score(
        searchable, name, color, vibe, category,
        FORMAL_POSITIVE, FORMAL_NEGATIVE,
        formal_color_bonus=True
    )

    casual_score = _compute_single_style_score(
        searchable, name, color, vibe, category,
        CASUAL_POSITIVE, CASUAL_NEGATIVE,
        casual_color_bonus=True
    )

    streetwear_score = _compute_single_style_score(
        searchable, name, color, vibe, category,
        STREETWEAR_POSITIVE, STREETWEAR_NEGATIVE,
        streetwear_color_bonus=True
    )

    monochrome_score = _compute_monochrome_score(color, name)

    scores = {
        "formal": _clamp(formal_score),
        "casual": _clamp(casual_score),
        "streetwear": _clamp(streetwear_score),
        "monochrome": _clamp(monochrome_score),
    }

    return scores


def _compute_single_style_score(
    searchable: str,
    name: str,
    color: str,
    vibe: str,
    category: str,
    positive_keywords: List[str],
    negative_keywords: List[str],
    formal_color_bonus: bool = False,
    casual_color_bonus: bool = False,
    streetwear_color_bonus: bool = False,
) -> float:
    """Compute a style score based on keyword matching with confidence stacking."""
    score = 0.3  # base neutral score

    # Positive keyword matches (stacking)
    positive_hits = 0
    for kw in positive_keywords:
        if kw in searchable:
            positive_hits += 1
            score += 0.15

    # Negative keyword matches (reduce)
    negative_hits = 0
    for kw in negative_keywords:
        if kw in searchable:
            negative_hits += 1
            score -= 0.12

    # Vibe alignment bonus
    if formal_color_bonus and vibe == "formal":
        score += 0.2
    if casual_color_bonus and vibe == "casual":
        score += 0.15
    if streetwear_color_bonus and vibe in ("trendy", "sporty"):
        score += 0.15

    # Color bonuses
    if formal_color_bonus:
        if color in ("black", "navy", "gray", "grey", "white", "charcoal", "brown"):
            score += 0.05
    if streetwear_color_bonus:
        if color in ("black", "white", "red", "orange", "green"):
            score += 0.05

    # Confidence scaling: more keyword matches = higher confidence
    if positive_hits >= 3:
        score += 0.1
    if negative_hits >= 2:
        score -= 0.1

    return score


def _compute_monochrome_score(color: str, name: str) -> float:
    """Score monochrome affinity based on color and tonal consistency."""
    if not color or color == "unknown":
        return 0.3

    if color in MONOCHROME_HIGH_COLORS:
        return 0.9
    if color in MONOCHROME_MEDIUM_COLORS:
        return 0.6
    if color in MONOCHROME_LOW_COLORS:
        return 0.4

    return 0.3


def _clamp(value: float) -> float:
    """Clamp a score between 0.0 and 1.0."""
    return max(0.0, min(1.0, round(value, 3)))


def _is_hard_blocked_for_formal(item: Dict) -> bool:
    """Check if an item is hard-blocked from formal outfits."""
    name = (item.get("name") or "").lower()

    for blocked in FORMAL_HARD_BLOCK:
        if blocked in name:
            return True

    for pattern in FORMAL_HARD_BLOCK_PATTERNS:
        if re.search(pattern, name):
            return True

    return False


def filter_wardrobe_by_style(
    wardrobe: List[Dict],
    occasion: str,
) -> Tuple[List[Dict], List[Dict]]:
    """
    Filter wardrobe items by style affinity for the given occasion.

    Returns:
        (accepted_items, rejected_items) — both with style scores attached.
    """
    threshold = STYLE_THRESHOLDS.get(occasion, 0.15)
    accepted = []
    rejected = []

    logger.info("[style-filter] === Filtering wardrobe for occasion=%s (threshold=%.2f) ===",
                occasion, threshold)

    for item in wardrobe:
        scores = compute_item_style_scores(item)
        item["_style_scores"] = scores
        style_score = scores.get(occasion, 0.0)

        rejection_reason = None

        # Hard-block check for formal
        if occasion == "formal" and _is_hard_blocked_for_formal(item):
            rejection_reason = "hard-blocked for formal"
            style_score = 0.0

        # Threshold check
        if rejection_reason is None and style_score < threshold:
            rejection_reason = f"score {style_score:.3f} below threshold {threshold:.2f}"

        if rejection_reason:
            logger.info("[style-filter] REJECTED: '%s' — reason: %s | scores: %s",
                        item.get("name", "?"), rejection_reason, scores)
            rejected.append(item)
        else:
            logger.info("[style-filter] ACCEPTED: '%s' — %s_score=%.3f | all_scores: %s",
                        item.get("name", "?"), occasion, style_score, scores)
            accepted.append(item)

    logger.info("[style-filter] Result: %d accepted, %d rejected out of %d total",
                len(accepted), len(rejected), len(wardrobe))

    # Fallback: if filtering is too aggressive, relax threshold
    if len(accepted) < 3 and wardrobe:
        logger.info("[style-filter] Too few items accepted (%d). Relaxing threshold to %.2f",
                    len(accepted), threshold * 0.5)
        relaxed_threshold = threshold * 0.5
        accepted = []
        rejected = []
        for item in wardrobe:
            scores = item.get("_style_scores") or compute_item_style_scores(item)
            style_score = scores.get(occasion, 0.0)

            is_blocked = (occasion == "formal" and _is_hard_blocked_for_formal(item))

            if is_blocked or style_score < relaxed_threshold:
                rejected.append(item)
            else:
                accepted.append(item)

        logger.info("[style-filter] After relaxation: %d accepted, %d rejected",
                    len(accepted), len(rejected))

    return accepted, rejected


def score_outfit_style_coherence(
    outfit_items: List[str],
    occasion: str,
    wardrobe_lookup: Dict[str, Dict],
) -> Dict[str, float]:
    """
    Score an outfit's overall style coherence for the given occasion.

    Returns:
        Dict with: per_item_scores, aggregate_score, passes_threshold, rejection_reasons
    """
    per_item = {}
    total_score = 0.0
    count = 0
    rejection_reasons = []

    for item_name in outfit_items:
        item_data = wardrobe_lookup.get(item_name.lower())
        if not item_data:
            per_item[item_name] = {"score": 0.3, "source": "not_found"}
            total_score += 0.3
            count += 1
            continue

        scores = item_data.get("_style_scores") or compute_item_style_scores(item_data)
        style_score = scores.get(occasion, 0.0)
        per_item[item_name] = {"score": style_score, "all_scores": scores}
        total_score += style_score
        count += 1

        threshold = STYLE_THRESHOLDS.get(occasion, 0.15)
        if style_score < threshold:
            rejection_reasons.append(
                f"'{item_name}' has {occasion}_score={style_score:.3f} (below {threshold:.2f})"
            )

        if occasion == "formal" and _is_hard_blocked_for_formal(item_data):
            rejection_reasons.append(f"'{item_name}' is hard-blocked for formal")

    aggregate = (total_score / count) if count > 0 else 0.0
    passes = aggregate >= OUTFIT_STYLE_COHERENCE_THRESHOLD and len(rejection_reasons) == 0

    return {
        "per_item_scores": per_item,
        "aggregate_score": round(aggregate, 3),
        "passes_threshold": passes,
        "rejection_reasons": rejection_reasons,
    }


def validate_outfit_style(
    outfit: Dict,
    occasion: str,
    wardrobe_lookup: Dict[str, Dict],
) -> Tuple[bool, Dict]:
    """
    Validate a single outfit for style coherence.

    Returns:
        (is_valid, debug_info)
    """
    items = outfit.get("items", [])
    if not items:
        return False, {"reason": "empty outfit"}

    coherence = score_outfit_style_coherence(items, occasion, wardrobe_lookup)

    logger.info("[style-validate] Outfit %s — aggregate=%.3f, passes=%s, reasons=%s",
                items[:3], coherence["aggregate_score"],
                coherence["passes_threshold"], coherence["rejection_reasons"])

    return coherence["passes_threshold"], coherence


def validate_outfits_style(
    outfits: List[Dict],
    occasion: str,
    wardrobe: List[Dict],
) -> List[Dict]:
    """
    Validate a list of outfits for style coherence. Returns only passing outfits.
    Falls back to best-scoring outfits if all fail.
    """
    if not outfits:
        return outfits

    wardrobe_lookup = {item.get("name", "").lower(): item for item in wardrobe}

    valid = []
    scored_all = []

    for outfit in outfits:
        is_valid, debug_info = validate_outfit_style(outfit, occasion, wardrobe_lookup)
        outfit["_style_coherence"] = debug_info
        scored_all.append((outfit, debug_info.get("aggregate_score", 0.0)))

        if is_valid:
            valid.append(outfit)

    if valid:
        logger.info("[style-validate] %d/%d outfits passed style validation for '%s'",
                    len(valid), len(outfits), occasion)
        return valid

    # Fallback: return top-scoring outfits even if they don't pass strict threshold
    scored_all.sort(key=lambda x: -x[1])
    fallback = [outfit for outfit, _ in scored_all[:3]]
    logger.warning("[style-validate] No outfits passed strict validation for '%s'. "
                   "Returning top %d by score.", occasion, len(fallback))
    return fallback


def compute_color_compatibility(
    outfit_items: List[str],
    occasion: str,
    wardrobe_lookup: Dict[str, Dict],
) -> Dict[str, any]:
    """
    Validate color compatibility for an outfit.
    For monochrome: all items should share a color family.
    For others: check for clashing combinations.
    """
    colors = []
    for item_name in outfit_items:
        item_data = wardrobe_lookup.get(item_name.lower())
        if item_data:
            color = (item_data.get("color") or "").lower()
            if color and color != "unknown":
                colors.append(color)

    if not colors:
        return {"valid": True, "reason": "no colors detected", "colors": []}

    unique_colors = list(set(colors))

    if occasion == "monochrome":
        color_families = _group_by_color_family(unique_colors)
        dominant_family = max(color_families.items(), key=lambda x: len(x[1]))[0] if color_families else None
        non_dominant = sum(len(v) for k, v in color_families.items() if k != dominant_family)

        if non_dominant > 1:
            return {
                "valid": False,
                "reason": f"too many color families for monochrome: {color_families}",
                "colors": unique_colors,
                "score": 0.3,
            }
        return {
            "valid": True,
            "reason": "monochrome-compatible",
            "colors": unique_colors,
            "score": 0.9 if non_dominant == 0 else 0.7,
        }

    # For non-monochrome: check for known clashing pairs
    CLASHING_PAIRS = [
        ("red", "orange"), ("red", "pink"), ("orange", "pink"),
        ("green", "red"),  # unless intentional
    ]

    clashes = []
    for c1 in unique_colors:
        for c2 in unique_colors:
            if c1 != c2:
                pair = tuple(sorted([c1, c2]))
                if pair in [(tuple(sorted(p))) for p in CLASHING_PAIRS]:
                    clashes.append(pair)

    if clashes:
        return {
            "valid": False,
            "reason": f"clashing colors: {clashes}",
            "colors": unique_colors,
            "score": 0.4,
        }

    return {"valid": True, "reason": "colors compatible", "colors": unique_colors, "score": 0.8}


def _group_by_color_family(colors: List[str]) -> Dict[str, List[str]]:
    """Group colors into families for monochrome validation."""
    FAMILY_MAP = {
        "black": "dark", "charcoal": "dark", "dark": "dark",
        "white": "light", "cream": "light", "ivory": "light",
        "gray": "neutral", "grey": "neutral", "silver": "neutral", "beige": "neutral", "tan": "neutral",
        "navy": "blue", "blue": "blue", "teal": "blue", "indigo": "blue",
        "red": "red", "burgundy": "red", "maroon": "red", "crimson": "red",
        "green": "green", "olive": "green", "khaki": "green", "forest": "green",
        "brown": "brown", "camel": "brown", "chocolate": "brown",
        "pink": "pink", "rose": "pink", "magenta": "pink",
        "purple": "purple", "violet": "purple", "lavender": "purple",
        "orange": "orange", "coral": "orange", "rust": "orange",
        "yellow": "yellow", "gold": "yellow", "mustard": "yellow",
    }

    families: Dict[str, List[str]] = {}
    for color in colors:
        family = FAMILY_MAP.get(color, color)
        if family not in families:
            families[family] = []
        families[family].append(color)

    return families


def get_style_filter_summary(wardrobe: List[Dict], occasion: str) -> str:
    """Generate a human-readable summary of style filtering for debug output."""
    accepted, rejected = filter_wardrobe_by_style(wardrobe, occasion)

    lines = [f"Style Filter Summary for '{occasion}':"]
    lines.append(f"  Total items: {len(wardrobe)}")
    lines.append(f"  Accepted: {len(accepted)}")
    lines.append(f"  Rejected: {len(rejected)}")

    if rejected:
        lines.append("  Rejected items:")
        for item in rejected[:10]:
            scores = item.get("_style_scores", {})
            lines.append(f"    - {item.get('name', '?')}: {occasion}_score={scores.get(occasion, 0):.3f}")

    return "\n".join(lines)
