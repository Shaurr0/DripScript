"""
FashionCLIP Scoring Service for Outfit Compatibility.

Uses FashionCLIP (patrickjohncyh/fashion-clip) text embeddings to score
outfit coherence, style consistency, and occasion compatibility.

Only used during outfit recommendation ranking — NOT during uploads.
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple
from functools import lru_cache

logger = logging.getLogger(__name__)

_fashionclip_model = None
_fashionclip_tokenizer = None
_load_attempted = False

FASHIONCLIP_MODEL_ID = "patrickjohncyh/fashion-clip"


def _load_fashionclip():
    """Load FashionCLIP model once on first use."""
    global _fashionclip_model, _fashionclip_tokenizer, _load_attempted
    if _load_attempted:
        return
    _load_attempted = True

    try:
        from transformers import CLIPModel, CLIPTokenizerFast
        import torch

        logger.info("Loading FashionCLIP model (%s)...", FASHIONCLIP_MODEL_ID)
        _fashionclip_tokenizer = CLIPTokenizerFast.from_pretrained(FASHIONCLIP_MODEL_ID)
        _fashionclip_model = CLIPModel.from_pretrained(FASHIONCLIP_MODEL_ID)
        _fashionclip_model.eval()
        logger.info("FashionCLIP loaded successfully")
    except Exception as e:
        logger.warning("FashionCLIP unavailable (non-fatal): %s", e)
        _fashionclip_model = None
        _fashionclip_tokenizer = None


def is_available() -> bool:
    """Check if FashionCLIP is loaded and ready."""
    _load_fashionclip()
    return _fashionclip_model is not None and _fashionclip_tokenizer is not None


def _get_text_embedding(text: str) -> Optional[np.ndarray]:
    """Compute a normalized text embedding using FashionCLIP."""
    if not is_available():
        return None

    try:
        import torch

        inputs = _fashionclip_tokenizer(
            text, return_tensors="pt", padding=True, truncation=True, max_length=77
        )
        with torch.no_grad():
            text_features = _fashionclip_model.get_text_features(**inputs)
        embedding = text_features[0].cpu().numpy()
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        return embedding
    except Exception as e:
        logger.debug("FashionCLIP embedding failed for '%s': %s", text[:50], e)
        return None


def _get_batch_embeddings(texts: List[str]) -> Optional[np.ndarray]:
    """Compute normalized embeddings for a batch of texts."""
    if not is_available() or not texts:
        return None

    try:
        import torch

        inputs = _fashionclip_tokenizer(
            texts, return_tensors="pt", padding=True, truncation=True, max_length=77
        )
        with torch.no_grad():
            text_features = _fashionclip_model.get_text_features(**inputs)
        embeddings = text_features.cpu().numpy()
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms = np.where(norms > 0, norms, 1.0)
        embeddings = embeddings / norms
        return embeddings
    except Exception as e:
        logger.debug("FashionCLIP batch embedding failed: %s", e)
        return None


def _build_item_description(item: Dict) -> str:
    """Build a fashion-oriented text description from wardrobe item metadata."""
    parts = []
    color = (item.get("color") or "").strip()
    if color and color != "unknown":
        parts.append(color)

    vibe = (item.get("vibe") or "").strip()
    if vibe and vibe != "unknown":
        parts.append(vibe)

    name = (item.get("name") or "").strip()
    if name:
        parts.append(name)
    else:
        category = (item.get("category") or "clothing").strip()
        parts.append(category)

    pattern = (item.get("pattern") or "").strip()
    if not pattern:
        blip_attrs = item.get("blip_attributes") or {}
        pattern = (blip_attrs.get("pattern") or "").strip()
    if pattern and pattern not in ("solid", "unknown", ""):
        parts.append(f"{pattern} pattern")

    return " ".join(parts)


OCCASION_PROMPTS = {
    "casual": "a relaxed casual everyday outfit with comfortable basics",
    "formal": "a polished formal professional outfit with tailored pieces",
    "streetwear": "a bold urban streetwear outfit with statement pieces and layers",
    "monochrome": "a tonal monochrome outfit in a single color family",
}

COLOR_HARMONY_RULES = {
    ("black", "white"): 1.0,
    ("black", "gray"): 0.9,
    ("navy", "white"): 0.9,
    ("navy", "beige"): 0.85,
    ("white", "blue"): 0.85,
    ("black", "red"): 0.8,
    ("gray", "blue"): 0.8,
    ("brown", "beige"): 0.9,
    ("olive", "brown"): 0.85,
    ("white", "gray"): 0.85,
}


def _color_harmony_bonus(colors: List[str]) -> float:
    """Compute a color harmony bonus based on known good pairings."""
    if len(colors) < 2:
        return 0.0

    unique_colors = list(set(c.lower() for c in colors if c and c != "unknown"))
    if not unique_colors:
        return 0.0

    # Monochrome bonus
    if len(unique_colors) == 1:
        return 0.3

    # Check known harmonious pairs
    bonus = 0.0
    pair_count = 0
    for i in range(len(unique_colors)):
        for j in range(i + 1, len(unique_colors)):
            pair = tuple(sorted([unique_colors[i], unique_colors[j]]))
            score = COLOR_HARMONY_RULES.get(pair, 0.0)
            if score == 0.0:
                score = COLOR_HARMONY_RULES.get((pair[1], pair[0]), 0.0)
            bonus += score
            pair_count += 1

    return (bonus / max(pair_count, 1)) * 0.2


# Embedding cache keyed by item description string
_embedding_cache: Dict[str, np.ndarray] = {}
_MAX_CACHE_SIZE = 200


def _get_cached_embedding(description: str) -> Optional[np.ndarray]:
    """Get or compute a cached embedding for an item description."""
    if description in _embedding_cache:
        return _embedding_cache[description]

    embedding = _get_text_embedding(description)
    if embedding is not None:
        if len(_embedding_cache) >= _MAX_CACHE_SIZE:
            oldest_key = next(iter(_embedding_cache))
            del _embedding_cache[oldest_key]
        _embedding_cache[description] = embedding
    return embedding


def score_outfit(
    outfit_items: List[Dict],
    occasion: str,
    wardrobe_lookup: Dict[str, Dict],
) -> Dict[str, float]:
    """
    Score an outfit's compatibility using FashionCLIP embeddings.

    Returns a dict with:
        - coherence: how well items go together (0-1)
        - occasion_fit: how well the outfit matches the occasion (0-1)
        - color_harmony: color compatibility bonus (0-0.3)
        - total: weighted composite score
    """
    if not is_available() or len(outfit_items) < 2:
        return {"coherence": 0.0, "occasion_fit": 0.0, "color_harmony": 0.0, "total": 0.0}

    # Build descriptions for each item
    descriptions = []
    colors = []
    for item_name in outfit_items:
        item_data = wardrobe_lookup.get(item_name.lower())
        if item_data:
            descriptions.append(_build_item_description(item_data))
            color = (item_data.get("color") or "").lower()
            if color and color != "unknown":
                colors.append(color)
        else:
            descriptions.append(item_name)

    # Get embeddings for all items
    embeddings = []
    for desc in descriptions:
        emb = _get_cached_embedding(desc)
        if emb is not None:
            embeddings.append(emb)

    if len(embeddings) < 2:
        return {"coherence": 0.0, "occasion_fit": 0.0, "color_harmony": 0.0, "total": 0.0}

    embeddings_array = np.array(embeddings)

    # Coherence: average pairwise cosine similarity
    n = len(embeddings_array)
    similarities = []
    for i in range(n):
        for j in range(i + 1, n):
            sim = float(np.dot(embeddings_array[i], embeddings_array[j]))
            similarities.append(sim)
    coherence = float(np.mean(similarities)) if similarities else 0.0
    coherence = max(0.0, min(1.0, (coherence + 1.0) / 2.0))

    # Occasion fit: similarity of outfit centroid to occasion prompt
    occasion_prompt = OCCASION_PROMPTS.get(occasion, f"a stylish {occasion} outfit")
    occasion_embedding = _get_cached_embedding(occasion_prompt)

    occasion_fit = 0.5
    if occasion_embedding is not None:
        centroid = np.mean(embeddings_array, axis=0)
        centroid_norm = np.linalg.norm(centroid)
        if centroid_norm > 0:
            centroid = centroid / centroid_norm
        sim = float(np.dot(centroid, occasion_embedding))
        occasion_fit = max(0.0, min(1.0, (sim + 1.0) / 2.0))

    # Color harmony
    color_harmony = _color_harmony_bonus(colors)

    # Weighted total
    total = (coherence * 0.4) + (occasion_fit * 0.4) + (color_harmony * 0.2)

    return {
        "coherence": round(coherence, 3),
        "occasion_fit": round(occasion_fit, 3),
        "color_harmony": round(color_harmony, 3),
        "total": round(total, 3),
    }


def rank_outfits(
    outfits: List[Dict],
    occasion: str,
    wardrobe: List[Dict],
) -> List[Dict]:
    """
    Score and re-rank candidate outfits using FashionCLIP compatibility scoring.

    Attaches a `fashionclip_score` field to each outfit and sorts by total score descending.
    Falls back gracefully (returns outfits unchanged) if FashionCLIP is unavailable.
    """
    if not is_available():
        logger.info("[fashionclip] Not available — skipping outfit ranking")
        return outfits

    if not outfits:
        return outfits

    wardrobe_lookup = {item.get("name", "").lower(): item for item in wardrobe}

    logger.info("[fashionclip] Scoring %d candidate outfits for occasion=%s", len(outfits), occasion)

    for outfit in outfits:
        items = outfit.get("items", [])
        score = score_outfit(items, occasion, wardrobe_lookup)
        outfit["fashionclip_score"] = score

    outfits.sort(key=lambda o: o.get("fashionclip_score", {}).get("total", 0), reverse=True)

    logger.info(
        "[fashionclip] Ranking complete. Top score=%.3f, Bottom score=%.3f",
        outfits[0].get("fashionclip_score", {}).get("total", 0) if outfits else 0,
        outfits[-1].get("fashionclip_score", {}).get("total", 0) if outfits else 0,
    )

    return outfits
