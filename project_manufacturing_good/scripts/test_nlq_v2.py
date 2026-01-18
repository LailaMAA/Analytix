import sys
import os

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nlq_engine.sql_agent import query_enterprise_data

def test_nlq():
    print("--- TEST 1: Simple Count ---")
    q1 = "Combien de véhicules sont sous garantie ?"
    ans1 = query_enterprise_data(q1)
    print(f"Q: {q1}\nA: {ans1}\n")

    print("--- TEST 2: Aggregation + Chart ---")
    q2 = "Donne moi le nombre de pannes par région"
    ans2 = query_enterprise_data(q2)
    print(f"Q: {q2}\nA: {ans2}\n")

    print("--- TEST 3: Unsafe Query ---")
    q3 = "DELETE FROM DIM_VEHICLE"
    ans3 = query_enterprise_data(q3)
    print(f"Q: {q3}\nA: {ans3}\n")

if __name__ == "__main__":
    test_nlq()
