#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(__file__))

from services.price_analysis_service import PriceAnalysisService

def test_price_parsing():
    """Test if the CSV price parsing is working correctly now."""
    print("🧪 Testing Price Analysis Service - Price Parsing Fix")
    print("=" * 60)
    
    # Reset any cached instance to ensure fresh data load
    if hasattr(PriceAnalysisService, '_instance'):
        PriceAnalysisService._instance = None
    
    # Create new instance
    service = PriceAnalysisService.get_instance()
    
    # Check if data loaded
    if service.rav4_data is None or service.rav4_data.empty:
        print("❌ Failed to load RAV4 data")
        return
    
    print(f"✅ Successfully loaded {len(service.rav4_data)} RAV4 records")
    print("\n📊 Sample of loaded data:")
    print(service.rav4_data[['year', 'model_name', 'price']].head(10).to_string())
    
    # Test with a PHEV model like the one showing price=2
    print("\n🔍 Testing 2020 PHEV models specifically:")
    phev_2020 = service.rav4_data[
        (service.rav4_data['year'] == 2020) & 
        (service.rav4_data['model_name'].str.contains('PHEV', na=False))
    ]
    print(phev_2020[['model_name', 'price']].to_string())
    
    # Test the problematic car analysis
    print("\n🚗 Testing problematic car from your example:")
    test_car = {
        'name': 'Toyota RAV4 Plug-in Hybrid',
        'year': 2020,
        'price': 279000,  # Changed from 'current_price' to 'price'
        'mileage': 233000,
        'km_per_year': 46600
    }
    
    print(f"🔍 Looking for matches for: {test_car['name']} ({test_car['year']})")
    
    result = service.analyze_car_value(test_car)
    
    if result is None:
        print("❌ Failed to analyze car - no result returned")
        return
        
    print(f"\nResult for {test_car['name']} ({test_car['year']}):")
    print(f"Original price from match: {result['historical_match']['original_price']}")
    print(f"Model matched: {result['historical_match']['model_name']}")
    print(f"Depreciation: {result['depreciation_analysis']['depreciation_percentage']:.1f}%")
    
    # Check if price is reasonable (should be 400k-600k range for 2020 PHEV)
    original = result['historical_match']['original_price']
    if original < 100000:
        print(f"❌ STILL BROKEN: Original price {original} is too low!")
    elif 400000 <= original <= 600000:
        print(f"✅ FIXED: Original price {original:,} kr is in reasonable range!")
    else:
        print(f"⚠️ SUSPICIOUS: Original price {original:,} kr - check if this is correct")

if __name__ == "__main__":
    test_price_parsing()
