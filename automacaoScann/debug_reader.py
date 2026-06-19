#!/usr/bin/env python3
"""
Debug script to see what the reader is actually returning
"""

import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

from reader import TestScriptReader

def debug_reader():
    """Debug what the reader returns"""
    print("=== Debugging Reader Output ===")
    
    # Define paths
    base_dir = Path(__file__).parent
    input_dir = base_dir / "input"
    input_csv = input_dir / "roteiro_testes.csv"
    
    if not input_csv.exists():
        print(f"ERROR: CSV file not found at {input_csv}")
        return False
        
    print(f"Using CSV file: {input_csv}")
    
    try:
        # Read the test script
        print("\n1. Reading test script...")
        reader = TestScriptReader(str(input_csv))
        raw_tests = reader.read_tests()
        print(f"   Found {len(raw_tests)} raw test cases")
        
        # Show ALL raw tests with all fields
        for i, test in enumerate(raw_tests):
            print(f"\n   Raw test {i+1}:")
            for key, value in test.items():
                print(f"     {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = debug_reader()
    sys.exit(0 if success else 1)