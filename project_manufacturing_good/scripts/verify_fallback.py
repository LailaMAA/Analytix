import sys
import os
from unittest.mock import MagicMock, patch

# Ensure correct path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from nlq_engine import sql_agent

def test_fallback():
    print("🧪 Testing Fallback Mode...")
    
    # Mock LLM to throw an exception
    mock_llm = MagicMock()
    mock_llm.invoke.side_effect = Exception("RateLimitReached")
    
    with patch('nlq_engine.sql_agent.get_llm', return_value=mock_llm):
        
        # Test 1: Pannes (Should return Bar Chart)
        print("▶️ Test 'Pannes' (Should trigger Fallback Bar Chart)")
        res1 = sql_agent.query_enterprise_data("Quelles sont les pannes ?")
        viz1 = res1.get("visualization", {})
        print(f"Viz Type: {viz1.get('type')}")
        if viz1.get("type") == "bar":
            print("✅ Fallback 'Pannes' Passed")
        else:
            print("❌ Fallback 'Pannes' Failed")

        # Test 2: Coût (Should return Doughnut Chart)
        print("▶️ Test 'Coût' (Should trigger Fallback Doughnut Chart)")
        res2 = sql_agent.query_enterprise_data("Montre les coûts par région")
        viz2 = res2.get("visualization", {})
        print(f"Viz Type: {viz2.get('type')}")
        if viz2.get("type") == "doughnut":
            print("✅ Fallback 'Coût' Passed")
        else:
            print("❌ Fallback 'Coût' Failed")

if __name__ == "__main__":
    test_fallback()
