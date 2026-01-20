#!/usr/bin/env python3
"""
Test script for the Download API functionality.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vnstock import Download
from datetime import datetime, timedelta

def test_download_api():
    """Test the Download API with various scenarios."""
    
    print("=== Testing Vnstock Download API ===\n")
    
    # Test 1: Basic CSV download
    print("1. Testing basic CSV download...")
    try:
        dl = Download(symbol="VCI", show_log=True)
        
        # Get data for last 30 days
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        csv_data = dl.to_csv(start_date=start_date, end_date=end_date)
        
        if csv_data and len(csv_data) > 0:
            print(f"✓ Successfully downloaded CSV data ({len(csv_data)} characters)")
            # Show first few lines
            lines = csv_data.split('\n')[:5]
            for line in lines:
                print(f"  {line}")
            if len(csv_data.split('\n')) > 5:
                print("  ...")
        else:
            print("✗ No data received")
            
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 2: Save to file
    print("2. Testing save to file...")
    try:
        dl = Download(symbol="FPT", show_log=True)
        
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        filepath = dl.save_csv(
            start_date=start_date,
            end_date=end_date,
            filename="FPT_test_data.csv"
        )
        
        if os.path.exists(filepath):
            print(f"✓ File saved successfully: {filepath}")
            file_size = os.path.getsize(filepath)
            print(f"  File size: {file_size} bytes")
        else:
            print("✗ File was not created")
            
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 3: Multiple symbols
    print("3. Testing multiple symbols download...")
    try:
        dl = Download(show_log=True)
        
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
        
        csv_dict = dl.download_multiple(
            symbols=["VCI", "FPT"],
            start_date=start_date,
            end_date=end_date
        )
        
        for symbol, csv_data in csv_dict.items():
            if csv_data:
                print(f"✓ {symbol}: {len(csv_data)} characters")
            else:
                print(f"✗ {symbol}: No data")
                
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 4: Validation tests
    print("4. Testing input validation...")
    try:
        dl = Download()
        
        # Test invalid date format
        try:
            dl.to_csv(symbol="VCI", start_date="2024/01/01", end_date="2024-01-31")
            print("✗ Should have failed with invalid date format")
        except (ValueError, Exception) as e:
            print(f"✓ Correctly caught invalid date format: {type(e).__name__}")
        
        # Test end date before start date
        try:
            dl.to_csv(symbol="VCI", start_date="2024-02-01", end_date="2024-01-31")
            print("✗ Should have failed with end date before start date")
        except (ValueError, Exception) as e:
            print(f"✓ Correctly caught invalid date range: {type(e).__name__}")
        
        # Test invalid symbol
        try:
            dl.to_csv(symbol="AB", start_date="2024-01-01", end_date="2024-01-31")
            print("✗ Should have failed with invalid symbol")
        except (ValueError, Exception) as e:
            print(f"✓ Correctly caught invalid symbol: {type(e).__name__}")
            
    except Exception as e:
        print(f"✗ Unexpected error in validation tests: {e}")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_download_api()
