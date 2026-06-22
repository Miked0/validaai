import sys
sys.path.insert(0, 'C:/Users/Mike/validaai/automacaoScann/src')
from validaai import TestScriptReader, ItemParser, PaymentNormalizer, TestValidator, APISalesBuilder
import json
import pandas as pd

# 1. Read template
reader = TestScriptReader('C:/Users/Mike/validaai/automacaoScann/biblioteca/TEMPLATE_COM_BIN_NOVO.xlsx')
reader.set_etapa('ETAPA 1')
tests = reader.read_tests()
print(f'Total testes lidos: {len(tests)}')

# 2. Load partner JSONs from audit file
audit_file = 'C:/Users/Mike/validaai/automacaoScann/biblioteca/export_tickets_audit.xlsx'
xls = pd.ExcelFile(audit_file)
partner_jsons = {}
for sheet_name in xls.sheet_names:
    df = pd.read_excel(audit_file, sheet_name=sheet_name, dtype=str)
    if 'Número cupom' in df.columns and 'Request' in df.columns:
        for _, row in df.iterrows():
            cupom = str(row.get('Número cupom', '')).strip()
            req = str(row.get('Request', '')).strip()
            if cupom and cupom.lower() not in ['nan', 'none', ''] and req and req not in ['nan', 'None', '']:
                try:
                    partner_jsons[cupom] = json.loads(req)
                except:
                    pass

print(f'Partner JSONs loaded: {len(partner_jsons)}')
print(f'Cupom keys: {sorted(partner_jsons.keys())[:10]}...')

# 3. Process each test with full validation
parser = ItemParser()
pay_norm = PaymentNormalizer()
validator = TestValidator(tolerance=0.01, partner_jsons=partner_jsons)
api_builder = APISalesBuilder()

results = {}
for test_dict in tests:
    test_dict = parser.parse_items(test_dict)
    test_dict = pay_norm.normalize_payment(test_dict)
    sale_json = api_builder.build_sale_json(
        teste=test_dict['teste'],
        itens_da_venda=test_dict['itens_da_venda'],
        pagamento=test_dict['pagamento'],
        subtotal=test_dict['subtotal_esperado'],
        desconto=test_dict['desconto_esperado'],
        total=test_dict['total_esperado'],
        observacoes=test_dict['observacoes'],
        numero_cupom=test_dict.get('cupom', ''),
        pagamentos=test_dict.get('pagamentos', [])
    )
    test_dict['sale_json'] = sale_json
    
    validated = validator.validate(test_dict)
    results[test_dict['teste']] = {
        'status': validated['status_final'],
        'motivo': validated['motivo_status'],
    }

# Summary
total_counts = {}
for r in results.values():
    s = r['status']
    total_counts[s] = total_counts.get(s, 0) + 1

print('\nTOTAL GERAL (SDD workflow):')
for status, count in sorted(total_counts.items()):
    print(f'  {status}: {count}')

for tid in sorted(results.keys()):
    r = results[tid]
    print(f'  Teste {tid:2d}: {r["status"]:15s} - {r["motivo"][:80]}')