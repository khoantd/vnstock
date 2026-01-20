#!/usr/bin/env python3
"""
Test script for the REST API endpoints.
"""

import requests
import json
import time
import os

# API base URL
BASE_URL = "http://localhost:8001"

def test_api():
    """Test all API endpoints."""
    
    print("=== Testing Vnstock REST API ===\n")
    
    # Test user credentials
    test_user = {
        "username": "testuser_" + str(int(time.time())),
        "email": f"test_{int(time.time())}@example.com",
        "password": "securepassword123"
    }
    
    # 1. Register user
    print("1. Testing user registration...")
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=test_user)
        if response.status_code == 200:
            print("✓ User registered successfully")
            print(f"  Response: {response.json()}")
        else:
            print(f"✗ Registration failed: {response.status_code}")
            print(f"  Response: {response.text}")
        print()
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to API. Make sure it's running on localhost:8000")
        return
    
    # 2. Login
    print("2. Testing user login...")
    try:
        login_data = {
            "username": test_user["username"],
            "password": test_user["password"]
        }
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            token_data = response.json()
            token = token_data["access_token"]
            print("✓ Login successful")
            print(f"  Token type: {token_data['token_type']}")
        else:
            print(f"✗ Login failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return
        print()
    except Exception as e:
        print(f"✗ Login error: {e}")
        return
    
    # Set up headers for authenticated requests
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 3. Get user info
    print("3. Testing user info endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        if response.status_code == 200:
            user_info = response.json()
            print("✓ User info retrieved successfully")
            print(f"  Username: {user_info['username']}")
            print(f"  Email: {user_info['email']}")
        else:
            print(f"✗ Failed to get user info: {response.status_code}")
        print()
    except Exception as e:
        print(f"✗ User info error: {e}")
    
    # 4. Health check
    print("4. Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health")
        if response.status_code == 200:
            health = response.json()
            print("✓ Health check successful")
            print(f"  Status: {health['status']}")
            print(f"  Version: {health['version']}")
        else:
            print(f"✗ Health check failed: {response.status_code}")
        print()
    except Exception as e:
        print(f"✗ Health check error: {e}")
    
    # 5. Get available symbols
    print("5. Testing symbols endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/symbols", headers=headers)
        if response.status_code == 200:
            symbols_data = response.json()
            print("✓ Symbols retrieved successfully")
            print(f"  Total symbols: {symbols_data['total']}")
            print(f"  Sample symbols: {symbols_data['symbols'][:5]}")
        else:
            print(f"✗ Failed to get symbols: {response.status_code}")
        print()
    except Exception as e:
        print(f"✗ Symbols error: {e}")
    
    # 6. Download CSV as text
    print("6. Testing CSV download (text)...")
    try:
        download_data = {
            "symbol": "VCI",
            "start_date": "2024-12-01",
            "end_date": "2024-12-05",
            "source": "vci",
            "interval": "D"
        }
        response = requests.post(f"{BASE_URL}/api/v1/download/csv-text", 
                               json=download_data, headers=headers)
        if response.status_code == 200:
            csv_response = response.json()
            print("✓ CSV data retrieved successfully")
            print(f"  Symbol: {csv_response['symbol']}")
            print(f"  Data size: {csv_response['data_size']} characters")
            print(f"  Sample data: {csv_response['csv_data'][:100]}...")
        else:
            print(f"✗ CSV download failed: {response.status_code}")
            print(f"  Response: {response.text}")
        print()
    except Exception as e:
        print(f"✗ CSV download error: {e}")
    
    # 7. Download CSV as file
    print("7. Testing CSV download (file)...")
    try:
        download_data = {
            "symbol": "FPT",
            "start_date": "2024-12-01",
            "end_date": "2024-12-05",
            "source": "vci",
            "interval": "D"
        }
        response = requests.post(f"{BASE_URL}/api/v1/download/csv", 
                               json=download_data, headers=headers)
        if response.status_code == 200:
            filename = f"FPT_test_{int(time.time())}.csv"
            with open(filename, "wb") as f:
                f.write(response.content)
            file_size = os.path.getsize(filename)
            print(f"✓ CSV file downloaded successfully")
            print(f"  Filename: {filename}")
            print(f"  File size: {file_size} bytes")
        else:
            print(f"✗ CSV file download failed: {response.status_code}")
            print(f"  Response: {response.text}")
        print()
    except Exception as e:
        print(f"✗ CSV file download error: {e}")
    
    # 8. Download multiple symbols
    print("8. Testing multiple symbols download...")
    try:
        multiple_data = {
            "symbols": ["VCI", "FPT"],
            "start_date": "2024-12-01",
            "end_date": "2024-12-05",
            "source": "vci",
            "interval": "D",
            "combine": False
        }
        response = requests.post(f"{BASE_URL}/api/v1/download/multiple", 
                               json=multiple_data, headers=headers)
        if response.status_code == 200:
            multi_response = response.json()
            print("✓ Multiple symbols download successful")
            print(f"  Total symbols: {multi_response['total_symbols']}")
            for symbol, csv_data in multi_response['csv_data'].items():
                if csv_data:
                    print(f"  {symbol}: {len(csv_data)} characters")
                else:
                    print(f"  {symbol}: No data")
        else:
            print(f"✗ Multiple symbols download failed: {response.status_code}")
            print(f"  Response: {response.text}")
        print()
    except Exception as e:
        print(f"✗ Multiple symbols download error: {e}")
    
    # 9. Test validation errors
    print("9. Testing input validation...")
    try:
        invalid_data = {
            "symbol": "AB",  # Invalid symbol (too short)
            "start_date": "2024/12/01",  # Invalid date format
            "end_date": "2024-12-05",
            "source": "vci",
            "interval": "D"
        }
        response = requests.post(f"{BASE_URL}/api/v1/download/csv-text", 
                               json=invalid_data, headers=headers)
        if response.status_code == 400:
            print("✓ Validation error caught correctly")
            print(f"  Error: {response.json()['detail']}")
        else:
            print(f"✗ Expected validation error, got: {response.status_code}")
        print()
    except Exception as e:
        print(f"✗ Validation test error: {e}")
    
    # 10. Test unauthorized access
    print("10. Testing unauthorized access...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/symbols")
        if response.status_code == 401:
            print("✓ Unauthorized access correctly blocked")
        else:
            print(f"✗ Expected 401, got: {response.status_code}")
        print()
    except Exception as e:
        print(f"✗ Unauthorized test error: {e}")
    
    print("=== API Test Complete ===")

if __name__ == "__main__":
    test_api()
