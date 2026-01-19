import requests

BASE_URL = "http://127.0.0.1:8000"

def test_auth():
    print("Testing Login...")
    login_data = {
        "username": "admin@analytixcare.com",
        "password": "admin123"
    }
    response = requests.post(f"{BASE_URL}/api/auth/token", data=login_data)
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"✅ Login successful! Token: {token[:20]}...")
        
        print("Testing Profile Retrieval...")
        headers = {"Authorization": f"Bearer {token}"}
        profile_res = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        if profile_res.status_code == 200:
            print(f"✅ Profile retrieved: {profile_res.json()['full_name']}")
        else:
            print(f"❌ Profile retrieval failed: {profile_res.status_code}")
            
        print("Testing Unauthorized access...")
        unauth_res = requests.get(f"{BASE_URL}/api/kpi/stats")
        if unauth_res.status_code == 401:
            print("✅ Unauthorized access correctly blocked (401).")
        else:
            print(f"❌ Security failure: {unauth_res.status_code}")
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_auth()
