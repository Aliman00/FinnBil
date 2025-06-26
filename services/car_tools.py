# import requests
# from bs4 import BeautifulSoup
# from typing import Dict, Optional
# import re
# import json
# from lxml import html

# class CarTools:
#     """Simple car data tools without MCP overhead."""
    
#     @staticmethod
#     async def fetch_detailed_car_info(car_url: str) -> Dict:
#         """Fetch detailed car information from Finn.no URL."""
#         try:
#             headers = {
#                 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
#             }
            
#             response = requests.get(car_url, headers=headers, timeout=10)
#             response.raise_for_status()
            
#             soup = BeautifulSoup(response.text, 'lxml')
            
#             # Extract detailed car information using the proven webscraper logic
#             details = {
#                 "url": car_url,
#                 "title": None,
#                 "description": None,
#                 "specifications": {},
#                 "equipment": [],
#                 "heftelser_info": {},
#                 "success": True
#             }
            
#             # Extract title
#             title_tag = soup.find('h1')
#             if title_tag:
#                 details["title"] = title_tag.get_text(strip=True)
            
#             # Extract registration number from specifications for heftelser lookup
#             registration_number = None
            
#             # Find the main content area
#             main_content = soup.find('main')
#             if main_content:
#                 # Look for all sections
#                 sections = main_content.find_all('section') # type: ignore
                
#                 for section in sections:
#                     section_text = section.get_text(strip=True).lower()
                    
#                     # Extract Description (Beskrivelse)
#                     if 'beskrivelse' in section_text or 'description' in section_text:
#                         description = CarTools._extract_description_from_section(section)
#                         if description:
#                             details["description"] = description
                    
#                     # Extract Specifications (Spesifikasjoner)
#                     elif 'spesifikasjoner' in section_text or 'specifications' in section_text:
#                         specs = CarTools._extract_specifications_from_section(section)
#                         details["specifications"].update(specs)
                        
#                         # Look for registration number in specifications
#                         for key, value in specs.items():
#                             if 'registreringsnummer' in key.lower() or 'regnr' in key.lower():
#                                 registration_number = value
                    
#                     # Extract Equipment (Utstyr)
#                     elif 'utstyr' in section_text or 'equipment' in section_text:
#                         equipment = CarTools._extract_equipment_from_section(section)
#                         details["equipment"].extend(equipment)
            
#             # Alternative approach for specs if not found
#             if not details["specifications"]:
#                 specs = CarTools._extract_specifications_alternative(soup)
#                 details["specifications"].update(specs)
                
#                 # Look for registration number in alternative specs
#                 for key, value in specs.items():
#                     if 'registreringsnummer' in key.lower() or 'regnr' in key.lower():
#                         registration_number = value
            
#             if not details["equipment"]:
#                 equipment = CarTools._extract_equipment_alternative(soup)
#                 details["equipment"].extend(equipment)
            
#             # Scrape heftelser info if we found a registration number
#             if registration_number:
#                 heftelser_info = await CarTools.check_car_heftelser(registration_number)
#                 details["heftelser_info"] = heftelser_info
#             else:
#                 details["heftelser_info"] = {"error": "Registreringsnummer ikke funnet"}
            
#             return details
            
#         except Exception as e:
#             return {"error": f"Failed to fetch car info: {str(e)}", "url": car_url, "success": False}
    
#     @staticmethod
#     async def check_car_heftelser(registration_number: str) -> Dict:
#         """Check heftelser for a car using the proven webscraper logic."""
#         try:
#             # Construct the heftelser URL
#             heftelser_url = f"https://rettsstiftelser.brreg.no/nb/oppslag/motorvogn/{registration_number}"
            
#             response = requests.get(heftelser_url, timeout=10)
#             response.raise_for_status()
            
#             tree = html.fromstring(response.content)
            
#             heftelser_info = {
#                 "registration_number": registration_number,
#                 "has_heftelser": True,
#                 "belop": None,
#                 "pantsettere": [],
#                 "status": "success"
#             }
            
#             # Check if there are any liens
#             pant_tekst = "Det er ingen oppføringer på registreringsnummer"
#             if pant_tekst in tree.text_content():
#                 heftelser_info["has_heftelser"] = False
#                 heftelser_info["status"] = "ingen_heftelser"
#                 return heftelser_info
            
#             # Get amount
#             belop_xpath = "//*[contains(text(), 'NOK')]"
#             belop_element = tree.xpath(belop_xpath)
#             if belop_element:
#                 heftelser_info["belop"] = belop_element[0].text.strip()
            
#             # General XPath for all lienholders
#             pantsettere_xpath = "/html/body/main/section/article/div[1]/div/div/div/div/div/div[1]/div/div[2]/text()"
#             pantsettere = tree.xpath(pantsettere_xpath)
            
#             heftelser_info["pantsettere"] = [pantsetter.strip() for pantsetter in pantsettere if pantsetter.strip()]
            
#             if not heftelser_info["pantsettere"]:
#                 heftelser_info["status"] = "ingen_pantsettere_funnet"
            
#             return heftelser_info
            
#         except Exception as e:
#             return {
#                 "registration_number": registration_number,
#                 "error": str(e),
#                 "status": "error"
#             }
    
#     @staticmethod
#     def _extract_description_from_section(section):
#         """Extract description text from a beskrivelse section"""
#         description = None
        
#         # Method 1: Look for paragraphs in the section
#         paragraphs = section.find_all('p')
#         if paragraphs:
#             # Combine all paragraphs
#             desc_parts = []
#             for p in paragraphs:
#                 text = p.get_text(strip=True)
#                 if text and text.lower() != 'beskrivelse':  # Skip the header
#                     desc_parts.append(text)
#             if desc_parts:
#                 description = ' '.join(desc_parts)
        
