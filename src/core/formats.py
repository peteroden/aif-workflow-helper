"""Shared constants and mappings for agent file formats.

This module provides centralized definitions for supported file formats,
their extensions, and glob patterns to avoid duplication across the codebase.
"""

from typing import Dict, List

# Supported format types
SUPPORTED_FORMATS: List[str] = ["json", "yaml", "md"]

# File extension mappings (for saving files)
EXTENSION_MAP: Dict[str, str] = {
    "json": ".json",
    "yaml": ".yaml", 
    "md": ".md"
}

# Glob pattern mappings (for finding files)
GLOB_PATTERN_MAP: Dict[str, str] = {
    "json": "*.json",
    "yaml": "*.yaml",
    "md": "*.md"
}

# Additional extensions to check (e.g., .yml as alternative to .yaml)
ALTERNATIVE_EXTENSIONS: Dict[str, List[str]] = {
    "yaml": [".yml"]
}

def get_file_extension(format: str) -> str:
    """Get the appropriate file extension for the given format.
    
    Args:
        format: Format type (json, yaml, md)
        
    Returns:
        File extension including the dot
        
    Raises:
        ValueError: If format is not supported
    """
    if format not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported format '{format}'. Supported formats: {SUPPORTED_FORMATS}")
    
    return EXTENSION_MAP.get(format, ".json")

def get_glob_pattern(format: str) -> str:
    """Get the glob pattern for finding files of the given format.
    
    Args:
        format: Format type (json, yaml, md)
        
    Returns:
        Glob pattern string
        
    Raises:
        ValueError: If format is not supported
    """
    if format not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported format '{format}'. Supported formats: {SUPPORTED_FORMATS}")
    
    return GLOB_PATTERN_MAP.get(format, "*.json")

def get_alternative_extensions(format: str) -> List[str]:
    """Get alternative file extensions for the given format.
    
    Args:
        format: Format type (json, yaml, md)
        
    Returns:
        List of alternative extensions (empty if none)
    """
    return ALTERNATIVE_EXTENSIONS.get(format, [])

def is_supported_format(format: str) -> bool:
    """Check if the given format is supported.
    
    Args:
        format: Format type to check
        
    Returns:
        True if format is supported, False otherwise
    """
    return format in SUPPORTED_FORMATS