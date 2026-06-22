#!/usr/bin/env python3
"""
Run ValidaAI validation against 'teste 2' template + 30 audit JSONs
"""

import json
import pandas as pd
from src.validaai.reader import TestScriptReader
from src.validaai.parser_items import ItemParser
from src.validaai.payments import PaymentNormalizer
from src.validaai.api_sales import APISalesBuilder
from src.validaai.validators import TestValidator

# 1. Load audit JSONs
print("=" * 60)
print("LOADING AUDIT JSONS")
print("=" * 60)

audit_file = 'biblioteca/teste 2/export_tickets_audit_companyId=74866_auditDate=2026-06-11_a99383_18-06-2026_00-00.xlsx'
df_audit = pd.read_excel(audit_file, header=None)

partner_jsons = {}
for i in range(1, len(df_audit)):
    row = df_audit.iloc[i]
    cupom = str(row[7]).strip()
    metodo = str(row[5]).strip()
    request_json_str = str(row[18]).strip()
    
    if cupom and cupom.lower() not in ['nan', 'none', ''] and request_json_str and request_json_str not in ['nan', '{}', '']:
        if metodo == 'agregarMovimiento':
            try:
                parsed = json.loads(request_json_str)
                partner_jsons[cupom] = parsed
                print(f"  Cupom {cupom}: JSON loaded OK")
            except Exception as e:
                print(f"  Cupom {cupom}: ERROR parsing JSON: {e}")

print(f"\nTotal partner JSONs loaded: {len(partner_jsons)}")

# 2. Load template tests (ETAPA 1)
print("\n" + "=" * 60)
print("LOADING TEMPLATE TESTS (ETAPA 1)")
print("=" * 60)

reader = TestScriptReader('biblioteca/teste 2/TEMPLATE_COM_BIN_NOVO (2).xlsx')
reader.set_etapa('ETAPA 1')
tests = reader.read_tests()
print(f"Total tests read: {len(tests)}")

# 3. Process each test through the pipeline
print("\n" + "=" * 60)
print("PROCESSING TESTS THROUGH PIPELINE")
print("=" * 60)

item_parser = ItemParser()
payment_normalizer = PaymentNormalizer()
api_builder = APISalesBuilder()
validator = TestValidator(tolerance=0.01, partner_jsons=partner_jsons)

results = []

for test in tests:
    teste_num = test.get('teste')
    itens_raw = test.get('itens_da_venda', '')
    pagamento_raw = test.get('pagamento', '')
    observacoes = test.get('observacoes', '')
    observacao_parceiro = test.get('observacao_parceiro', '')
    subtotal = test.get('subtotal_esperado', '')
    desconto = test.get('desconto_esperado', '')
    total = test.get('total_esperado', '')
    cupom = test.get('cupom', '')
    sat = test.get('sat', '')
    ecf = test.get('ecf', '')
    nfce = test.get('nfce', '')
    
    print(f"\n--- Teste {teste_num} ---")
    print(f"  Itens: {itens_raw[:80]}")
    print(f"  Pagamento: {pagamento_raw}")
    print(f"  Obs: {observacoes}")
    print(f"  Cupom: {cupom}, SAT: {sat}, ECF: {ecf}, NFCE: {nfce}")
    print(f"  Sub: {subtotal}, Desc: {desconto}, Total: {total}")
    
    # Parse items
    test_with_items = item_parser.parse_items(test)
    
    # Normalize payment
    test_with_payments = payment_normalizer.normalize_payment(test_with_items)
    
    # Add partner JSONs and observations
    test_with_payments['partner_jsons'] = partner_jsons
    test_with_payments['observacao_parceiro'] = observacao_parceiro
    test_with_payments['pagamento_raw'] = pagamento_raw
    
    # Build sale_json
    sale_json = api_builder.build_sale_json(
        teste=teste_num,
        itens_da_venda=itens_raw,
        pagamento=pagamento_raw,
        subtotal=subtotal,
        desconto=desconto,
        total=total,
        observacoes=observacoes,
        numero_cupom=cupom,
        tipo_promo=test.get('tipo_promo', ''),
        pagamentos=test_with_payments.get('pagamentos', [])
    )
    test_with_payments['sale_json'] = sale_json
    
    # Run LEGACY validation (matches gui_app_standalone.py / run_full_validation.py)
    legacy_result = validator.validate_legacy(test_with_payments)
    
    # Run SDD validation (new 4-stage pipeline)
    sdd_result = validator.validate(test_with_payments)
    
    print(f"  LEGACY: {legacy_result['status_final']} - {legacy_result['motivo_status'][:80]}")
    print(f"  SDD:    {sdd_result['status_final']} - {sdd_result['motivo_status'][:80]}")
    
    results.append({
        'teste': teste_num,
        'cupom': cupom,
        'itens': itens_raw[:100],
        'pagamento': pagamento_raw,
        'obs': observacoes[:60],
        'legacy_status': legacy_result['status_final'],
        'legacy_motivo': legacy_result['motivo_status'],
        'sdd_status': sdd_result['status_final'],
        'sdd_motivo': sdd_result['motivo_status'],
        'sdd_etapa1': sdd_result.get('etapa1_itens', {}),
        'sdd_etapa2': sdd_result.get('etapa2_pagamento', {}),
        'sdd_etapa3': sdd_result.get('etapa3_valores', {}),
        'sdd_etapa4': sdd_result.get('etapa4_observacoes', {}),
    })

# 4. Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)

legacy_counts = {}
sdd_counts = {}
for r in results:
    legacy_counts[r['legacy_status']] = legacy_counts.get(r['legacy_status'], 0) + 1
    sdd_counts[r['sdd_status']] = sdd_counts.get(r['sdd_status'], 0) + 1

print(f"\nLEGACY distribution: {legacy_counts}")
print(f"SDD distribution:    {sdd_counts}")

print("\nDetailed results:")
for r in results:
    match = "✓" if r['legacy_status'] == r['sdd_status'] else "✗"
    print(f"  Teste {r['teste']:>3}: Legacy={r['legacy_status']:15} SDD={r['sdd_status']:15} {match}")

# Save detailed results
with open('output/teste2_validation_results.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print("\nResults saved to output/teste2_validation_results.json")
