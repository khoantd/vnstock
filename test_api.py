#!/usr/bin/env python3
"""
Test script for vnstock comprehensive API endpoints
"""

import requests
import json
from datetime import datetime

# API base URL (assuming running on localhost:8001)
BASE_URL = "http://localhost:8001"

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health")
        print(f"Health check: {response.status_code}")
        print(f"Response: {response.json()}")
        return True
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def register_and_login():
    """Register a test user and get JWT token"""
    # Register user
    register_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
        print(f"Register: {response.status_code}")
    except Exception as e:
        print(f"Register failed (might already exist): {e}")
    
    # Login and get token
    login_data = {
        "username": "testuser",
        "password": "testpass123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            token_data = response.json()
            return token_data["access_token"]
        else:
            print(f"Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Login failed: {e}")
        return None

def test_company_endpoints(token):
    """Test company information endpoints"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test company overview
    company_data = {
        "symbol": "VCB",
        "source": "vci"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/company/overview", 
                                json=company_data, headers=headers)
        print(f"Company overview: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Symbol: {data.get('symbol')}")
            print(f"  Data keys: {list(data.get('data', {}).keys()) if isinstance(data.get('data'), dict) else 'Not a dict'}")
        else:
            print(f"  Error: {response.text}")
    except Exception as e:
        print(f"Company overview failed: {e}")

def test_financial_endpoints(token):
    """Test financial information endpoints"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test financial ratios
    financial_data = {
        "symbol": "VCB",
        "source": "vci",
        "period": "quarter"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/financial/ratios", 
                                json=financial_data, headers=headers)
        print(f"Financial ratios: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Symbol: {data.get('symbol')}")
            print(f"  Period: {data.get('period')}")
        else:
            print(f"  Error: {response.text}")
    except Exception as e:
        print(f"Financial ratios failed: {e}")

def test_trading_endpoints(token):
    """Test trading data endpoints"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test price board
    trading_data = {
        "symbols_list": ["VCB", "FPT", "HPG"],
        "source": "vci"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/trading/price-board", 
                                json=trading_data, headers=headers)
        print(f"Price board: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Symbols: {data.get('symbols')}")
        else:
            print(f"  Error: {response.text}")
    except Exception as e:
        print(f"Price board failed: {e}")

def main():
    """Main test function"""
    print("=== Vnstock Comprehensive API Test ===")
    print(f"Timestamp: {datetime.now()}")
    print()
    
    # Test health
    if not test_health():
        print("API server not running. Please start the API server first.")
        print("Run: python -m vnstock.api.rest_api")
        return
    
    print()
    
    # Get authentication token
    print("=== Authentication ===")
    token = register_and_login()
    if not token:
        print("Failed to get authentication token")
        return
    
    print(f"Token obtained: {token[:20]}...")
    print()
    
    # Test endpoints
    print("=== Testing Company Endpoints ===")
    test_company_endpoints(token)
    print()
    
    print("=== Testing Financial Endpoints ===")
    test_financial_endpoints(token)
    print()
    
    print("=== Testing Trading Endpoints ===")
    test_trading_endpoints(token)
    print()
    
    print("=== Test Complete ===")

if __name__ == "__main__":
    main()
