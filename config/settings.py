"""
Configuration settings for FinnBil Analyzer application.
"""
import os
from typing import Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class AIConfig:
    """AI service configuration."""
    model: str = os.getenv("AI_MODEL", "deepseek/deepseek-chat-v3-0324:free")
    base_url: str = os.getenv("AI_BASE_URL", "https://openrouter.ai/api/v1")
    api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    timeout: int = int(os.getenv("AI_TIMEOUT", "60"))


@dataclass
class ScrapingConfig:
    """Web scraping configuration."""
    max_pages: int = int(os.getenv("MAX_PAGES", "2"))
    rate_limit_delay_min: float = float(os.getenv("RATE_LIMIT_MIN", "2.0"))
    rate_limit_delay_max: float = float(os.getenv("RATE_LIMIT_MAX", "4.0"))
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "10"))
    user_agent: str = os.getenv(
        "USER_AGENT", 
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )


@dataclass
class AppConfig:
    """Application configuration."""
    page_title: str = "FinnBil Analyzer"
    page_icon: str = "🚗"
    layout: str = "wide"
    data_directory: str = "data"
    logs_directory: str = "logs"
    default_finn_url: str = (
        "https://www.finn.no/mobility/search/car"
        "?location=20007&location=20061&location=20003&location=20002"
        "&model=1.813.3074&model=1.813.2000660&price_to=380000"
        "&sales_form=1&sort=MILEAGE_ASC&stored-id=80260642"
        "&wheel_drive=2&year_from=2019"
    )
    max_url_length: int = 1000
    display_url_truncate_length: int = 50


class Settings:
    """Main settings class containing all configuration."""
    
    def __init__(self):
        self.ai = AIConfig()
        self.scraping = ScrapingConfig()
        self.app = AppConfig()
    
    def validate(self) -> None:
        """Validate configuration settings."""
        if not self.ai.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is required")
        
        if self.scraping.rate_limit_delay_min >= self.scraping.rate_limit_delay_max:
            raise ValueError("Rate limit min delay must be less than max delay")
        
        if self.scraping.max_pages < 1:
            raise ValueError("MAX_PAGES must be at least 1")


# Global settings instance
settings = Settings()
