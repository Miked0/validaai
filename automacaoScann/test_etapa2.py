#!/usr/bin/env python3
"""Teste da ETAPA 2 usando as classes do package validaai-core"""
import sys
sys.path.insert(0, '/home/ubuntu/validaai/automacaoScann')

from src.validaai.reader import TestScriptReader
from src.validaai.parser_items import ItemParser
from src.validaai.payments import PaymentNormalizer
from src.validaai.validators import TestValidator
from src.validaai.api_sales import APISalesBuilder

# 1. Read roteiro (ETAPA 2)
print('1. Lendo roteiro ETAPA 2...')
reader = TestScriptReader('/home/ubuntu/validaai_test_data/doc_2e02e003bd9a_TEMPLATE_ROTEIRO_DE_TESTES_CB_1.0.xlsx')
reader.set_etapa('ETAPA 2')
raw_tests = reader.read_tests()
print(f'   Encontrados {len(raw_tests)} casos de teste')

# 2. Parse items
print('2. Parseando itens...')
item_parser = ItemParser()
parsed_tests = [item_parser.parse_items(t) for t in raw_tests]

# 3. Normalize payments
print('3. Normalizando pagamentos...')
payment_normalizer = PaymentNormalizer()
normalized_tests = [payment_normalizer.normalize_payment(t) for t in parsed_tests]

# 4. Business rule validation
print('4. Validando regras de negócio...')
validator = TestValidator(tolerance=0.01)
validated_tests = [validator.validate(t) for t in normalized_tests]

# 5. Load partner JSONs (audit)
print('5. Carregando JSONs do parceiro (auditoria)...')
api_builder = APISalesBuilder()

audit_file = '/home/ubuntu/validaai_test_data/doc_0f4caf1d2b79_export_tickets_audit_companyId201901_auditDate2026-06-22_87bda8_24-06-2026_15-38.xlsx'
partner_jsons = api_builder._load_partner_jsons(audit_file)
print(f'   JSONs de auditoria: {len(partner_jsons)}')

# 6. Validate each test against partner JSON
print('6. Validando contra JSON do parceiro...')
for t in validated_tests:
    test_cupom = str(t.get('cupom', '')).strip()
    if test_cupom and test_cupom in partner_jsons:
        partner_json = partner_jsons[test_cupom]
        t['sale_json'] = partner_json
        api_check = api_builder.validate_sale_json(partner_json)
        t['api_status'] = api_check.get('status', 'ERRO_JSON')
        t['api_alertas'] = api_check.get('alertas', []) or []
    else:
        t['sale_json'] = {}
        t['api_status'] = 'NOT_FOUND'
        t['api_alertas'] = [f'JSON nao encontrado para cupom {test_cupom}']

# 7. Print results
print()
print('=' * 80)
print('RESULTADOS DA VALIDACAO - ETAPA 2')
print('=' * 80)

status_counts = {}
for t in validated_tests:
    status = t.get('status_final', 'UNKNOWN')
    status_counts[status] = status_counts.get(status, 0) + 1

print(f'Resumo: {status_counts}')
print()

for t in validated_tests:
    teste_num = t.get('teste', 'N/A')
    status = t.get('status_final', 'N/A')
    motivo = t.get('motivo_status', '')[:100]
    api_status = t.get('api_status', 'N/A')
    api_alertas = '; '.join(t.get('api_alertas', []))[:100]
    cupom = t.get('cupom', 'N/A')
    tipo_promo = t.get('tipo_promo', '')[:40]
    itens = t.get('itens_da_venda', '')[:50]
    pagamento = t.get('pagamento', '')[:30]
    
    print(f'Teste {teste_num:>3} | Status: {status:>12} | API: {api_status:>10} | Cupom: {cupom}')
    print(f'         Promo: {tipo_promo}')
    print(f'         Itens: {itens}')
    print(f'         Pagto: {pagamento}')
    if motivo:
        print(f'         Motivo: {motivo}')
    if api_alertas:
        print(f'         API Alertas: {api_alertas}')
    print()