import asyncio
import json
import requests
import re
import time
import random
from typing import Optional
from bs4 import BeautifulSoup
from mcp.types import Tool, TextContent
import datetime 

from config.settings import settings
from utils.logging import logger


# This function fetches car data from Finn.no and parses it
async def fetch_finn_data(url: str, max_pages: Optional[int] = None):
    """Enhanced version of your parse_car_data function"""
    if max_pages is None:
        max_pages = settings.scraping.max_pages
    
    try:
        headers = {
            'User-Agent': settings.scraping.user_agent
        }
        
        all_cars = []
        
        logger.info(f"Starting to fetch data from {max_pages} pages")
        
        for page in range(max_pages):
            page_url = f"{url}&page={page + 1}" if page > 0 else url
            
            # Add rate limiting to be respectful to finn.no
            if page > 0:
                delay = random.uniform(
                    settings.scraping.rate_limit_delay_min, 
                    settings.scraping.rate_limit_delay_max
                )
                logger.debug(f"Rate limiting: waiting {delay:.1f} seconds")
                await asyncio.sleep(delay)
            
            logger.debug(f"Fetching page {page + 1}/{max_pages}")
            response = requests.get(
                page_url, 
                headers=headers, 
                timeout=settings.scraping.request_timeout
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            cars = parse_page_cars(soup)
            all_cars.extend(cars)
            
            logger.debug(f"Found {len(cars)} cars on page {page + 1}")
            
        logger.info(f"Successfully fetched {len(all_cars)} total cars from {max_pages} pages")
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": True,
                "cars_found": len(all_cars),
                "data": all_cars
            }, ensure_ascii=False)
        )]
        
    except Exception as e:
        error_msg = f"Error fetching finn data: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return [TextContent(
            type="text", 
            text=json.dumps({"success": False, "error": error_msg})
        )]


def parse_page_cars(soup):
    """Your existing parsing logic from main.py"""
    current_year = datetime.datetime.now().year
    parsed_cars_list = []
    successful_car_id_counter = 0

    # Find the main tag with a class that starts with "page-container"
    main_element = soup.find('main', class_=re.compile(r"page-container"))
    if not main_element:
        return []

    # CSS selector to navigate to the container of car listings
    ads_container_selector = 'div:nth-of-type(1) > div:nth-of-type(2) > section > div:nth-of-type(3)'
    ads_container = main_element.select_one(ads_container_selector)
    if not ads_container:
        return []

    # Get all direct div children of ads_container
    car_item_wrapper_divs = ads_container.find_all('div', recursive=False)
    if not car_item_wrapper_divs:
        return []

    # Iterate through potential car ad wrappers
    for car_wrapper_div in car_item_wrapper_divs: 
        article_element = car_wrapper_div.find('article', recursive=False)
        if not article_element:
            article_element = car_wrapper_div.find('article') 
            if not article_element:
                continue
        
        # Initialize dictionary for this potential car
        car_info = {
            'name': None,
            'link': None,
            'image_url': None,
            'additional_info': None,
            'year': None,
            'mileage': None,
            'price': None,
            'age': None,
            'km_per_year': None
        }

        # Image URL
        image_tag = article_element.select_one('div:nth-of-type(2) > div > img')
        if image_tag:
            car_info['image_url'] = image_tag.get('src') or image_tag.get('data-src')

        # Main info container
        info_div = article_element.select_one('div:nth-of-type(3)')
        
        if info_div:
            # Car Name (Model) and Ad Link
            name_tag = info_div.find('h2')
            if name_tag:
                car_info['name'] = name_tag.get_text(strip=True)
                link_tag = name_tag.find('a')
                if link_tag and link_tag.has_attr('href'):
                    ad_url = link_tag['href']
                    if ad_url.startswith('/'):
                        base_url = "https://www.finn.no"
                        ad_url = base_url + ad_url
                    car_info['link'] = ad_url
                    
                    # Extract Finn code from URL
                    finn_code_match = re.search(r'/(\d+)/?$', ad_url)
                    if finn_code_match:
                        car_info['finn_code'] = finn_code_match.group(1) # type: ignore

            # Additional Info
            additional_info_tag = info_div.find('span', class_='text-caption')
            if additional_info_tag:
                car_info['additional_info'] = additional_info_tag.get_text(strip=True)

            # Year and Mileage details
            details_tag = info_div.select_one('span:nth-of-type(2)')
            if details_tag:
                details_text = details_tag.get_text(strip=True)
                
                year_match = re.search(r'\b(19\d{2}|20\d{2})\b', details_text)
                if year_match:
                    year_str = year_match.group(0)
                    if year_str.isdigit():
                        car_info['year'] = int(year_str) # type: ignore
                        car_info['age'] = current_year - car_info['year'] # type: ignore
                
                mileage_match = re.search(r'(\d[\d\s.,]*\s*km)\b', details_text, re.IGNORECASE)
                if mileage_match:
                    raw_mileage_text = mileage_match.group(1)
                    mileage_str_cleaned = re.sub(r'[^\d]', '', raw_mileage_text.lower().replace('km', ''))
                    if mileage_str_cleaned.isdigit():
                        car_info['mileage'] = int(mileage_str_cleaned) # type: ignore

            # Calculate km_per_year
            if car_info['mileage'] is not None and car_info['age'] is not None:
                if car_info['age'] > 0:
                    car_info['km_per_year'] = round(car_info['mileage'] / car_info['age']) # type: ignore
                elif car_info['age'] == 0:
                    car_info['km_per_year'] = car_info['mileage'] # type: ignore
            
            # Price
            price_tag = info_div.select_one('div:nth-of-type(1)')
            if price_tag:
                price_text = price_tag.get_text(strip=True)
                if "solgt" in price_text.lower():
                    car_info['price'] = "Solgt" # type: ignore
                else:
                    price_digits = re.sub(r'[^\d]', '', price_text)
                    if price_digits:
                        car_info['price'] = int(price_digits) # type: ignore

        # Only add to list if essential data like name was found
        if car_info.get('name'): 
            successful_car_id_counter += 1
            car_info['id'] = successful_car_id_counter # type: ignore
            parsed_cars_list.append(car_info)

    return parsed_cars_list


