"""
Utility functions for FinnBil Analyzer.
"""
import urllib.parse
import os
import json
from typing import Any, Dict, List, Optional
from pathlib import Path


def is_valid_finn_url(url: str) -> bool:
    """
    Validate that URL is from finn.no and properly formatted.
    
    Args:
        url: The URL to validate
        
    Returns:
        True if valid finn.no URL, False otherwise
    """
    try:
        parsed = urllib.parse.urlparse(url.strip())
        
        # Check if it's a finn.no domain
        if not parsed.netloc.lower() in ['finn.no', 'www.finn.no']:
            return False
        
        # Check if it's using HTTP/HTTPS
        if parsed.scheme not in ['http', 'https']:
            return False
        
        # Check if it's a car search URL
        if not parsed.path.startswith('/mobility/'):
            return False
            
        return True
    except Exception:
        return False


def ensure_directory_exists(directory: str) -> Path:
    """
    Ensure a directory exists, create if it doesn't.
    
    Args:
        directory: Directory path to create
        
    Returns:
        Path object of the directory
    """
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_json_dump(data: Any, filepath: str, **kwargs) -> bool:
    """
    Safely dump data to JSON file with error handling.
    
    Args:
        data: Data to dump
        filepath: File path to write to
        **kwargs: Additional arguments for json.dump
        
    Returns:
        True if successful, False otherwise
    """
    try:
        ensure_directory_exists(os.path.dirname(filepath))
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4, **kwargs)
        return True
    except Exception:
        return False


def safe_json_load(filepath: str) -> Optional[Any]:
    """
    Safely load data from JSON file with error handling.
    
    Args:
        filepath: File path to read from
        
    Returns:
        Loaded data or None if failed
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def truncate_url_for_display(url: str, max_length: int = 50) -> str:
    """
    Truncate URL for display purposes.
    
    Args:
        url: URL to truncate
        max_length: Maximum length before truncation
        
    Returns:
        Truncated URL with ellipsis if needed
    """
    if len(url) <= max_length:
        return url
    return url[:max_length] + "..."


def format_price(price: Any) -> str:
    """
    Format price for display.
    
    Args:
        price: Price value (can be int, float, str)
        
    Returns:
        Formatted price string
    """
    if price is None or str(price).lower() in ['nan', 'none', '']:
        return "N/A"
    
    try:
        if isinstance(price, (int, float)) and price > 0:
            return f"{price:,.0f} kr"
        elif str(price).lower() == "solgt":
            return "Solgt"
        else:
            return str(price)
    except (ValueError, TypeError):
        return "N/A"


def format_mileage(mileage: Any) -> str:
    """
    Format mileage for display.
    
    Args:
        mileage: Mileage value
        
    Returns:
        Formatted mileage string
    """
    if mileage is None or str(mileage).lower() in ['nan', 'none', '']:
        return "N/A"
    
    try:
        if isinstance(mileage, (int, float)) and mileage >= 0:
            return f"{mileage:,.0f} km"
        else:
            return str(mileage)
    except (ValueError, TypeError):
        return "N/A"


def calculate_cars_per_year(mileage: Any, age: Any) -> Optional[float]:
    """
    Calculate kilometers per year.
    
    Args:
        mileage: Total mileage
        age: Age in years
        
    Returns:
        Kilometers per year or None if calculation not possible
    """
    try:
        if (isinstance(mileage, (int, float)) and mileage > 0 and 
            isinstance(age, (int, float)) and age > 0):
            return mileage / age
    except (ValueError, TypeError, ZeroDivisionError):
        pass
    return None


def filter_valid_urls(urls: List[str]) -> List[str]:
    """
    Filter list of URLs to only include valid finn.no URLs.
    
    Args:
        urls: List of URLs to filter
        
    Returns:
        List of valid URLs
    """
    return [url.strip() for url in urls if url.strip() and is_valid_finn_url(url.strip())]
