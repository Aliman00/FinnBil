import pandas as pd
import re
import csv
from io import StringIO
from typing import Dict, Optional, List
from datetime import datetime
import os
import streamlit as st


class SimpleCarAnalyzer:
    """Simplified car analysis using SmartePenger.no depreciation standards."""
    
    # SmartePenger.no CUMULATIVE depreciation rates (total depreciation from new)
    CUMULATIVE_DEPRECIATION = {
        1: 0.20,  # 20% total after 1 year
        2: 0.31,  # 31% total after 2 years  
        3: 0.40,  # 40% total after 3 years
        4: 0.47,  # 47% total after 4 years
        5: 0.53,  # 53% total after 5 years
        6: 0.57   # 57% total after 6+ years
    }
    
    def __init__(self):
        self._rav4_data = None
        self._data_loaded = False
    
    def load_rav4_data(self):
        """Load RAV4 historical price data with proper parsing."""
        if self._data_loaded:
            return
        
        try:
            csv_path = os.path.join(os.path.dirname(__file__), '..', 'rav4.csv')
            
            # Parse the special CSV format manually
            parsed_data = []
            current_year = None
            
            with open(csv_path, 'r', encoding='utf-8') as file:
                for line in file:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Check if line contains a date (year)
                    if line.startswith('01.11.'):
                        year_str = line.split('.')[2].split(',')[0]
                        current_year = int(year_str)
                        continue
                    
                    # Skip header lines
                    if line.startswith('Modellnavn'):
                        continue
                    
                    # Parse car data lines - use proper CSV parsing
                    if current_year and ',' in line and not line.startswith('01.11.'):
                        try:
                            # Use CSV reader to handle quoted fields properly
                            csv_reader = csv.reader(StringIO(line))
                            parts = next(csv_reader)
                            
                            if len(parts) >= 14 and parts[0] and parts[13]:
                                model_name = parts[0].strip()
                                price_str = parts[13].strip()
                                
                                # Clean price string and convert
                                if price_str.isdigit():
                                    price = int(price_str)
                                    parsed_data.append({
                                        'Year': current_year,
                                        'Model': model_name,
                                        'Price': price
                                    })
                                    print(f"Parsed: {current_year} - {model_name} - {price:,} kr")
                                else:
                                    print(f"Invalid price: '{price_str}' for {model_name}")
                        except (ValueError, IndexError, StopIteration) as e:
                            print(f"Error parsing line: {line[:50]}... Error: {e}")
                            continue
            
            # Convert to DataFrame
            self._rav4_data = pd.DataFrame(parsed_data)
            self._data_loaded = True
            print(f"Successfully loaded {len(parsed_data)} RAV4 price records from {len(self._rav4_data['Year'].unique())} years")
            
            # Debug: Show sample data
            if len(parsed_data) > 0:
                print("\nSample data:")
                print(self._rav4_data.head())
                print(f"\nPrice range: {self._rav4_data['Price'].min():,} - {self._rav4_data['Price'].max():,} kr")
            
        except Exception as e:
            print(f"Feil ved lasting av RAV4-data: {e}")
            import traceback
            traceback.print_exc()
            self._rav4_data = None
    
    def get_new_car_price(self, car_year: int, car_name: str) -> Optional[float]:
        """Get original new car price from historical data."""
        if not self._data_loaded:
            self.load_rav4_data()
        
        if self._rav4_data is None or len(self._rav4_data) == 0:
            print(f"Ingen RAV4-data tilgjengelig for {car_name} ({car_year})")
            return None
        
        # Debug: Print available years
        available_years = sorted(self._rav4_data['Year'].unique())
        print(f"Tilgjengelige år i data: {available_years}")
        
        # Find matches for the specific year
        matches = self._rav4_data[self._rav4_data['Year'] == car_year]
        
        if matches.empty:
            # Try adjacent years
            for offset in [1, -1, 2, -2]:
                alt_year = car_year + offset
                matches = self._rav4_data[self._rav4_data['Year'] == alt_year]
                if not matches.empty:
                    print(f"Bruker data fra {alt_year} i stedet for {car_year}")
                    break
        
        if matches.empty:
            print(f"Ingen match funnet for år {car_year} eller nærliggende år")
            return None
        
        # Simple name matching
        car_name_lower = car_name.lower()
        best_match = None
        best_score = 0
        
        print(f"Søker etter match for: '{car_name}' i {len(matches)} modeller")
        
        for _, row in matches.iterrows():
            model_name = str(row['Model']).lower()
            
            # Simple keyword matching
            score = 0
            
            # Basic matching
            if 'hybrid' in car_name_lower and 'hybrid' in model_name:
                score += 2
            if 'phev' in car_name_lower or 'plug-in' in car_name_lower:
                if 'phev' in model_name:
                    score += 3
            
            # Trim level matching
            keywords = ['life', 'active', 'style', 'executive', 'awd', '2wd']
            for keyword in keywords:
                if keyword in car_name_lower and keyword in model_name:
                    score += 1
            
            if score > best_score:
                best_score = score
                best_match = row
                print(f"Ny beste match: '{model_name}' (score: {score})")
        
        if best_match is not None:
            price = float(best_match['Price'])
            print(f"Funnet match: {best_match['Model']} -> {price:,.0f} kr")
            return price
        
        # Fallback to average price for the year
        avg_price = float(matches['Price'].mean())
        print(f"Bruker gjennomsnittspris for {car_year}: {avg_price:,.0f} kr")
        return avg_price
    
    def calculate_expected_value(self, original_price: float, age_years: int) -> Dict:
        """Calculate expected current value using SmartePenger CUMULATIVE depreciation."""
        # Use direct cumulative depreciation rates (much simpler and correct!)
        cumulative_rate = self.CUMULATIVE_DEPRECIATION.get(age_years, self.CUMULATIVE_DEPRECIATION[6])
        
        total_depreciation = original_price * cumulative_rate
        current_value = original_price - total_depreciation
        
        return {
            'expected_value': current_value,
            'total_depreciation_amount': total_depreciation,
            'total_depreciation_percent': cumulative_rate * 100
        }
    
    def analyze_car(self, car_data: Dict) -> Dict:
        """Simple car analysis - the only method you need."""
        
        # Extract basic info
        car_name = car_data.get('name', '')
        car_year = car_data.get('year', 2024)
        current_price = car_data.get('price', 0)
        km_per_year = car_data.get('km_per_year', 15000)
        age_years = max(2024 - car_year, 0)
        
        print(f"\n=== Analyserer: {car_name} ({car_year}) ===")
        print(f"Pris: {current_price:,} kr, km/år: {km_per_year}, alder: {age_years} år")
        
        # Get original new car price
        try:
            original_price = self.get_new_car_price(car_year, car_name)
        except Exception as e:
            print(f"Feil ved henting av nybilpris: {e}")
            return {'error': f'Kunne ikke hente nybilpris: {e}'}
        
        if not original_price or current_price == 0:
            return {'error': 'Mangler prisdata for analyse'}
        
        print(f"Nybilpris: {original_price:,} kr")
        
        # Calculate expected value
        try:
            expected = self.calculate_expected_value(original_price, age_years)
        except Exception as e:
            print(f"Feil ved beregning av forventet verdi: {e}")
            return {'error': f'Feil ved verdiberegning: {e}'}
        
        print(f"Forventet verdi nå: {expected['expected_value']:,.0f} kr")
        
        # Compare actual vs expected
        actual_depreciation_amount = original_price - current_price
        actual_depreciation_percent = (actual_depreciation_amount / original_price) * 100
        
        # How much cheaper/more expensive than expected
        price_difference = current_price - expected['expected_value']
        depreciation_difference = actual_depreciation_percent - expected['total_depreciation_percent']
        
        print(f"Faktisk verdifall: {actual_depreciation_percent:.1f}%")
        print(f"Forventet verdifall: {expected['total_depreciation_percent']:.1f}%")
        print(f"Forskjell: {depreciation_difference:+.1f}% ({'billigere' if depreciation_difference > 0 else 'dyrere'})")
        
        # PRIMARY: Mileage-based recommendation (most important for used cars)
        if km_per_year < 8000:
            primary_grade = 'A'
            mileage_assessment = 'Utmerket - meget lav kjørelengde'
        elif km_per_year < 12000:
            primary_grade = 'A'
            mileage_assessment = 'Utmerket - lav kjørelengde'
        elif km_per_year < 15000:
            primary_grade = 'B'
            mileage_assessment = 'Bra - normal kjørelengde'
        elif km_per_year < 18000:
            primary_grade = 'B'
            mileage_assessment = 'Bra - akseptabel kjørelengde'
        elif km_per_year < 22000:
            primary_grade = 'C'
            mileage_assessment = 'Greit - litt høy kjørelengde'
        elif km_per_year < 28000:
            primary_grade = 'D'
            mileage_assessment = 'Dårlig - høy kjørelengde'
        else:
            primary_grade = 'F'
            mileage_assessment = 'Svært dårlig - ekstrem kjørelengde'
        
        # SECONDARY: Price context (good to know, but not primary factor)
        if depreciation_difference > 10:
            price_grade = 'A'
            price_assessment = 'Underpriset - mye billigere enn forventet'
        elif depreciation_difference > 5:
            price_grade = 'B'
            price_assessment = 'Billig - under forventet pris'
        elif depreciation_difference > -5:
            price_grade = 'C'
            price_assessment = 'Normal pris - som forventet'
        elif depreciation_difference > -10:
            price_grade = 'D'
            price_assessment = 'Dyr - over forventet pris'
        else:
            price_grade = 'F'
            price_assessment = 'Overpriset - mye dyrere enn forventet'
        
        # MAIN GRADE = Mileage grade (this is what matters most)
        grade = primary_grade
        
        # Enhanced assessment combining both factors
        if primary_grade in ['A', 'B'] and price_grade in ['A', 'B']:
            assessment = f"Topp kjøp - {mileage_assessment.lower()} OG {price_assessment.lower()}"
        elif primary_grade in ['A', 'B']:
            assessment = f"Anbefalt - {mileage_assessment.lower()} ({price_assessment.lower()})"
        elif primary_grade == 'C' and price_grade in ['A', 'B']:
            assessment = f"Vurder - {mileage_assessment.lower()} men {price_assessment.lower()}"
        elif primary_grade == 'C':
            assessment = f"Greit valg - {mileage_assessment.lower()} ({price_assessment.lower()})"
        else:
            assessment = f"Frarådes - {mileage_assessment.lower()} ({price_assessment.lower()})"
        
        # INTELLIGENT recommendation: combines mileage (primary) and price (secondary)
        if primary_grade == 'A':  # Excellent mileage (under 12k km/år)
            if price_grade in ['A', 'B']:
                recommendation = '🟢 ANBEFALT - Perfekt: lav kjørelengde og god pris'
            elif price_grade == 'C':
                recommendation = '🟢 ANBEFALT - Utmerket kjørelengde kompenserer for normal pris'
            elif price_grade == 'D':
                recommendation = '🟡 VURDER - Utmerket kjørelengde men dyr pris'
            else:  # F
                recommendation = '🟠 FORSIKTIG - Utmerket kjørelengde men overpriset'
        elif primary_grade == 'B':  # Good mileage (12-18k km/år)
            if price_grade in ['A', 'B']:
                recommendation = '🟢 ANBEFALT - God kjørelengde og attraktiv pris'
            elif price_grade == 'C':
                recommendation = '🟢 ANBEFALT - God kombinasjon'
            elif price_grade == 'D':
                recommendation = '🟡 VURDER - God kjørelengde men dyr'
            else:  # F
                recommendation = '🟠 FORSIKTIG - God kjørelengde men overpriset'
        elif primary_grade == 'C':
            if price_grade in ['A', 'B']:
                recommendation = '🟡 VURDER - Høy kjørelengde men god pris'
            elif price_grade == 'C':
                recommendation = '🟡 VURDER - Gjennomsnittlig bil'
            else:  # D eller F
                recommendation = '🟠 FORSIKTIG - Høy kjørelengde og dyr pris'
        elif primary_grade == 'D':
            if price_grade in ['A', 'B']:
                recommendation = '🟠 FORSIKTIG - Høy kjørelengde men kompenserende pris'
            else:
                recommendation = '🔴 UNNGÅ - Høy kjørelengde'
        else:  # primary_grade == 'F' - Very high mileage (over 30k km/år)
            if price_grade in ['A', 'B']:
                recommendation = '🔴 UNNGÅ - Svært høy kjørelengde selv med god pris'
            else:
                recommendation = '🔴 UNNGÅ - Svært høy kjørelengde og dårlig pris'
        
        print(f"Priskarakter: {price_grade} - {price_assessment}")
        print(f"Kjørelengde: {primary_grade} - {mileage_assessment}")
        print(f"Totalkarakter: {grade} - {assessment}")
        print(f"Anbefaling: {recommendation}")
        
        return {
            'car_info': {
                'name': car_name,
                'year': car_year,
                'age_years': age_years,
                'current_price': current_price,
                'km_per_year': km_per_year
            },
            'price_analysis': {
                'original_price': original_price,
                'expected_value': expected['expected_value'],
                'actual_depreciation_percent': actual_depreciation_percent,
                'expected_depreciation_percent': expected['total_depreciation_percent'],
                'price_difference': price_difference,
                'depreciation_difference': depreciation_difference,
                'grade': price_grade,  # Keep original price grade here
                'assessment': price_assessment
            },
            'mileage_analysis': {
                'km_per_year': km_per_year,
                'grade': primary_grade,
                'assessment': mileage_assessment
            },
            'recommendation': recommendation,
            'summary': f"Totalkarakter {grade} - {assessment}",
            # Add top-level fields for convenience and backward compatibility
            'grade': grade,  # This is now the COMBINED grade
            'overall_assessment': assessment
        }
    
    def analyze_multiple_cars(self, cars_list: List[Dict]) -> Dict:
        """Analyze multiple cars and provide summary."""
        analyses = []
        
        for car in cars_list:
            try:
                analysis = self.analyze_car(car)
                if 'error' not in analysis:
                    analyses.append(analysis)
            except Exception as e:
                print(f"Feil ved analyse av bil {car.get('name', 'Ukjent')}: {e}")
        
        if not analyses:
            return {'error': 'Ingen biler kunne analyseres'}
        
        # Summary stats - use COMBINED grade for overall evaluation
        grades = [a['grade'] for a in analyses]  # This is the combined grade
        grade_counts = {grade: grades.count(grade) for grade in ['A', 'B', 'C', 'D', 'F']}
        
        # Best deals (A/B combined grade) - now properly considers mileage
        good_deals = [a for a in analyses if a['grade'] in ['A', 'B']]
        
        # Sort by MILEAGE FIRST (primary factor), then by grade and price difference
        # Lower km/year = better (manual table sorting logic)
        grade_values = {'A': 4, 'B': 3, 'C': 2, 'D': 1, 'F': 0}
        analyses.sort(key=lambda x: (
            x['car_info']['km_per_year'],  # Primary: lowest mileage first
            -grade_values[x['grade']],     # Secondary: highest grade first (negative for desc)
            -x['price_analysis']['depreciation_difference']  # Tertiary: best price difference
        ))
        
        return {
            'total_cars': len(analyses),
            'grade_distribution': grade_counts,
            'good_deals': len(good_deals),
            'best_deal': analyses[0] if analyses else None,
            'worst_deal': analyses[-1] if analyses else None,
            'all_analyses': analyses
        }
    
    def analyze_car_value(self, name_or_data, year=None, price=None, mileage=None) -> Dict:
        """
        Backward compatibility method for analyze_car_value.
        Supports both old calling style (name, year, price, mileage) and new style (dict).
        """
        if isinstance(name_or_data, dict):
            # New style: dictionary parameter
            return self.analyze_car(name_or_data)
        else:
            # Old style: individual parameters - calculate km_per_year
            age_years = max(2024 - year, 1) if year else 1  # Avoid division by zero
            km_per_year = mileage / age_years if mileage and age_years > 0 else 15000
            
            car_data = {
                'name': name_or_data,
                'year': year,
                'price': price,
                'mileage': mileage,
                'km_per_year': km_per_year
            }
            return self.analyze_car(car_data)


# Singleton instance for easy use
car_analyzer = SimpleCarAnalyzer()
