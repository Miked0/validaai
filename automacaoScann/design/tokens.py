"""
Design Token Loader - Loads and provides access to design tokens.
Supports W3C Design Token format (https://design-tokens.github.io/format/)
"""
import json
from pathlib import Path
from typing import Any, Dict, Optional
from functools import lru_cache


class TokenError(Exception):
    """Raised when token loading or resolution fails."""
    pass


def _resolve_value(token: Dict[str, Any]) -> Any:
    """Extract the actual value from a design token dictionary."""
    if not isinstance(token, dict):
        return token
    
    # W3C format: {"value": X, "type": "color", ...}
    if "value" in token:
        return token["value"]
    
    # Nested group - return dict of resolved values
    return {k: _resolve_value(v) for k, v in token.items()}


def _flatten_tokens(tokens: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
    """Flatten nested token structure to dot-notation keys."""
    flat = {}
    for key, value in tokens.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            if "value" in value or "type" in value:
                # Leaf token
                flat[full_key] = _resolve_value(value)
            else:
                # Nested group - recurse
                flat.update(_flatten_tokens(value, full_key))
        else:
            flat[full_key] = value
    return flat


@lru_cache(maxsize=1)
def load_tokens(token_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load design tokens from JSON file.
    
    Args:
        token_path: Path to tokens.json. Defaults to design/tokens.json
                    relative to this file's directory.
    
    Returns:
        Dictionary with both nested and flat (dot-notation) access.
    """
    if token_path is None:
        token_path = Path(__file__).parent / "tokens.json"
    
    if not token_path.exists():
        raise TokenError(f"Token file not found: {token_path}")
    
    try:
        with open(token_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except json.JSONDecodeError as e:
        raise TokenError(f"Invalid JSON in token file: {e}")
    
    # Provide both nested and flat access
    return {
        "nested": raw,
        "flat": _flatten_tokens(raw),
        "path": str(token_path)
    }


def get_token(key: str, default: Any = None, token_path: Optional[Path] = None) -> Any:
    """
    Get a single token value by dot-notation key.
    
    Args:
        key: Dot-notation key (e.g., "color.bg.primary", "spacing.md")
        default: Default value if key not found
        token_path: Optional custom token file path
    
    Returns:
        Token value or default
    """
    tokens = load_tokens(token_path)
    return tokens["flat"].get(key, default)


def get_color(key: str, default: str = "#000000") -> str:
    """Get a color token value (convenience wrapper)."""
    return get_token(f"color.{key}", default)


def get_spacing(key: str, default: int = 0) -> int:
    """Get a spacing token value (convenience wrapper)."""
    return get_token(f"spacing.{key}", default)


def get_typography(key: str, default: Any = None) -> Any:
    """Get a typography token value (convenience wrapper)."""
    return get_token(f"typography.{key}", default)


def get_radius(key: str, default: int = 0) -> int:
    """Get a border radius token value (convenience wrapper)."""
    return get_token(f"radius.{key}", default)


# Convenience: expose commonly used tokens as module-level constants
# These are evaluated at import time
try:
    _TOKENS = load_tokens()
    _FLAT = _TOKENS["flat"]
    
    # Colors
    COLOR_BG_PRIMARY = _FLAT.get("color.bg.primary", "#2C2F33")
    COLOR_BG_CARD = _FLAT.get("color.bg.card", "#23272A")
    COLOR_BG_INPUT = _FLAT.get("color.bg.input", "#1E1F22")
    COLOR_BG_HOVER = _FLAT.get("color.bg.hover", "#2C2F33")
    
    COLOR_FG_PRIMARY = _FLAT.get("color.fg.primary", "#FFFFFF")
    COLOR_FG_MUTED = _FLAT.get("color.fg.muted", "#CCCCCC")
    COLOR_FG_DISABLED = _FLAT.get("color.fg.disabled", "#888888")
    
    COLOR_ACCENT_PRIMARY = _FLAT.get("color.accent.primary", "#5865F2")
    COLOR_ACCENT_HOVER = _FLAT.get("color.accent.hover", "#4752C4")
    COLOR_ACCENT_PRESS = _FLAT.get("color.accent.press", "#3C45A5")
    
    COLOR_SUCCESS = _FLAT.get("color.semantic.success", "#3BA55C")
    COLOR_ERROR = _FLAT.get("color.semantic.error", "#ED4245")
    COLOR_WARNING = _FLAT.get("color.semantic.warning", "#FAA61A")
    COLOR_INFO = _FLAT.get("color.semantic.info", "#5865F2")
    
    COLOR_BORDER_DEFAULT = _FLAT.get("color.border.default", "#40444B")
    COLOR_BORDER_FOCUS = _FLAT.get("color.border.focus", "#5865F2")
    COLOR_BORDER_ERROR = _FLAT.get("color.border.error", "#ED4245")
    
    # Spacing
    SPACING_NONE = _FLAT.get("spacing.none", 0)
    SPACING_XS = _FLAT.get("spacing.xs", 4)
    SPACING_SM = _FLAT.get("spacing.sm", 8)
    SPACING_MD = _FLAT.get("spacing.md", 12)
    SPACING_LG = _FLAT.get("spacing.lg", 16)
    SPACING_XL = _FLAT.get("spacing.xl", 24)
    SPACING_2XL = _FLAT.get("spacing.2xl", 32)
    
    # Typography
    FONT_FAMILY_PRIMARY = _FLAT.get("typography.fontFamily.primary", "Segoe UI")
    FONT_FAMILY_MONO = _FLAT.get("typography.fontFamily.mono", "Consolas")
    
    FONT_WEIGHT_NORMAL = _FLAT.get("typography.fontWeight.normal", 400)
    FONT_WEIGHT_MEDIUM = _FLAT.get("typography.fontWeight.medium", 500)
    FONT_WEIGHT_SEMIBOLD = _FLAT.get("typography.fontWeight.semibold", 600)
    FONT_WEIGHT_BOLD = _FLAT.get("typography.fontWeight.bold", 700)
    
    FONT_SIZE_XS = _FLAT.get("typography.fontSize.xs", 10)
    FONT_SIZE_SM = _FLAT.get("typography.fontSize.sm", 11)
    FONT_SIZE_BASE = _FLAT.get("typography.fontSize.base", 12)
    FONT_SIZE_LG = _FLAT.get("typography.fontSize.lg", 14)
    FONT_SIZE_XL = _FLAT.get("typography.fontSize.xl", 18)
    FONT_SIZE_2XL = _FLAT.get("typography.fontSize.2xl", 22)
    
    LINE_HEIGHT_TIGHT = _FLAT.get("typography.lineHeight.tight", 1.2)
    LINE_HEIGHT_NORMAL = _FLAT.get("typography.lineHeight.normal", 1.5)
    LINE_HEIGHT_RELAXED = _FLAT.get("typography.lineHeight.relaxed", 1.75)
    
    # Radius
    RADIUS_NONE = _FLAT.get("radius.none", 0)
    RADIUS_SM = _FLAT.get("radius.sm", 4)
    RADIUS_MD = _FLAT.get("radius.md", 6)
    RADIUS_LG = _FLAT.get("radius.lg", 8)
    RADIUS_XL = _FLAT.get("radius.xl", 12)
    RADIUS_FULL = _FLAT.get("radius.full", 9999)
    
    # Shadows
    SHADOW_NONE = _FLAT.get("shadow.none", "none")
    SHADOW_SM = _FLAT.get("shadow.sm", "0 1px 2px rgba(0,0,0,0.3)")
    SHADOW_MD = _FLAT.get("shadow.md", "0 4px 8px rgba(0,0,0,0.4)")
    SHADOW_LG = _FLAT.get("shadow.lg", "0 8px 16px rgba(0,0,0,0.5)")
    
    # Transitions
    TRANSITION_FAST = _FLAT.get("transition.fast", "150ms")
    TRANSITION_NORMAL = _FLAT.get("transition.normal", "200ms")
    TRANSITION_SLOW = _FLAT.get("transition.slow", "300ms")
    
except TokenError:
    # Fallback if tokens not found (e.g., during standalone testing)
    COLOR_BG_PRIMARY = "#2C2F33"
    COLOR_BG_CARD = "#23272A"
    COLOR_BG_INPUT = "#1E1F22"
    COLOR_BG_HOVER = "#2C2F33"
    COLOR_FG_PRIMARY = "#FFFFFF"
    COLOR_FG_MUTED = "#CCCCCC"
    COLOR_FG_DISABLED = "#888888"
    COLOR_ACCENT_PRIMARY = "#5865F2"
    COLOR_ACCENT_HOVER = "#4752C4"
    COLOR_ACCENT_PRESS = "#3C45A5"
    COLOR_SUCCESS = "#3BA55C"
    COLOR_ERROR = "#ED4245"
    COLOR_WARNING = "#FAA61A"
    COLOR_INFO = "#5865F2"
    COLOR_BORDER_DEFAULT = "#40444B"
    COLOR_BORDER_FOCUS = "#5865F2"
    COLOR_BORDER_ERROR = "#ED4245"
    SPACING_NONE = 0
    SPACING_XS = 4
    SPACING_SM = 8
    SPACING_MD = 12
    SPACING_LG = 16
    SPACING_XL = 24
    SPACING_2XL = 32
    FONT_FAMILY_PRIMARY = "Segoe UI"
    FONT_FAMILY_MONO = "Consolas"
    FONT_WEIGHT_NORMAL = 400
    FONT_WEIGHT_MEDIUM = 500
    FONT_WEIGHT_SEMIBOLD = 600
    FONT_WEIGHT_BOLD = 700
    FONT_SIZE_XS = 10
    FONT_SIZE_SM = 11
    FONT_SIZE_BASE = 12
    FONT_SIZE_LG = 14
    FONT_SIZE_XL = 18
    FONT_SIZE_2XL = 22
    LINE_HEIGHT_TIGHT = 1.2
    LINE_HEIGHT_NORMAL = 1.5
    LINE_HEIGHT_RELAXED = 1.75
    RADIUS_NONE = 0
    RADIUS_SM = 4
    RADIUS_MD = 6
    RADIUS_LG = 8
    RADIUS_XL = 12
    RADIUS_FULL = 9999
    SHADOW_NONE = "none"
    SHADOW_SM = "0 1px 2px rgba(0,0,0,0.3)"
    SHADOW_MD = "0 4px 8px rgba(0,0,0,0.4)"
    SHADOW_LG = "0 8px 16px rgba(0,0,0,0.5)"
    TRANSITION_FAST = "150ms"
    TRANSITION_NORMAL = "200ms"
    TRANSITION_SLOW = "300ms"


if __name__ == "__main__":
    # Quick verification
    tokens = load_tokens()
    print("Tokens loaded successfully!")
    print(f"Flat keys: {len(tokens['flat'])}")
    print(f"Color bg primary: {get_color('bg.primary')}")
    print(f"Spacing md: {get_spacing('md')}")
    print(f"Font size base: {get_typography('fontSize.base')}")