#         # Method 2: Look for divs with text content
#         if not description:
#             divs = section.find_all('div')
#             for div in divs:
#                 text = div.get_text(strip=True)
#                 if text and len(text) > 20 and text.lower() != 'beskrivelse':
#                     # Check if this div doesn't have many nested elements (likely pure text)
#                     nested_elements = len(div.find_all(['div', 'span', 'p']))
#                     if nested_elements <= 2:  # Allow some nesting but not too much
#                         description = text
#                         break
        
#         # Method 3: Get all text from section excluding header
#         if not description:
#             all_text = section.get_text(strip=True)
#             # Remove the "Beskrivelse" header if it's at the beginning
#             if all_text.lower().startswith('beskrivelse'):
#                 description = all_text[11:].strip()  # Remove "beskrivelse" and clean
#             elif len(all_text) > 20:
#                 description = all_text
        
#         return description if description and len(description) > 10 else None

#     @staticmethod
#     def _extract_specifications_from_section(section):
#         """Extract specifications from a section element"""
#         specs = {}
        
#         # Look for definition lists (dl/dt/dd structure)
#         dl_elements = section.find_all('dl')
#         for dl in dl_elements:
#             dt_elements = dl.find_all('dt')
#             dd_elements = dl.find_all('dd')
            
#             for dt, dd in zip(dt_elements, dd_elements):
#                 key = dt.get_text(strip=True)
#                 value = dd.get_text(strip=True)
#                 if key and value:
#                     specs[key] = value
        
#         # Look for table structures
#         tables = section.find_all('table')
#         for table in tables:
#             rows = table.find_all('tr')
#             for row in rows:
#                 cells = row.find_all(['td', 'th'])
#                 if len(cells) >= 2:
#                     key = cells[0].get_text(strip=True)
#                     value = cells[1].get_text(strip=True)
#                     if key and value:
#                         specs[key] = value
        
#         # Look for div pairs or similar structures
#         divs = section.find_all('div')
#         for i in range(0, len(divs) - 1, 2):
#             if i + 1 < len(divs):
#                 potential_key = divs[i].get_text(strip=True)
#                 potential_value = divs[i + 1].get_text(strip=True)
                
#                 # Check if this looks like a key-value pair
#                 if (len(potential_key) < 50 and len(potential_value) < 200 and 
#                     ':' not in potential_key and potential_key and potential_value):
#                     specs[potential_key] = potential_value
        
#         return specs

#     @staticmethod
#     def _extract_equipment_from_section(section):
#         """Extract equipment list from a section element"""
#         equipment = []
        
#         # Look for unordered/ordered lists
#         lists = section.find_all(['ul', 'ol'])
#         for ul in lists:
#             items = ul.find_all('li')
#             for item in items:
#                 text = item.get_text(strip=True)
#                 if text and len(text) < 100:  # Avoid very long text that's not equipment
#                     equipment.append(text)
        
#         # Look for divs that might contain equipment items
#         divs = section.find_all('div')
#         for div in divs:
#             text = div.get_text(strip=True)
#             # Check if this looks like an equipment item (short, descriptive text)
#             if (text and len(text.split()) <= 5 and len(text) < 50 and 
#                 not any(char.isdigit() for char in text[:10])):  # Avoid specs that start with numbers
#                 if text not in equipment:  # Avoid duplicates
#                     equipment.append(text)
        
#         return equipment

#     @staticmethod
#     def _extract_specifications_alternative(soup):
#         """Alternative method to extract specifications if section-based approach fails"""
#         specs = {}
        
#         # Look for any element that might contain specifications
#         spec_keywords = ['motor', 'drivstoff', 'girkasse', 'hjuldrift', 'årsmodell', 'kilometer', 
#                         'effekt', 'sylindre', 'co2', 'forbruk', 'toppfart', 'acceleration']
        
#         for keyword in spec_keywords:
#             # Look for text that contains the keyword followed by a value
#             pattern = rf'{keyword}[:\s]*([^\n\r,]+)'
#             matches = re.findall(pattern, soup.get_text(), re.IGNORECASE)
#             if matches:
#                 specs[keyword.capitalize()] = matches[0].strip()
        
#         return specs

#     @staticmethod
#     def _extract_equipment_alternative(soup):
#         """Alternative method to extract equipment if section-based approach fails"""
#         equipment = []
        
#         # Common Norwegian car equipment terms
#         equipment_keywords = [
#             'klimaanlegg', 'aircondition', 'cruisecontrol', 'navigasjon', 'gps',
#             'bluetooth', 'dab', 'radio', 'cd', 'mp3', 'usb', 'aux',
#             'elektriske', 'oppvarming', 'kjøling', 'automatisk', 'manuell',
#             'sportsseter', 'skinnseter', 'elektrisk', 'parkeringssensor',
#             'ryggekamera', 'xenon', 'led', 'tåkelys', 'metallic', 'felger'
#         ]
        
#         soup_text = soup.get_text().lower()
        
#         for keyword in equipment_keywords:
#             if keyword in soup_text:
#                 # Try to extract the full equipment name around the keyword
#                 pattern = f'([^.\n]*{keyword}[^.\n]*)'
#                 matches = re.findall(pattern, soup_text, re.IGNORECASE)
#                 for match in matches:
#                     clean_match = match.strip()
#                     if 10 < len(clean_match) < 50:  # Reasonable length for equipment item
#                         equipment.append(clean_match.capitalize())
        
#         return list(set(equipment))  # Remove duplicates