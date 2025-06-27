import pandas as pd
import re
import csv
from io import StringIO
from typing import Dict, Optional, List, Tuple
from datetime import datetime
import os
import streamlit as st


class DepreciationModel:
    """Depreciation models based on SmartePenger.no industry standards."""
    
    # Depreciation rates from SmartePenger.no
    NEW_CAR_DEPRECIATION = {
        1: 0.20,  # 20% first year
        2: 0.14,  # 14% second year  
        3: 0.13,  # 13% third year
        4: 0.12,  # 12% fourth year
        5: 0.11,  # 11% fifth year
        6: 0.10   # 10% sixth year and onwards
    }
    
    USED_CAR_DEPRECIATION = {
        1: 0.17,  # 17% first year (slightly lower than new)
        2: 0.11,  # 11% second year
        3: 0.11,  # 11% third year
        4: 0.11,  # 11% fourth year
        5: 0.11,  # 11% fifth year
        6: 0.10   # 10% sixth year and onwards
    }
    
    @classmethod
    def calculate_expected_depreciation(cls, original_price: float, age_years: int, is_new_car: bool = True) -> Dict:
        """
        Calculate expected depreciation based on SmartePenger.no models.
        
        Args:
            original_price: Original purchase price
            age_years: Age of the car in years
            is_new_car: Whether it was bought new or used
            
        Returns:
            Dictionary with depreciation calculations
        """
        model = cls.NEW_CAR_DEPRECIATION if is_new_car else cls.USED_CAR_DEPRECIATION
        
        current_value = original_price
        yearly_depreciation = []
        total_depreciation_amount = 0
        
        for year in range(1, age_years + 1):
            # Get depreciation rate for this year (use year 6 rate for years beyond 6)
            rate = model.get(year, model[6])
            
            # Calculate depreciation for this year
            year_depreciation = current_value * rate
            yearly_depreciation.append({
                'year': year,
                'rate_percent': rate * 100,
                'depreciation_amount': year_depreciation,
                'value_before': current_value,
                'value_after': current_value - year_depreciation
            })
            
            current_value -= year_depreciation
            total_depreciation_amount += year_depreciation
        
        total_depreciation_percent = (total_depreciation_amount / original_price) * 100
        
        return {
            'original_price': original_price,
            'expected_current_value': current_value,
            'total_depreciation_amount': total_depreciation_amount,
            'total_depreciation_percent': total_depreciation_percent,
            'annual_depreciation_percent': total_depreciation_percent / age_years if age_years > 0 else 0,
            'yearly_breakdown': yearly_depreciation,
            'model_type': 'new_car' if is_new_car else 'used_car'
        }
    
    @classmethod
    def compare_with_expected(cls, original_price: float, current_price: float, age_years: int, is_new_car: bool = True) -> Dict:
        """
        Compare actual depreciation with expected depreciation.
        
        For used car marketplace analysis:
        - All cars on Finn.no were originally bought new
        - Use is_new_car=True to apply SmartePenger "new car" depreciation rates
        - This calculates what the car SHOULD be worth after X years of depreciation
        
        Args:
            original_price: Original new car price (listepris)
            current_price: Current market price on Finn.no
            age_years: Age of the car in years
            is_new_car: Should be True for marketplace analysis (cars started as new)
            
        Returns:
            Dictionary with comparison analysis
        """
        expected = cls.calculate_expected_depreciation(original_price, age_years, is_new_car)
        
        actual_depreciation_amount = original_price - current_price
        actual_depreciation_percent = (actual_depreciation_amount / original_price) * 100
        
        # Compare with expected
        depreciation_difference = actual_depreciation_percent - expected['total_depreciation_percent']
        value_difference = current_price - expected['expected_current_value']
        
        # Assessment from BUYER's perspective (higher depreciation = better deal)
        if depreciation_difference > 10:
            assessment = "Svært høy verdifall - utmerket kjøpsmulighet"
            value_grade = "A"
        elif depreciation_difference > 5:
            assessment = "Høyere verdifall enn forventet - god kjøpsmulighet"
            value_grade = "B"
        elif depreciation_difference > -5:
            assessment = "Normal verdifall som forventet"
            value_grade = "C"
        elif depreciation_difference > -10:
            assessment = "Lavere verdifall enn forventet - dyrere enn markedet"
            value_grade = "D"
        else:
            assessment = "Svært lav verdifall - overprised for kjøpere"
            value_grade = "F"
        
        return {
            'actual_depreciation': {
                'amount': actual_depreciation_amount,
                'percent': actual_depreciation_percent,
                'current_value': current_price
            },
            'expected_depreciation': expected,
            'comparison': {
                'depreciation_difference_percent': depreciation_difference,
                'value_difference_amount': value_difference,
                'assessment': assessment,
                'value_grade': value_grade,
                'performs_better_than_expected': depreciation_difference < 0,
                'better_deal_for_buyer': depreciation_difference > 0
            }
        }


