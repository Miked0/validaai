#!/usr/bin/env python3
"""Teste da ETAPA 2 usando as classes do package validaai-core - com export_movimentos"""
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

# 5. Load partner JSONs (audit + movimentos)
print('5. Carregando JSONs do parceiro (auditoria + movimentos)...')
api_builder = APISalesBuilder()

# NOVO ARQUIVO DE AUDITORIA ATUALIZADO (tem todos os tickets)
audit_file = '/home/ubuntu/.hermes/cache/documents/doc_dc51504a8b81_export_tickets_audit_companyId201901_auditDate2026-06-22_ec1c34_25-06-2026_07-44.xlsx'
partner_jsons = api_builder._load_partner_jsons(audit_file)
print(f'   JSONs de auditoria: {len(partner_jsons)}')
print(f'   Testes com JSON do parceiro: {sorted(partner_jsons.keys())}')
# 5b. Load export_movimentos and build JSONs per cupom
print('5b. Carregando export_movimentos e construindo JSONs por cupom...')
movimentos_file = '/home/ubuntu/validaai_test_data/doc_c0c58b0e0c99_export_tickets_companyId201901_from2026-06-22_to2026-06-22_7892db_24-06-2026_15-38.xlsx'
movimentos_jsons = api_builder._load_partner_jsons(movimentos_file) if False else {}

# Since export_movimentos has different structure, build JSONs manually
import pandas as pd
df = pd.read_excel(movimentos_file, sheet_name='TICKETS', dtype=str)
print(f'   Linhas no movimentos: {len(df)}')

# Group by cupom (Número) and build JSON
movimentos_jsons = {}
for cupom, group in df.groupby('Número'):
    # Build movimiento JSON from group rows
    movimiento = {
        'fecha': group.iloc[0]['Data'],
        'numero': cupom,
        'descuentoTotal': 0.0,
        'recargoTotal': 0.0,
        'codigoMoneda': '986',
        'cotizacion': 1.00,
        'total': float(group.iloc[0]['Total']) if group.iloc[0]['Total'] else 0.0,
        'cancelacion': cupom.startswith('-'),
        'documentoCliente': '',
        'codigoCanalVenta': 1,
        'descripcionCanalVenta': 'VENDA NA LOJA',
        'idCliente': '',
        'referencia': '',
        'detalles': [],
        'pagos': [],
        'deliveryPostalCode': '',
    }
    
    # Build detalles from items
    for _, row in group.iterrows():
        detalle = {
            'codigoArticulo': str(row['Código do produto']),
            'codigoBarras': str(row['Código de barras']),
            'descripcionArticulo': str(row['Descrição do produto']),
            'cantidad': float(row['Quantidade']) if row['Quantidade'] else 1.0,
            'importeUnitario': float(row['Importe unitário']) if row['Importe unitário'] else 0.0,
            'importe': float(row['Importe']) if row['Importe'] else 0.0,
            'impuesto': 0.0,
            'descuento': float(row['Desconto']) if row['Desconto'] else 0.0,
            'recargo': float(row['Sobretaxa']) if row['Sobretaxa'] else 0.0,
            'datosExtra': '{}',
        }
        movimiento['detalles'].append(detalle)
    
    # Build pagos - need to infer from roteiro or use single payment
    # For now, leave empty - will be validated against roteiro
    
    # Apply promotions from this group
    promocoes = group['ID Promoção'].dropna().unique()
    if len(promocoes) > 0:
        movimiento['promociones'] = []
        for promo_id in promocoes:
            promo_rows = group[group['ID Promoção'] == promo_id]
            desc_promo = promo_rows['Desconto promoção'].sum()
            if desc_promo:
                # Handle format like '5.690.71' -> 5690.71
                desc_str = str(desc_promo).replace('.', '').replace(',', '.')
                desc_val = float(desc_str) if desc_str else 0.0
                movimiento['promociones'].append({
                    'idPromocion': str(promo_id),
                    'descuento': desc_val,
                })
    
    # Calculate descuentoTotal from items
    desc_total = sum(float(d.get('descuento', 0) or 0) for d in movimiento['detalles'])
    movimiento['descuentoTotal'] = round(desc_total, 2)
    
    # Update total based on items
    total_items = sum(float(d.get('importe', 0) or 0) for d in movimiento['detalles'])
    if total_items > 0:
        movimiento['total'] = round(total_items, 2)
    
    # Wrap in 'movimiento' key like API format
    movimentos_jsons[cupom] = {'movimiento': movimiento}

