#!/usr/bin/env python3
"""
Main script for QA Roteiro Automation MVP
Orchestrates the reading, parsing, validation, and export of test script data.
"""

from __future__ import annotations

import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent / "src"))
sys.path.append(str(Path(__file__).parent.parent))

from validaai.reader import TestScriptReader
from validaai.parser_items import ItemParser
from validaai.payments import PaymentNormalizer
from validaai.validators import TestValidator
from validaai.exporters import ResultExporter
from validaai.api_sales import APISalesBuilder


def main() -> int:
    print("=== QA Roteiro Automation MVP ===")
    print("Starting test script validation process...\n")

    base_dir = Path(__file__).parent.parent
    input_dir = base_dir / "input"
    output_dir = base_dir / "output"

    output_dir.mkdir(exist_ok=True)

    input_excel = input_dir / "roteiro_testes.xlsx"
    input_csv = input_dir / "roteiro_testes.csv"

    input_file = input_excel if input_excel.exists() else input_csv
    if not input_file.exists():
        print("ERROR: No input file found. Please place 'roteiro_testes.xlsx' or 'roteiro_testes.csv' in the input directory.")
        return 1

    print(f"Using input file: {input_file}")

    try:
        print("\n1. Reading test script...")
        reader = TestScriptReader(str(input_file))
        raw_tests = reader.read_tests()
        print(f"   Found {len(raw_tests)} raw test cases")

        print("\n2. Parsing items...")
        item_parser = ItemParser()
        parsed_tests = [item_parser.parse_items(test) for test in raw_tests]
        print(f"   Parsed items for {len(parsed_tests)} test cases")

        print("\n3. Normalizing payments...")
        payment_normalizer = PaymentNormalizer()
        normalized_tests = [payment_normalizer.normalize_payment(test) for test in parsed_tests]
        print(f"   Normalized payments for {len(normalized_tests)} test cases")

        print("\n4. Validating tests...")
        validator = TestValidator(tolerance=0.01)
        validated_tests = [validator.validate(test) for test in normalized_tests]
        print(f"   Validated {len(validated_tests)} test cases")

        print("\n5. Building and validating API sale JSONs...")
        api_builder = APISalesBuilder()
        for test in validated_tests:
            sale_json = api_builder.build_sale_json(
                teste=test.get("teste"),
                itens_da_venda=test.get("itens_da_venda", ""),
                pagamento=test.get("pagamento", ""),
                subtotal=test.get("subtotal_esperado", test.get("subtotal", "")),
                desconto=test.get("desconto_esperado", test.get("desconto", "0")),
                total=test.get("total_esperado", test.get("total", "")),
                observacoes=test.get("observacoes", ""),
                numero_cupom=test.get("cupom", ""),
                tipo_promo=test.get("tipo_promo", ""),
            )
            test["sale_json"] = sale_json

            api_check = api_builder.validate_sale_json(sale_json or {})
            test["api_status"] = api_check.get("status", "ERRO_JSON")
            test["api_alertas"] = api_check.get("alertas", []) or []

        print("\n6. Exporting results...")
        exporter = ResultExporter()
        output_file = output_dir / "validacao_resultado.xlsx"
        exporter.export(validated_tests, str(output_file))
        print(f"   Results exported to: {output_file}")

        def _sanitize(obj):
            from decimal import Decimal as _Decimal
            if isinstance(obj, dict):
                return {k: _sanitize(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [_sanitize(v) for v in obj]
            if isinstance(obj, _Decimal):
                return float(obj)
            if obj is None or isinstance(obj, (bool, int, float, str)):
                return obj
            return str(obj)

        audit_path = output_dir / f"audit_{__import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        payload = {
            "generated_at": datetime.now().isoformat(),
            "total": len(validated_tests),
            "results": _sanitize(validated_tests),
        }
        with open(audit_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f"   Audit JSON exported to: {audit_path}")

        print("\n=== VALIDATION SUMMARY ===")
        status_counts = {}
        for test in validated_tests:
            status = test.get("status_final", "UNKNOWN")
            status_counts[status] = status_counts.get(status, 0) + 1

        for status, count in status_counts.items():
            print(f"{status}: {count}")

        print(f"\nTotal tests processed: {len(validated_tests)}")
        print("Process completed successfully!")
        return 0

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
