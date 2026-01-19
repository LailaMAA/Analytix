import requests
import time

BASE_URL = "http://127.0.0.1:8000"

def test_briefing_cache():
    print("🔹 Connexion...")
    login_data = {
        "username": "admin@analytixcare.com",
        "password": "admin123"
    }
    
    try:
        # 1. Login
        response = requests.post(f"{BASE_URL}/api/auth/token", data=login_data)
        if response.status_code != 200:
            print(f"❌ Echec Login: {response.status_code}")
            return
            
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. First Call (Should compute or fetch from cache if already there)
        print("\n🔹 Appel 1: Génération/Récupération du Briefing...")
        start_time = time.time()
        res1 = requests.get(f"{BASE_URL}/api/reports/daily-briefing", headers=headers)
        duration1 = time.time() - start_time
        
        if res1.status_code == 200:
            print(f"✅ Reçu (Taille: {len(res1.text)} chars)")
            print(f"⏱️ Durée appel 1: {duration1:.2f}s")
        else:
            print(f"❌ Erreur Appel 1: {res1.status_code}")
            print(res1.text)

        # 3. Second Call (Should be instant from cache)
        print("\n🔹 Appel 2: Test du Cache...")
        start_time = time.time()
        res2 = requests.get(f"{BASE_URL}/api/reports/daily-briefing", headers=headers)
        duration2 = time.time() - start_time
        
        if res2.status_code == 200:
            print(f"✅ Reçu (Taille: {len(res2.text)} chars)")
            print(f"⏱️ Durée appel 2: {duration2:.2f}s")
            
            if duration2 < 0.5:
                print("\n✨ SUCCÈS : Le cache fonctionne (réponse instantanée) !")
            else:
                print("\n⚠️ ATTENTION : La réponse semble lente pour du cache.")
        else:
            print(f"❌ Erreur Appel 2: {res2.status_code}")

    except Exception as e:
        print(f"❌ Erreur de script : {e}")

if __name__ == "__main__":
    test_briefing_cache()
