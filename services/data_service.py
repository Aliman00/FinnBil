import asyncio
import json
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass

from webscraper import fetch_finn_data
from config.settings import settings
from utils.exceptions import DataFetchError, DataParsingError
from utils.common import ensure_directory_exists, safe_json_dump
from utils.logging import logger


@dataclass
class FetchResult:
    """Result of fetching car data."""
    success: bool
    cars: List[Dict]
    raw_data: Optional[str] = None
    error_message: Optional[str] = None


class DataService:
    """Handles data fetching and processing operations."""
    
    def __init__(self):
        self.data_dir = Path(settings.app.data_directory)
        ensure_directory_exists(str(self.data_dir))
    
    async def fetch_and_parse_cars(self, url: str) -> FetchResult:
        """
        Fetch and parse car data from Finn.no URL.
        
        Args:
            url: Finn.no URL to fetch data from
            
        Returns:
            FetchResult containing success status, cars data, and any error message
            
        Raises:
            DataFetchError: When data fetching fails
            DataParsingError: When data parsing fails
        """
        try:
            logger.info(f"Fetching car data from URL: {url}")
            result = await fetch_finn_data(url)
            
            if not result or len(result) == 0:
                error_msg = "Ingen data mottatt fra server"
                logger.warning(error_msg)
                return FetchResult(success=False, cars=[], error_message=error_msg)
            
            # Extract the JSON string from the TextContent object
            json_text = result[0].text
            logger.debug(f"Received {len(json_text)} characters of data")
            
            try:
                data = json.loads(json_text)
            except json.JSONDecodeError as e:
                error_msg = f"Feil ved parsing av JSON: {str(e)}"
                logger.error(error_msg)
                return FetchResult(success=False, cars=[], error_message=error_msg)
            
            if data.get("success"):
                parsed_cars = data.get("data", [])
                logger.info(f"Successfully parsed {len(parsed_cars)} cars")
                return FetchResult(
                    success=True,
                    cars=parsed_cars,
                    raw_data=json_text
                )
            else:
                error_msg = data.get('error', 'Ukjent feil fra server')
                logger.warning(f"Server returned error: {error_msg}")
                return FetchResult(
                    success=False,
                    cars=[],
                    error_message=f"Feil ved henting av data: {error_msg}"
                )
                
        except Exception as e:
            error_msg = f"En uventet feil oppstod: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return FetchResult(success=False, cars=[], error_message=error_msg)
    
    
    def save_data_to_file(self, data: List[Dict], filename: str = "finn_data.json") -> bool:
        """
        Save car data to JSON file.
        
        Args:
            data: Car data to save
            filename: Name of the file to save to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            filepath = self.data_dir / filename
            success = safe_json_dump(data, str(filepath))
            if success:
                logger.info(f"Saved {len(data)} cars to {filepath}")
            else:
                logger.error(f"Failed to save data to {filepath}")
            return success
        except Exception as e:
            logger.error(f"Error saving data to file: {str(e)}", exc_info=True)
            return False
    
    @staticmethod
    def calculate_statistics(cars_data: List[Dict]) -> Dict[str, Any]:
        """
        Calculate statistics from car data.
        
        Args:
            cars_data: List of car dictionaries
            
        Returns:
            Dictionary containing calculated statistics
        """
        if not cars_data:
            return {
                'avg_price': 0,
                'avg_mileage': 0,
                'sold_count': 0,
                'total_cars': 0,
                'price_range': {'min': 0, 'max': 0},
                'mileage_range': {'min': 0, 'max': 0},
                'year_range': {'min': 0, 'max': 0}
            }
        
        try:
            # Filter valid prices (exclude 'solgt' and invalid values)
            valid_prices = []
            for car in cars_data:
                price = car.get('price')
                if isinstance(price, (int, float)) and price > 0:
                    valid_prices.append(price)
            
            # Filter valid mileage
            valid_mileage = []
            for car in cars_data:
                mileage = car.get('mileage')
                if isinstance(mileage, (int, float)) and mileage >= 0:
                    valid_mileage.append(mileage)
            
            # Filter valid years
            valid_years = []
            for car in cars_data:
                year = car.get('year')
                if isinstance(year, (int, float)) and year > 1900:
                    valid_years.append(year)
            
            # Count sold cars
            sold_cars = sum(
                1 for car in cars_data 
                if str(car.get('price', '')).lower() == "solgt"
            )
            
            stats = {
                'avg_price': sum(valid_prices) / len(valid_prices) if valid_prices else 0,
                'avg_mileage': sum(valid_mileage) / len(valid_mileage) if valid_mileage else 0,
                'sold_count': sold_cars,
                'total_cars': len(cars_data),
                'price_range': {
                    'min': min(valid_prices) if valid_prices else 0,
                    'max': max(valid_prices) if valid_prices else 0
                },
                'mileage_range': {
                    'min': min(valid_mileage) if valid_mileage else 0,
                    'max': max(valid_mileage) if valid_mileage else 0
                },
                'year_range': {
                    'min': min(valid_years) if valid_years else 0,
                    'max': max(valid_years) if valid_years else 0
                }
            }
            
            logger.debug(f"Calculated statistics for {len(cars_data)} cars")
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating statistics: {str(e)}", exc_info=True)
            # Return empty stats on error
            return {
                'avg_price': 0,
                'avg_mileage': 0,
                'sold_count': 0,
                'total_cars': len(cars_data),
                'price_range': {'min': 0, 'max': 0},
                'mileage_range': {'min': 0, 'max': 0},
                'year_range': {'min': 0, 'max': 0}
            }