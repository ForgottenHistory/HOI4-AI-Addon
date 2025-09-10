#!/usr/bin/env python3
"""
Shared Utilities
Common utility functions used across services and analyzers
"""

from typing import List, Optional, Dict, Any


def has_dynamic_text(text: str) -> bool:
    """
    Check if text contains dynamic placeholders like [FROM.GetName]
    
    This function consolidates duplicate logic from multiple analyzer classes.
    Dynamic text indicates content that will be replaced at runtime by the game engine.
    
    Args:
        text: Text to check for dynamic content
        
    Returns:
        True if text contains dynamic placeholders, False otherwise
        
    Examples:
        >>> has_dynamic_text("Germany declares war")
        False
        >>> has_dynamic_text("[FROM.GetName] declares war on [ROOT.GetName]")
        True
        >>> has_dynamic_text("The ROOT.GetAdjective army advances")
        True
    """
    if not text:
        return False
    
    # Check for square bracket patterns (most common)
    if '[' in text and ']' in text:
        return True
    
    # Check for other dynamic patterns
    dynamic_patterns = ['ROOT.', 'FROM.', 'THIS.', 'PREV.', '.Get']
    return any(pattern in text for pattern in dynamic_patterns)


def clean_text_for_display(text: str, max_length: Optional[int] = None) -> str:
    """
    Clean text for display by removing newlines and optionally truncating
    
    Args:
        text: Text to clean
        max_length: Optional maximum length for truncation
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Clean up newlines and extra whitespace
    cleaned = text.replace('\\n', ' ').replace('\n', ' ').strip()
    
    # Truncate if requested
    if max_length and len(cleaned) > max_length:
        cleaned = cleaned[:max_length] + "..."
    
    return cleaned


def truncate_description(description: str, truncate: bool = False, max_length: int = 150) -> str:
    """
    Truncate description text with consistent formatting
    
    This consolidates the truncation logic found in multiple analyzers.
    
    Args:
        description: Description text to process
        truncate: Whether to truncate the text
        max_length: Maximum length when truncating
        
    Returns:
        Processed description text
    """
    if not description:
        return ""
    
    # Clean up newlines
    cleaned = description.replace('\\n', ' ').strip()
    
    # Truncate if requested
    if truncate and len(cleaned) > max_length:
        cleaned = cleaned[:max_length] + "..."
    
    return cleaned


def filter_dynamic_content(items: List[str]) -> List[str]:
    """
    Filter out items that contain dynamic text
    
    Args:
        items: List of text items to filter
        
    Returns:
        List with dynamic content removed
    """
    return [item for item in items if not has_dynamic_text(item)]


def get_major_power_tags() -> set:
    """
    Get the canonical set of major power country tags
    
    This centralizes the hardcoded major power detection logic
    found across multiple files.
    
    Returns:
        Set of major power country tags
    """
    return {'GER', 'SOV', 'USA', 'ENG', 'FRA', 'ITA', 'JAP'}


def is_major_power(tag: str) -> bool:
    """
    Check if a country tag represents a major power
    
    Args:
        tag: Country tag to check
        
    Returns:
        True if the country is a major power
    """
    return tag in get_major_power_tags()


def format_percentage(value: float, decimals: int = 1) -> str:
    """
    Format a decimal value as a percentage
    
    Args:
        value: Decimal value (0.0 to 1.0)
        decimals: Number of decimal places
        
    Returns:
        Formatted percentage string
    """
    percentage = value * 100 if value <= 1.0 else value
    return f"{percentage:.{decimals}f}%"


def safe_get_nested(data: Dict[str, Any], path: str, default: Any = None) -> Any:
    """
    Safely get nested dictionary values using dot notation
    
    Args:
        data: Dictionary to search
        path: Dot-separated path (e.g., "politics.ruling_party")
        default: Default value if path not found
        
    Returns:
        Value at path or default
        
    Examples:
        >>> data = {"politics": {"ruling_party": "fascism"}}
        >>> safe_get_nested(data, "politics.ruling_party")
        "fascism"
        >>> safe_get_nested(data, "politics.nonexistent", "unknown")
        "unknown"
    """
    try:
        current = data
        for key in path.split('.'):
            current = current[key]
        return current
    except (KeyError, TypeError):
        return default


def create_country_display_name(tag: str, country_name: str, ideology: Optional[str] = None) -> str:
    """
    Create a display name for a country
    
    Args:
        tag: Country tag
        country_name: Base country name
        ideology: Optional ideology for ideological variants
        
    Returns:
        Formatted display name
    """
    if ideology and ideology != 'neutrality':
        # For non-neutral ideologies, the name might already include ideology
        return country_name
    return country_name


# Legacy compatibility aliases
_has_dynamic_text = has_dynamic_text  # For existing code that uses the private method name