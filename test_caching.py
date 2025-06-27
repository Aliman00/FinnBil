#!/usr/bin/env python3
"""
Test script to verify PriceAnalysisService caching behavior.
Run this to ensure CSV is only loaded once even with multiple instances.
"""

import time
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.price_analysis_service import PriceAnalysisService


def test_singleton_behavior():
    """Test that multiple instances share the same cached data."""
    print("🧪 Testing PriceAnalysisService Singleton Behavior\n")
    
    # Test 1: First instance (should load CSV)
    print("1️⃣ Creating first instance...")
    start_time = time.time()
    service1 = PriceAnalysisService.get_instance()
    load_time1 = time.time() - start_time
    print(f"   ⏱️ Time taken: {load_time1:.3f}s")
    
    if service1.rav4_data is not None:
        print(f"   ✅ Data loaded: {len(service1.rav4_data)} records")
    else:
        print("   ❌ No data loaded")
    
    print()
    
    # Test 2: Second instance (should use cache)
    print("2️⃣ Creating second instance...")
    start_time = time.time()
    service2 = PriceAnalysisService.get_instance()
    load_time2 = time.time() - start_time
    print(f"   ⏱️ Time taken: {load_time2:.3f}s")
    
    # Test 3: Third instance with direct constructor
    print("3️⃣ Creating third instance with constructor...")
    start_time = time.time()
    service3 = PriceAnalysisService()
    load_time3 = time.time() - start_time
    print(f"   ⏱️ Time taken: {load_time3:.3f}s")
    
    print()
    
    # Verify singleton behavior
    print("🔍 Singleton Verification:")
    print(f"   service1 is service2: {service1 is service2}")
    print(f"   service2 is service3: {service2 is service3}")
    print(f"   All instances identical: {service1 is service2 is service3}")
    
    print()
    
    # Performance comparison
    print("📊 Performance Comparison:")
    print(f"   First load:  {load_time1:.3f}s")
    print(f"   Second load: {load_time2:.3f}s (should be ~0s)")
    print(f"   Third load:  {load_time3:.3f}s (should be ~0s)")
    
    if load_time2 < 0.01 and load_time3 < 0.01:
        print("   ✅ Caching is working correctly!")
        speedup = load_time1 / max(load_time2, 0.001)
        print(f"   🚀 ~{speedup:.0f}x speedup for cached access")
    else:
        print("   ⚠️ Caching might not be working optimally")
    
    print()
    
    # Test cache reset
    print("4️⃣ Testing cache reset...")
    PriceAnalysisService.reset_cache()
    
    print("5️⃣ Creating instance after reset...")
    start_time = time.time()
    service4 = PriceAnalysisService.get_instance()
    load_time4 = time.time() - start_time
    print(f"   ⏱️ Time taken: {load_time4:.3f}s (should be similar to first load)")
    
    if abs(load_time4 - load_time1) < 0.1:
        print("   ✅ Cache reset working correctly!")
    else:
        print("   ⚠️ Cache reset behavior unexpected")


def test_data_consistency():
    """Test that cached data is consistent across instances."""
    print("\n🔬 Testing Data Consistency\n")
    
    service1 = PriceAnalysisService.get_instance()
    service2 = PriceAnalysisService()
    
    if service1.rav4_data is not None and service2.rav4_data is not None:
        print(f"   service1 records: {len(service1.rav4_data)}")
        print(f"   service2 records: {len(service2.rav4_data)}")
        print(f"   Data consistency: {service1.rav4_data is service2.rav4_data}")
        
        if service1.rav4_data is service2.rav4_data:
            print("   ✅ Data objects are identical (shared reference)")
        else:
            print("   ⚠️ Data objects are different (potential issue)")
    else:
        print("   ❌ One or both services have no data")


if __name__ == "__main__":
    print("=" * 60)
    print("🗄️ FINNBIL CACHING SYSTEM TEST")
    print("=" * 60)
    
    try:
        test_singleton_behavior()
        test_data_consistency()
        
        print("\n" + "=" * 60)
        print("✅ CACHE TESTING COMPLETED")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
