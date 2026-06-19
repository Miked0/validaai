#!/usr/bin/env python3
"""
Test script to validate the core functionality without pandas
"""

import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

from reader import TestScriptReader
from parser_items import ItemParser
from payments import PaymentNormalizer
from validators import TestValidator

def test_with_csv():
    """Test the core functionality with the CSV file"""
    print("=== Testing Core Functionality ===")
    
    # Define paths
    base_dir = Path(__file__).parent
    input_dir = base_dir / "input"
    input_csv = input_dir / "roteiro_testes.csv"
    
    if not input_csv.exists():
        print(f"ERROR: CSV file not found at {input_csv}")
        return False
        
    print(f"Using CSV file: {input_csv}")
    
    try:
        # Step 1: Read the test script
        print("\n1. Reading test script...")
        reader = TestScriptReader(str(input_csv))
        raw_tests = reader.read_tests()
        print(f"   Found {len(raw_tests)} raw test cases")
        
        # Show first few raw tests for debugging
        for i, test in enumerate(raw_tests[:3]):
            print(f"   Raw test {i+1}: {test}")
        
        # Step 2: Parse items
        print("\n2. Parsing items...")
        item_parser = ItemParser()
        parsed_tests = []
        for test in raw_tests:
            parsed_test = item_parser.parse_items(test)
            parsed_tests.append(parsed_test)
        print(f"   Parsed items for {len(parsed_tests)} test cases")
        
        # Show first few parsed tests
        for i, test in enumerate(parsed_tests[:3]):
            print(f"   Parsed test {i+1}: teste={test.get('teste')}, itens={test.get('itens_parseados')}")
        
        # Step 3: Normalize payments
        print("\n3. Normalizing payments...")
        payment_normalizer = PaymentNormalizer()
        normalized_tests = []
        for test in parsed_tests:
            normalized_test = payment_normalizer.normalize_payment(test)
            normalized_tests.append(normalized_test)
        print(f"   Normalized payments for {len(normalized_tests)} test cases")
        
        # Show first few normalized tests
        for i, test in enumerate(normalized_tests[:3]):
            print(f"   Normalized test {i+1}: pagamento={test.get('pagamento_raw')} -> {test.get('pagamento_normalizado')} (cod={test.get('codigo_tipo_pago')})")
        
        # Step 4: Validate tests
        print("\n4. Validating tests...")
        validator = TestValidator(tolerance=0.01)
        validated_tests = []
        for test in normalized_tests:
            validated_test = validator.validate(test)
            validated_tests.append(validated_test)
        print(f"   Validated {len(validated_tests)} test cases")
        
        # Show validation results
        print("\n=== VALIDATION RESULTS ===")
        status_counts = {}
        for test in validated_tests:
            status = test.get('status_final', 'UNKNOWN')
            status_counts[status] = status_counts.get(status, 0) + 1
            if status != 'OK':
                print(f"   Teste {test.get('teste')}: {status} - {test.get('motivo_status')}")
        
        for status, count in status_counts.items():
            print(f"{status}: {count}")
        
        print(f"\nTotal tests processed: {len(validated_tests)}")
        
        # Return True if we got here successfully
        return True
        
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_with_csv()
    sys.exit(0 if success else 1)