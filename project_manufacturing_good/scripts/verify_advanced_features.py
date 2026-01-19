import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_inventory_forecast():
    print("Testing /api/inventory/forecast...")
    try:
        response = requests.get(f"{BASE_URL}/api/inventory/forecast")
        if response.status_code == 200:
            data = response.json()
            print(f"Success! Found {len(data)} forecasted parts.")
            print(json.dumps(data[:2], indent=2))
        else:
            print(f"Failed with status code: {response.status_code}")
    except Exception as e:
        print(f"Error connecting to server: {e}")

def test_financial_kpi():
    print("\nTesting /api/kpi/financial...")
    try:
        response = requests.get(f"{BASE_URL}/api/kpi/financial")
        if response.status_code == 200:
            data = response.json()
            print("Success! Financial KPI data:")
            print(json.dumps(data, indent=2))
        else:
            print(f"Failed with status code: {response.status_code}")
    except Exception as e:
        print(f"Error connecting to server: {e}")

if __name__ == "__main__":
    # Note: Server must be running for this to work
    test_inventory_forecast()
    test_financial_kpi()
