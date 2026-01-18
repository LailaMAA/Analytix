import sys
import os
from unittest.mock import MagicMock, patch

# Ensure correct path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from nlq_engine import sql_agent

def test_cache_and_logic():
    print("🧪 Testing Logic & Caching...")
    
    # Mock LLM
    mock_llm = MagicMock()
    # Setup returns for the chain:
    # 1. SQL Generation
    # 2. Visualization/Interpretation
    mock_llm.invoke.side_effect = [
        MagicMock(content="SELECT count(*) FROM DIM_VEHICLE"), 
        MagicMock(content='{"answer": "Il y a 10 véhicules.", "visualization": {"type": "none"}}')
    ]
    
    # Mock pandas execution to return dummy data so we don't need real DB connectivity or valid SQL for this logic test
    with patch('nlq_engine.sql_agent.get_llm', return_value=mock_llm), \
         patch('pandas.read_sql_query') as mock_pd:
        
        # Setup dummy DF
        import pandas as pd
        mock_pd.return_value = pd.DataFrame({"count": [10]})
        
        # First Call
        print("▶️ First Call (Should hit LLM)")
        res1 = sql_agent.query_enterprise_data("Test Question")
        print(f"Result 1: {res1}")
        
        # Second Call (Should hit Cache)
        print("▶️ Second Call (Should hit Cache)")
        res2 = sql_agent.query_enterprise_data("Test Question")
        
        if res1 == res2:
            print("✅ Cache Verification Passed")
        else:
            print("❌ Cache Verification Failed")
            
        # Verify LLM call count
        # Should be 2 (1 for SQL, 1 for Viz) for the FIRST call.
        # Second call hits cache, so 0 extra calls. Total 2.
        print(f"LLM Calls: {mock_llm.invoke.call_count}")
        if mock_llm.invoke.call_count == 2:
             print("✅ Call count optimization verified (2 calls)")
        else:
             print(f"❌ Unexpected call count: {mock_llm.invoke.call_count}")

if __name__ == "__main__":
    test_cache_and_logic()