class PriceAnalysisService:
    """Service for analyzing car prices against historical new car prices."""
    
    _instance = None
    _rav4_data = None
    _data_loaded = False
    
    def __new__(cls):
        """Singleton pattern to ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super(PriceAnalysisService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the service and load data only once."""
        if not PriceAnalysisService._data_loaded:
            print("🔄 Initializing PriceAnalysisService (first time)...")
            self.load_rav4_data()
            PriceAnalysisService._data_loaded = True
        else:
            print("♻️ Using cached PriceAnalysisService instance")
    
    @classmethod
    def get_instance(cls):
        """Get the singleton instance of PriceAnalysisService."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset_cache(cls):
        """Reset the singleton cache (useful for testing or data refresh)."""
        cls._instance = None
        cls._rav4_data = None
        cls._data_loaded = False
        print("🔄 PriceAnalysisService cache reset")
    
    @property
    def rav4_data(self):
        """Get the cached RAV4 data."""
        return PriceAnalysisService._rav4_data
    
    @rav4_data.setter
    def rav4_data(self, value):
        """Set the RAV4 data at class level for shared access."""
        PriceAnalysisService._rav4_data = value
    
    def load_rav4_data(self) -> None:
        """Load RAV4 historical price data from CSV once and cache it."""
        try:
            csv_path = "rav4.csv"
            if not os.path.exists(csv_path):
                print(f"⚠️ Warning: {csv_path} not found. Price analysis will be limited.")
                PriceAnalysisService._rav4_data = None
                return
            
            print(f"📂 Loading RAV4 data from {csv_path}...")
            # Read CSV with custom parsing for the multi-year format
            PriceAnalysisService._rav4_data = self._parse_rav4_csv(csv_path)
            
            if PriceAnalysisService._rav4_data is not None:
                print(f"✅ Successfully loaded {len(PriceAnalysisService._rav4_data)} RAV4 price records from 2019-2024")
            else:
                print("❌ Failed to load RAV4 data")
            
        except Exception as e:
            print(f"❌ Error loading RAV4 data: {e}")
            PriceAnalysisService._rav4_data = None
    
    @st.cache_data(hash_funcs={pd.DataFrame: lambda _: None})
    def _parse_rav4_csv(_self, csv_path: str) -> pd.DataFrame:
        """Parse the multi-year RAV4 CSV format with Streamlit caching."""
        all_data = []
        current_year = None
        
        with open(csv_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Check for year header (e.g., "01.11.2019")
            if re.match(r'\d{2}\.\d{2}\.\d{4}', line):
                year_match = re.search(r'(\d{4})', line)
                if year_match:
                    current_year = int(year_match.group(1))
                continue
            
            # Skip header rows
            if line.startswith('Modellnavn,') or line.count(',') < 5:
                continue
            
            # Parse data rows
            if current_year and ',' in line:
                # Handle CSV parsing properly for quoted values containing commas
                try:
                    # Use proper CSV parsing to handle quoted values
                    csv_reader = csv.reader(StringIO(line))
                    parts = next(csv_reader)
                    
                    if len(parts) >= 14 and parts[0].startswith('RAV4'):
                        # Clean price - remove quotes and convert to int
                        price_str = parts[13].replace('"', '').replace(' ', '')
                        price = int(price_str) if price_str.isdigit() else None
                        
                        if price:
                            record = {
                                'year': current_year,
                                'model_name': parts[0],
                                'type': parts[1],
                                'doors': parts[2],
                                'seats': parts[3],
                                'engine': parts[4],
                                'power_hp_kw': parts[5],
                                'drivetrain': parts[6],
                                'transmission': parts[7],
                                'length': parts[8],
                                'weight': parts[9],
                                'fuel_consumption': parts[10],
                                'co2': parts[11],
                                'nox': parts[12],
                                'price': price
                            }
                            all_data.append(record)
                except (ValueError, IndexError) as e:
                    continue
        
        return pd.DataFrame(all_data)
    
    def find_best_match(self, car_name: str, car_year: int) -> Optional[Dict]:
        """Find the best matching RAV4 model from historical data."""
        if self.rav4_data is None or self.rav4_data.empty:
            return None
        
        # Clean and normalize the car name for matching
        normalized_name = self._normalize_car_name(car_name)
        
        # First try exact year match
        year_matches = self.rav4_data[self.rav4_data['year'] == car_year]
        
        if year_matches.empty:
            # If no exact year, try closest year
            year_matches = self.rav4_data.iloc[(self.rav4_data['year'] - car_year).abs().argsort()]
        
        # Score matches based on name similarity
        best_match = None
        best_score = 0
        
        for _, row in year_matches.head(20).iterrows():  # Check top 20 closest years
            score = self._calculate_match_score(normalized_name, row['model_name'])
            if score > best_score and score > 0.3:  # Minimum similarity threshold
                best_score = score
                best_match = row.to_dict()
        
        return best_match
    
    def _normalize_car_name(self, name: str) -> str:
        """Normalize car name for better matching."""
        # Convert to lowercase and remove common variations
        name = name.lower()
        
        # Standardize hybrid naming
        name = re.sub(r'\bhybrid\b', 'hybrid', name)
        name = re.sub(r'\bphev\b', 'phev', name)
        name = re.sub(r'\bplug[-\s]?in\s+hybrid\b', 'phev', name)
        
        # Standardize drivetrain
        name = re.sub(r'\bawd[-\s]?i?\b', 'awd', name)
        name = re.sub(r'\b2wd\b', '2wd', name)
        name = re.sub(r'\b4wd\b', 'awd', name)
        
        # Standardize trim levels
        name = re.sub(r'\bexecutive\b', 'executive', name)
        name = re.sub(r'\bactive\b', 'active', name)
        name = re.sub(r'\bstyle\b', 'style', name)
        name = re.sub(r'\blife\b', 'life', name)
        
        # Remove transmission info
        name = re.sub(r'\baut(omat)?\b', '', name)
        name = re.sub(r'\bmanual\b', '', name)
        
        return re.sub(r'\s+', ' ', name).strip()
    
    def _calculate_match_score(self, search_name: str, model_name: str) -> float:
        """Calculate similarity score between search name and model name."""
        model_normalized = self._normalize_car_name(model_name)
        
        # Extract key components
        search_tokens = set(search_name.split())
        model_tokens = set(model_normalized.split())
        
        # Calculate token overlap
        common_tokens = search_tokens.intersection(model_tokens)
        total_unique_tokens = search_tokens.union(model_tokens)
        
        if not total_unique_tokens:
            return 0.0
        
        base_score = len(common_tokens) / len(total_unique_tokens)
        
        # Bonus for important matches
        important_tokens = {'hybrid', 'phev', 'awd', 'executive', 'active', 'style', 'life'}
        important_matches = common_tokens.intersection(important_tokens)
        
        bonus = len(important_matches) * 0.1
        
        return min(base_score + bonus, 1.0)
    
    def calculate_depreciation(self, original_price: int, current_market_price: int, 
                            car_year: int) -> Dict:
        """Calculate depreciation metrics."""
        current_year = datetime.now().year
        age = current_year - car_year
        
        # Calculate depreciation
        total_depreciation = original_price - current_market_price
        depreciation_percentage = (total_depreciation / original_price) * 100
        
        # Calculate annual depreciation
        annual_depreciation = total_depreciation / age if age > 0 else 0
        annual_depreciation_percentage = depreciation_percentage / age if age > 0 else 0
        
        return {
            'original_price': original_price,
            'current_market_price': current_market_price,
            'total_depreciation': total_depreciation,
            'depreciation_percentage': round(depreciation_percentage, 1),
            'annual_depreciation': round(annual_depreciation, 0),
            'annual_depreciation_percentage': round(annual_depreciation_percentage, 1),
            'age_years': age
        }
    
    def analyze_car_value(self, car_data: Dict) -> Optional[Dict]:
        """Analyze a car's value against historical new car prices."""
        if not car_data.get('name') or not car_data.get('year') or not car_data.get('price'):
            return None
        
        # Skip if price is "Solgt" or not a number
        if not isinstance(car_data['price'], (int, float)):
            return None
        
        # Find matching historical model
        match = self.find_best_match(car_data['name'], car_data['year'])
        
        if not match:
            return None
        
        # Calculate depreciation metrics
        depreciation = self.calculate_depreciation(
            match['price'], 
            int(car_data['price']), 
            car_data['year']
        )
        
        # Add match information
        result = {
            'car_info': {
                'name': car_data['name'],
                'year': car_data['year'],
                'current_price': car_data['price'],
                'mileage': car_data.get('mileage'),
                'km_per_year': car_data.get('km_per_year')
            },
            'historical_match': {
                'model_name': match['model_name'],
                'year': match['year'],
                'original_price': match['price'],
                'match_confidence': 'high'  # Could be enhanced with actual score
            },
            'depreciation_analysis': depreciation,
            'value_assessment': self._assess_value(depreciation, car_data.get('km_per_year', 0))
        }

        return result
    
    def _assess_value(self, depreciation: Dict, km_per_year: int) -> Dict:
        """Assess if the car represents good value."""
        dep_pct = depreciation['depreciation_percentage']
        annual_dep_pct = depreciation['annual_depreciation_percentage']
        age = depreciation['age_years']
        
        # Typical RAV4 depreciation benchmarks (realistic Norwegian market)
        expected_annual_dep = 10  # ~10% per year for popular Toyota hybrids (8-12% range)
        expected_total_dep = expected_annual_dep * age
        
        # Assess depreciation
        if dep_pct < expected_total_dep - 5:
            dep_assessment = "høy verdi - lav verdifall"
        elif dep_pct > expected_total_dep + 10:
            dep_assessment = "høyt verdifall"
        else:
            dep_assessment = "normalt verdifall"
        
        # Assess mileage
        if km_per_year < 10000:
            mileage_assessment = "lav kjørelengde - positivt"
        elif km_per_year > 20000:
            mileage_assessment = "høy kjørelengde - negativt"
        else:
            mileage_assessment = "normal kjørelengde"
        
        # Overall assessment
        value_score = 50  # Start neutral
        
        # Adjust for depreciation
        if "høy verdi" in dep_assessment:
            value_score += 20
        elif "høyt verdifall" in dep_assessment:
            value_score -= 15
        
        # Adjust for mileage
        if "lav kjørelengde" in mileage_assessment:
            value_score += 15
        elif "høy kjørelengde" in mileage_assessment:
            value_score -= 10
        
        if value_score >= 70:
            overall = "svært god verdi"
        elif value_score >= 55:
            overall = "god verdi"
        elif value_score >= 45:
            overall = "ok verdi"
        else:
            overall = "dårlig verdi"
        
        return {
            'depreciation_assessment': dep_assessment,
            'mileage_assessment': mileage_assessment,
            'overall_assessment': overall,
            'value_score': value_score,
            'expected_annual_depreciation': f"{expected_annual_dep}%",
            'actual_annual_depreciation': f"{annual_dep_pct}%"
        }
    
    def get_analysis_summary(self, cars_data: List[Dict]) -> Dict:
        """Get summary analysis for multiple cars."""
        if not cars_data:
            return {}
        
        analyses = []
        for car in cars_data:
            analysis = self.analyze_car_value(car)
            if analysis:
                analyses.append(analysis)
        
        if not analyses:
            return {}
        
        # Calculate summary statistics
        avg_depreciation = sum(a['depreciation_analysis']['depreciation_percentage'] for a in analyses) / len(analyses)
        
        good_value_count = sum(1 for a in analyses if 'god verdi' in a['value_assessment']['overall_assessment'])
        
        return {
            'total_analyzed': len(analyses),
            'average_depreciation': round(avg_depreciation, 1),
            'good_value_cars': good_value_count,
            'analyses': analyses
        }
    
    def analyze_car_value_with_industry_standard(self, car_data: Dict, is_new_car: bool = False) -> Optional[Dict]:
        """
        Analyze car value using industry standard depreciation models from SmartePenger.no
        
        Args:
            car_data: Dictionary containing car information
            is_new_car: Whether the car was bought new (affects depreciation model)
            
        Returns:
            Dictionary with comprehensive value analysis
        """
        if not car_data or 'year' not in car_data:
            return None
        
        # Skip if price is "Solgt" or not a number
        if not isinstance(car_data['price'], (int, float)):
            return None
        
        # Find matching historical model to get original price
        match = self.find_best_match(car_data['name'], car_data['year'])
        
        if not match:
            return None
        
        current_year = datetime.now().year
        age_years = current_year - car_data['year']
        
        if age_years <= 0:
            return None
        
        # Use SmartePenger depreciation model
        depreciation_analysis = DepreciationModel.compare_with_expected(
            original_price=match['price'],
            current_price=car_data['price'],
            age_years=age_years,
            is_new_car=is_new_car
        )
        
        # Enhanced value assessment
        value_assessment = self._assess_value_with_industry_standard(
            depreciation_analysis, 
            car_data.get('km_per_year', 0),
            age_years
        )
        
        return {
            'car_info': {
                'name': car_data['name'],
                'year': car_data['year'],
                'current_price': car_data['price'],
                'mileage': car_data.get('mileage'),
                'km_per_year': car_data.get('km_per_year'),
                'age_years': age_years
            },
            'historical_match': {
                'model_name': match['model_name'],
                'year': match['year'],
                'original_price': match['price'],
                'match_confidence': 'high'
            },
            'industry_standard_analysis': depreciation_analysis,
            'value_assessment': value_assessment,
            'recommendations': self._generate_recommendations(depreciation_analysis, car_data)
        }
    
    def _assess_value_with_industry_standard(self, depreciation_analysis: Dict, km_per_year: int, age_years: int) -> Dict:
        """Enhanced value assessment using industry standard depreciation models."""
        comparison = depreciation_analysis['comparison']
        actual = depreciation_analysis['actual_depreciation']
        expected = depreciation_analysis['expected_depreciation']
        
        # Assess mileage (industry standard: ~15,000 km/year in Norway)
        if km_per_year < 10000:
            mileage_assessment = "svært lav kjørelengde - stor fordel"
            mileage_score = 20
        elif km_per_year < 15000:
            mileage_assessment = "lav kjørelengde - positivt"
            mileage_score = 10
        elif km_per_year < 20000:
            mileage_assessment = "normal kjørelengde"
            mileage_score = 0
        elif km_per_year < 25000:
            mileage_assessment = "høy kjørelengde - negativt"
            mileage_score = -10
        else:
            mileage_assessment = "svært høy kjørelengde - stor ulempe"
            mileage_score = -20
        
        # Base score from depreciation grade
        grade_scores = {'A': 25, 'B': 15, 'C': 0, 'D': -15, 'F': -25}
        depreciation_score = grade_scores.get(comparison['value_grade'], 0)
        
        # Total value score
        total_score = 50 + depreciation_score + mileage_score
        
        # Final assessment
        if total_score >= 80:
            overall = "utmerket kjøp - svært god verdi"
        elif total_score >= 65:
            overall = "godt kjøp - god verdi"
        elif total_score >= 50:
            overall = "ok kjøp - akseptabel verdi"
        elif total_score >= 35:
            overall = "tvilsomt kjøp - dårlig verdi"
        else:
            overall = "dårlig kjøp - unngå"
        
        return {
            'depreciation_grade': comparison['value_grade'],
            'depreciation_assessment': comparison['assessment'],
            'mileage_assessment': mileage_assessment,
            'overall_assessment': overall,
            'value_score': total_score,
            'price_vs_expected': {
                'expected_price': expected['expected_current_value'],
                'actual_price': actual['current_value'],
                'difference_amount': comparison['value_difference_amount'],
                'difference_percent': (comparison['value_difference_amount'] / expected['expected_current_value']) * 100 if expected['expected_current_value'] > 0 else 0
            }
        }
    
    def _generate_recommendations(self, depreciation_analysis: Dict, car_data: Dict) -> List[str]:
        """Generate recommendations based on the analysis."""
        recommendations = []
        comparison = depreciation_analysis['comparison']
        
        if comparison['value_grade'] in ['A', 'B']:
            recommendations.append("✅ Denne bilen holder verdien godt - anbefalt kjøp")
        elif comparison['value_grade'] == 'C':
            recommendations.append("⚠️ Normal verdifall - vurder andre faktorer som stand og service")
        else:
            recommendations.append("❌ Høyt verdifall - vurder å forhandle om prisen")
        
        # Mileage recommendations
        km_per_year = car_data.get('km_per_year', 0)
        if km_per_year > 20000:
            recommendations.append("⚠️ Høy årlig kjørelengde kan påvirke fremtidig videresalg")
        elif km_per_year < 10000:
            recommendations.append("✅ Lav kjørelengde er positivt for videresalg")
        
        # Price recommendations
        if comparison['value_difference_amount'] > 50000:
            recommendations.append(f"💰 Prisen er {int(comparison['value_difference_amount']):,} kr over forventet markedsverdi")
        elif comparison['value_difference_amount'] < -30000:
            recommendations.append(f"🎯 Prisen er {int(abs(comparison['value_difference_amount'])):,} kr under forventet - godt kjøp!")
        
        return recommendations
    
    def get_depreciation_forecast(self, car_data: Dict, years_ahead: int = 3) -> Optional[Dict]:
        """
        Forecast future depreciation for a car based on industry standards.
        
        Args:
            car_data: Dictionary containing car information
            years_ahead: Number of years to forecast
            
        Returns:
            Dictionary with depreciation forecast
        """
        if not car_data or 'year' not in car_data:
            return None
        
        current_year = datetime.now().year
        current_age = current_year - car_data['year']
        current_price = car_data['price']
        
        if not isinstance(current_price, (int, float)) or current_age <= 0:
            return None
        
        forecast = []
        price = current_price
        
        for year in range(1, years_ahead + 1):
            future_age = current_age + year
            # Use 10% depreciation for cars older than 6 years
            depreciation_rate = DepreciationModel.NEW_CAR_DEPRECIATION.get(future_age, 0.10)
            
            depreciation_amount = price * depreciation_rate
            new_price = price - depreciation_amount
            
            forecast.append({
                'year': current_year + year,
                'age': future_age,
                'estimated_price': int(new_price),
                'depreciation_amount': int(depreciation_amount),
                'depreciation_rate': depreciation_rate * 100
            })
            
            price = new_price
        
        total_depreciation = current_price - price
        
        return {
            'current_info': {
                'year': car_data['year'],
                'current_age': current_age,
                'current_price': current_price
            },
            'forecast': forecast,
            'summary': {
                'total_depreciation': int(total_depreciation),
                'total_depreciation_percent': (total_depreciation / current_price) * 100,
                'final_estimated_value': int(price)
            }
        }
    
    def compare_multiple_cars_industry_standard(self, cars_data: List[Dict]) -> Dict:
        """
        Compare multiple cars using industry standard depreciation models.
        
        Args:
            cars_data: List of car dictionaries
            
        Returns:
            Dictionary with comparative analysis
        """
        if not cars_data:
            return {}
        
        analyses = []
        for car in cars_data:
            analysis = self.analyze_car_value_with_industry_standard(car)
            if analysis:
                analyses.append(analysis)
        
        if not analyses:
            return {'error': 'No cars could be analyzed'}
        
        # Calculate statistics
        grades = [a['value_assessment']['depreciation_grade'] for a in analyses]
        scores = [a['value_assessment']['value_score'] for a in analyses]
        
        # Grade distribution
        grade_counts = {}
        for grade in ['A', 'B', 'C', 'D', 'F']:
            grade_counts[grade] = grades.count(grade)
        
        # Best and worst performers
        best_car = max(analyses, key=lambda x: x['value_assessment']['value_score'])
        worst_car = min(analyses, key=lambda x: x['value_assessment']['value_score'])
        
        # Price efficiency analysis
        price_efficient_cars = [
            a for a in analyses 
            if a['value_assessment']['price_vs_expected']['difference_amount'] < 0
        ]
        
        return {
            'summary': {
                'total_cars': len(analyses),
                'average_score': round(sum(scores) / len(scores), 1),
                'grade_distribution': grade_counts,
                'recommended_cars': len([a for a in analyses if a['value_assessment']['depreciation_grade'] in ['A', 'B']]),
                'price_efficient_cars': len(price_efficient_cars)
            },
            'best_performer': {
                'car': best_car['car_info']['name'],
                'year': best_car['car_info']['year'],
                'price': best_car['car_info']['current_price'],
                'grade': best_car['value_assessment']['depreciation_grade'],
                'score': best_car['value_assessment']['value_score'],
                'assessment': best_car['value_assessment']['overall_assessment']
            },
            'worst_performer': {
                'car': worst_car['car_info']['name'],
                'year': worst_car['car_info']['year'],
                'price': worst_car['car_info']['current_price'],
                'grade': worst_car['value_assessment']['depreciation_grade'],
                'score': worst_car['value_assessment']['value_score'],
                'assessment': worst_car['value_assessment']['overall_assessment']
            },
            'detailed_analyses': analyses,
            'market_insights': self._generate_market_insights(analyses)
        }
    
    def _generate_market_insights(self, analyses: List[Dict]) -> List[str]:
        """Generate market insights based on multiple car analyses."""
        insights = []
        
        if not analyses:
            return insights
        
        # Analyze grade distribution
        grades = [a['value_assessment']['depreciation_grade'] for a in analyses]
        a_b_count = grades.count('A') + grades.count('B')
        
        if a_b_count / len(grades) > 0.6:
            insights.append("📈 Markedet har mange biler med god verdiholdighet")
        elif a_b_count / len(grades) < 0.3:
            insights.append("📉 Få biler holder verdien godt - vær ekstra kritisk")
        
        # Analyze price efficiency
        price_efficient = [
            a for a in analyses 
            if a['value_assessment']['price_vs_expected']['difference_amount'] < -20000
        ]
        
        if len(price_efficient) > 0:
            insights.append(f"💰 {len(price_efficient)} biler er prisgunstig sammenlignet med markedet")
        
        # Age analysis
        ages = [a['car_info']['age_years'] for a in analyses]
        avg_age = sum(ages) / len(ages)
        
        if avg_age > 8:
            insights.append("⚠️ Mange eldre biler - vurder service og reparasjonskostnader")
        elif avg_age < 4:
            insights.append("✨ Mange nyere biler tilgjengelig - god markedssituasjon")
        
        return insights

    def analyze_with_industry_standards(self, car_data: Dict) -> Dict:
        """
        Analyze a single car using SmartePenger.no industry depreciation standards.
        
        Args:
            car_data: Dictionary containing car information
            
        Returns:
            Dictionary with comprehensive analysis including industry comparison
        """
        # Extract car information
        price = car_data.get('price', 0)
        year = car_data.get('year', 2024)
        current_year = 2024
        age_years = max(current_year - year, 0)
        km_per_year = car_data.get('km_per_year', 15000)
        
        # Get historical price analysis first
        historical_analysis = self.analyze_car_value(car_data)
        
        if not historical_analysis or 'historical_match' not in historical_analysis:
            return {
                'error': 'Kunne ikke finne historisk nybilpris for sammenligning',
                'car_info': car_data
            }
        
        original_price = historical_analysis['historical_match']['original_price']
        
        # All cars on Finn.no are used cars that were originally bought new
        # Use SmartePenger "new car" depreciation model to calculate expected value after X years
        industry_comparison = DepreciationModel.compare_with_expected(
            original_price=original_price,
            current_price=price,
            age_years=age_years,
            is_new_car=True  # Always use "new car" model since all cars started as new
        )
        
        # Enhanced assessment
        value_score = self._calculate_value_score(industry_comparison, km_per_year, age_years)
        
        return {
            'car_info': {
                'name': car_data.get('name', 'Ukjent bil'),
                'year': year,
                'current_price': price,
                'age_years': age_years,
                'km_per_year': km_per_year
            },
            'historical_analysis': historical_analysis,
            'industry_standard_analysis': industry_comparison,
            'value_assessment': {
                'value_score': value_score,
                'depreciation_grade': industry_comparison['comparison']['value_grade'],
                'overall_assessment': industry_comparison['comparison']['assessment'],
                'recommendation': self._get_purchase_recommendation(industry_comparison, value_score),
                'price_vs_expected': {
                    'difference_amount': industry_comparison['comparison']['value_difference_amount'],
                    'difference_percent': industry_comparison['comparison']['depreciation_difference_percent']
                }
            }
        }
    
    def analyze_multiple_cars_with_standards(self, cars_list: List[Dict]) -> Dict:
        """
        Analyze multiple cars using industry standards and provide comparative insights.
        
        Args:
            cars_list: List of car dictionaries
            
        Returns:
            Dictionary with comprehensive multi-car analysis
        """
        analyses = []
        
        for car in cars_list:
            try:
                analysis = self.analyze_with_industry_standards(car)
                if 'error' not in analysis:
                    analyses.append(analysis)
            except Exception as e:
                print(f"Feil ved analyse av bil {car.get('name', 'Ukjent')}: {e}")
                continue
        
        if not analyses:
            return {
                'error': 'Ingen biler kunne analyseres',
                'total_cars': len(cars_list)
            }
        
        # Calculate summary statistics
        grades = [a['value_assessment']['depreciation_grade'] for a in analyses]
        scores = [a['value_assessment']['value_score'] for a in analyses]
        
        grade_counts = {grade: grades.count(grade) for grade in ['A', 'B', 'C', 'D', 'F']}
        
        # Find best and worst performers
        best_car = max(analyses, key=lambda x: x['value_assessment']['value_score'])
        worst_car = min(analyses, key=lambda x: x['value_assessment']['value_score'])
        
        # Find price-efficient cars (better than expected)
        price_efficient_cars = [
            a for a in analyses 
            if a['value_assessment']['price_vs_expected']['difference_amount'] < -20000
        ]
        
        return {
            'summary': {
                'total_cars': len(analyses),
                'average_score': round(sum(scores) / len(scores), 1),
                'grade_distribution': grade_counts,
                'recommended_cars': len([a for a in analyses if a['value_assessment']['depreciation_grade'] in ['A', 'B']]),
                'price_efficient_cars': len(price_efficient_cars)
            },
            'best_performer': {
                'car': best_car['car_info']['name'],
                'year': best_car['car_info']['year'],
                'price': best_car['car_info']['current_price'],
                'grade': best_car['value_assessment']['depreciation_grade'],
                'score': best_car['value_assessment']['value_score'],
                'assessment': best_car['value_assessment']['overall_assessment']
            },
            'worst_performer': {
                'car': worst_car['car_info']['name'],
                'year': worst_car['car_info']['year'],
                'price': worst_car['car_info']['current_price'],
                'grade': worst_car['value_assessment']['depreciation_grade'],
                'score': worst_car['value_assessment']['value_score'],
                'assessment': worst_car['value_assessment']['overall_assessment']
            },
            'detailed_analyses': analyses,
            'market_insights': self._generate_enhanced_market_insights(analyses)
        }
    
    def _calculate_value_score(self, industry_comparison: Dict, km_per_year: float, age_years: int) -> float:
        """Calculate overall value score (0-100) based on multiple factors."""
        score = 50  # Base score
        
        # Depreciation performance (40% weight) - FROM BUYER'S PERSPECTIVE
        dep_diff = industry_comparison['comparison']['depreciation_difference_percent']
        if dep_diff > 10:
            score += 20  # Excellent deal - much cheaper than expected
        elif dep_diff > 5:
            score += 15  # Very good deal - cheaper than expected  
        elif dep_diff > 0:
            score += 10  # Good deal - slightly cheaper than expected
        elif dep_diff > -5:
            score += 0   # Normal price - as expected
        elif dep_diff > -10:
            score -= 10  # Expensive - higher price than expected
        else:
            score -= 20  # Very expensive - much higher than expected
        
        # Mileage performance (30% weight) - Lower is better for buyers
        if km_per_year < 10000:
            score += 15  # Excellent - very low mileage
        elif km_per_year < 15000:
            score += 10  # Good - normal mileage  
        elif km_per_year < 20000:
            score += 0   # Acceptable - slightly high mileage
        elif km_per_year < 25000:
            score -= 10  # Poor - high mileage
        else:
            score -= 20  # Very poor - extremely high mileage
        
        # Age factor (30% weight)
        if age_years < 2:
            score += 15  # Very new
        elif age_years < 4:
            score += 10  # New
        elif age_years < 6:
            score += 5   # Moderate age
        elif age_years < 8:
            score += 0   # Getting older
        else:
            score -= 10  # Old
        
        return max(0, min(100, score))
    
    def _get_purchase_recommendation(self, industry_comparison: Dict, value_score: float) -> str:
        """Get purchase recommendation based on analysis - FROM BUYER'S PERSPECTIVE."""
        grade = industry_comparison['comparison']['value_grade']
        dep_diff = industry_comparison['comparison']['depreciation_difference_percent']
        
        if grade == 'A' and value_score >= 80:
            return "🟢 TOPP KJØP - Svært god pris, mye bil for pengene"
        elif grade in ['A', 'B'] and value_score >= 70:
            return "🟢 ANBEFALT - God kjøpsmulighet under markedspris"
        elif grade == 'C' and value_score >= 60:
            return "🟡 VURDER - Markedspris, sammenlign med andre"
        elif grade == 'D':
            return "🟠 FORSIKTIG - Dyrere enn forventet, prut på prisen"
        else:
            return "🔴 UNNGÅ - Overprised, finn billigere alternativer"
    
    def _generate_enhanced_market_insights(self, analyses: List[Dict]) -> List[str]:
        """Generate enhanced market insights based on SmartePenger analysis."""
        insights = []
        
        if not analyses:
            return insights
        
        # Analyze grade distribution
        grades = [a['value_assessment']['depreciation_grade'] for a in analyses]
        a_b_count = grades.count('A') + grades.count('B')
        
        if a_b_count / len(grades) > 0.6:
            insights.append("📈 Markedet har mange biler med utmerket verdiholdighet (SmartePenger-standard)")
        elif a_b_count / len(grades) < 0.3:
            insights.append("📉 Få biler holder verdien godt ifølge industristandarder - vær kritisk")
        
        # Analyze depreciation vs expectations
        better_than_expected = [
            a for a in analyses 
            if a['industry_standard_analysis']['comparison']['depreciation_difference_percent'] < -5
        ]
        
        if len(better_than_expected) > len(analyses) * 0.3:
            insights.append(f"💎 {len(better_than_expected)} biler har bedre verdiholdighet enn SmartePenger-forventet")
        
        # Value score analysis
        scores = [a['value_assessment']['value_score'] for a in analyses]
        avg_score = sum(scores) / len(scores)
        
        if avg_score > 75:
            insights.append("⭐ Høy gjennomsnittlig verdiscore - godt marked for kjøpere")
        elif avg_score < 50:
            insights.append("⚠️ Lav gjennomsnittlig verdiscore - selgers marked")
        
        # Age vs value analysis
        young_cars_good_value = [
            a for a in analyses 
            if a['car_info']['age_years'] < 4 and a['value_assessment']['depreciation_grade'] in ['A', 'B']
        ]
        
        if len(young_cars_good_value) > 0:
            insights.append(f"🚗 {len(young_cars_good_value)} nyere biler (under 4 år) med god verdi tilgjengelig")
        
        return insights

    def _assess_mileage(self, km_per_year: float) -> Dict:
        """Assess mileage from buyer's perspective."""
        if km_per_year < 10000:
            return {
                'grade': 'A',
                'assessment': 'Utmerket - Svært lav kjørelengde',
                'score_impact': 15,
                'buyer_benefit': 'Minimal slitasje, lang restlevetid'
            }
        elif km_per_year < 15000:
            return {
                'grade': 'B', 
                'assessment': 'Bra - Normal kjørelengde',
                'score_impact': 10,
                'buyer_benefit': 'Akseptabel slitasje for alderen'
            }
        elif km_per_year < 20000:
            return {
                'grade': 'C',
                'assessment': 'Greit - Litt høy kjørelengde', 
                'score_impact': 0,
                'buyer_benefit': 'Noe høy bruk, men fortsatt ok'
            }
        elif km_per_year < 25000:
            return {
                'grade': 'D',
                'assessment': 'Dårlig - Høy kjørelengde',
                'score_impact': -10,
                'buyer_benefit': 'Høy slitasje, vurder service-historie'
            }
        else:
            return {
                'grade': 'F',
                'assessment': 'Svært dårlig - Ekstrem kjørelengde',
                'score_impact': -20,
                'buyer_benefit': 'Svært høy slitasje, stor risiko'
            }