print(f'   JSONs de movimentos construidos: {len(movimentos_jsons)}')

# Merge: movimentos_jsons has priority (has applied promotions)
# Merge: audit has priority for JSONs with pagos (flat structure), otherwise movimentos (has promoções applied)
all_partner_jsons = {}
for cupom in set(partner_jsons.keys()) | set(movimentos_jsons.keys()):
    audit_json = partner_jsons.get(cupom)
    mov_json = movimentos_jsons.get(cupom)
    
    # Check if audit JSON has pagos (flat structure) or movimiento.pagos (wrapped structure)
    audit_has_pagos = False
    if audit_json:
        if 'pagos' in audit_json and audit_json['pagos']:
            audit_has_pagos = True
        elif 'movimiento' in audit_json and audit_json['movimiento'].get('pagos'):
            audit_has_pagos = True
    
    # Prefer audit JSON if it has pagos, otherwise use movimentos (has promoções)
    if audit_has_pagos:
        all_partner_jsons[cupom] = audit_json
    elif mov_json:
        all_partner_jsons[cupom] = mov_json
    else:
        all_partner_jsons[cupom] = audit_json

print(f'   Total JSONs combinados: {len(all_partner_jsons)}')

# 5c. Compare pagamentos do roteiro vs pagos do export_movimentos
print('5c. Comparando pagamentos do roteiro vs export_movimentos...')
for cupom, group in df.groupby('Número'):
    if cupom in all_partner_jsons:
        partner_json = all_partner_jsons[cupom]
        # Handle both flat and wrapped structure
        movimiento = partner_json.get('movimiento', partner_json)
        
        # Get expected payments from validated test for this cupom
        test_for_cupom = next((t for t in validated_tests if str(t.get('cupom', '')).strip() == cupom), None)
        if test_for_cupom:
            pagos_esperados = test_for_cupom.get('pagamentos', [])
            if pagos_esperados:
                # Build pagos from roteiro info
                built_json = api_builder.build_sale_json(
                    teste=test_for_cupom.get('teste'),
                    itens_da_venda=test_for_cupom.get('itens_da_venda', ''),
                    pagamento=test_for_cupom.get('pagamento', ''),
                    subtotal=test_for_cupom.get('subtotal_esperado', 0),
                    desconto=test_for_cupom.get('desconto_esperado', 0),
                    total=test_for_cupom.get('total_esperado', 0),
                    observacoes=test_for_cupom.get('observacoes', ''),
                    numero_cupom=cupom,
                    tipo_promo=str(test_for_cupom.get('tipo_promo', '')).strip(),
                    pagamentos=pagos_esperados,
                    delivery_postal_code='',
                    referencia='',
                    id_cliente='',
                    documento_cliente='',
                )
                # Update pagos in partner_json (handle both structures)
                if 'movimiento' in built_json:
                    pagos_built = built_json['movimiento'].get('pagos', [])
                    # Apply to correct structure
                    if 'movimiento' in partner_json:
                        partner_json['movimiento']['pagos'] = pagos_built
                    else:
                        partner_json['pagos'] = pagos_built

print(f'   Total JSONs combinados: {len(all_partner_jsons)}')

# 6. Re-validate with partner JSONs (combines business rules + partner JSON validation)
print('6. Re-validando com JSONs do parceiro...')
# Pass updated partner JSONs (with pagos from roteiro) to validator
revalidator = TestValidator(tolerance=0.01, partner_jsons=all_partner_jsons)
revalidated_tests = []
for t in validated_tests:
    test_cupom = str(t.get('cupom', '')).strip()
    if test_cupom in all_partner_jsons:
        # Use the updated partner JSON (with pagos from roteiro) as BOTH sale_json and partner reference
        # This ensures pagos_interno is populated (from sale_json) and pagos_parceiro works (from partner_jsons)
        t['sale_json'] = all_partner_jsons[test_cupom]
    revalidated_tests.append(revalidator.validate(t))
validated_tests = revalidated_tests

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