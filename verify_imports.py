
import sys
import os
sys.path.append(os.path.join(os.getcwd(), "src"))

try:
    from agents.context import ContextAgent
    from agents.abstract import AbstractAgent
    from agents.dialog import DialogAgent
    # Check if old names are gone (this should fail if I import them? no, just checking new ones work)
    
    print("Imports of new agent names successful!")
except ImportError as e:
    print(f"Import failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"An error occurred: {e}")
    sys.exit(1)
