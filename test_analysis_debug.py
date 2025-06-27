#!/usr/bin/env python3
"""
Test script to debug the car analysis system
"""

import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.simple_car_analyzer import car_analyzer

def test_single_car():
    """Test analysis of a single car"""
    
    # Test car data
    test_car = {
        "name": "Toyota RAV4 2.5 AWD Active Style Hybrid",
        "year": 2021,
        "price": 380000,
        "km_per_year": 12000
    }
    
    print("=== TESTING SINGLE CAR ANALYSIS ===")
    print(f"Testing: {test_car}")
    
    # Analyze the car
    result = car_analyzer.analyze_car(test_car)
    
    if 'error' in result:
        print(f"ERROR: {result['error']}")
        return
    
    print("\n=== ANALYSIS RESULT ===")
    print(f"Car: {result['car_info']['name']} ({result['car_info']['year']})")
    print(f"Current price: {result['car_info']['current_price']:,} kr")
    print(f"Age: {result['car_info']['age_years']} years")
    print(f"Mileage: {result['car_info']['km_per_year']} km/year")
    
    print("\n--- Price Analysis ---")
    pa = result['price_analysis']
    print(f"Original price: {pa['original_price']:,} kr")
    print(f"Expected value: {pa['expected_value']:,.0f} kr")
    print(f"Actual depreciation: {pa['actual_depreciation_percent']:.1f}%")
    print(f"Expected depreciation: {pa['expected_depreciation_percent']:.1f}%")
    print(f"Depreciation difference: {pa['depreciation_difference']:+.1f}%")
    print(f"Grade: {pa['grade']}")
    print(f"Assessment: {pa['assessment']}")
    
    print("\n--- Mileage Analysis ---")
    ma = result['mileage_analysis']
    print(f"Grade: {ma['grade']}")
    print(f"Assessment: {ma['assessment']}")
    
    print(f"\n--- Overall ---")
    print(f"Recommendation: {result['recommendation']}")
    print(f"Summary: {result['summary']}")
    
    # Test the interpretation
    print("\n=== INTERPRETATION TEST ===")
    if pa['depreciation_difference'] > 0:
        print(f"✅ CORRECT: Higher actual depreciation (+{pa['depreciation_difference']:.1f}%) = CHEAPER than expected = GOOD for buyer")
    else:
        print(f"❌ PROBLEM: Lower actual depreciation ({pa['depreciation_difference']:+.1f}%) = MORE EXPENSIVE than expected = BAD for buyer")
    
    return result

if __name__ == "__main__":
    test_single_car()
