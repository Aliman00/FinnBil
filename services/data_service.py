import asyncio
import json
import requests
from typing import List, Dict, Optional, Tuple
from webscraper import fetch_finn_data


class DataService:
    """Handles data fetching and processing operations."""
    
    @staticmethod
    async def fetch_and_parse_cars(url: str) -> Tuple[bool, Optional[str], List[Dict], Optional[str]]:
        """
        Fetch and parse car data from Finn.no URL.
        
        Returns:
            Tuple of (success, error_message, parsed_cars_list, raw_json_text)
        """
        try:
            result = await fetch_finn_data(url)
            if not result or len(result) == 0:
                return False, "Ingen data mottatt", [], None
            
            # Extract the JSON string from the TextContent object
            json_text = result[0].text
            data = json.loads(json_text)
            
            if data.get("success"):
                parsed_cars = data.get("data", [])
                return True, None, parsed_cars, json_text
            else:
                error_msg = data.get('error', 'Ukjent feil')
                return False, f"Feil ved henting av data: {error_msg}", [], None
                
        except requests.exceptions.RequestException as e:
            return False, f"Feil ved henting av data: {e}", [], None
        except json.JSONDecodeError as e:
            return False, f"Feil ved parsing av JSON: {e}", [], None
        except Exception as e:
            return False, f"En uventet feil oppstod: {e}", [], None
    
    @staticmethod
    def save_data_to_file(data: List[Dict], filename: str = "finn_data.json") -> None:
        """Save car data to JSON file."""
        # Create data directory if it doesn't exist
        import os
        data_dir = "data"
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        # Save to data directory for Docker persistence
        filepath = os.path.join(data_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    
    @staticmethod
    def calculate_statistics(cars_data: List[Dict]) -> Dict:
        """Calculate statistics from car data."""
        valid_prices = [car['price'] for car in cars_data 
                       if isinstance(car['price'], (int, float))]
        valid_mileage = [car['mileage'] for car in cars_data 
                        if car['mileage'] is not None]
        sold_cars = sum(1 for car in cars_data 
                       if str(car.get('price', '')).lower() == "solgt")
        
        stats = {
            'avg_price': sum(valid_prices) / len(valid_prices) if valid_prices else 0,
            'avg_mileage': sum(valid_mileage) / len(valid_mileage) if valid_mileage else 0,
            'sold_count': sold_cars,
            'total_cars': len(cars_data)
        }
        
        return stats