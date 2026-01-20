#!/usr/bin/env python3
"""
Simple usage example for the Download API.
"""

from vnstock import Download

def main():
    """Demonstrate basic usage of the Download API."""
    
    print("=== Vnstock Download API Usage Example ===\n")
    
    # Example 1: Download single symbol data as CSV string
    print("1. Download single symbol data:")
    dl = Download(symbol="VCI", show_log=True)
    
    csv_data = dl.to_csv(start_date="2024-12-01", end_date="2024-12-05")
    print("CSV data received:")
    print(csv_data[:200] + "..." if len(csv_data) > 200 else csv_data)
    
    print("\n" + "="*50 + "\n")
    
    # Example 2: Save data to file
    print("2. Save data to file:")
    filepath = dl.save_csv(
        start_date="2024-12-01", 
        end_date="2024-12-05",
        filename="VCI_sample_data.csv"
    )
    print(f"Data saved to: {filepath}")
    
    print("\n" + "="*50 + "\n")
    
    # Example 3: Download multiple symbols
    print("3. Download multiple symbols:")
    csv_dict = dl.download_multiple(
        symbols=["VCI", "FPT"],
        start_date="2024-12-01",
        end_date="2024-12-05"
    )
    
    for symbol, data in csv_dict.items():
        if data:
            print(f"{symbol}: {len(data)} characters")
        else:
            print(f"{symbol}: No data")
    
    print("\n=== Example Complete ===")

if __name__ == "__main__":
    main()
