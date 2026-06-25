#!/usr/bin/env python3
"""Bateria de testes completa - Relatório SDD por Etapa"""
import sys
sys.path.insert(0, '/home/ubuntu/validaai/automacaoScann')

from src.validaai.reader import TestScriptReader
from src.validaai.parser_items import ItemParser
from src.validaai.payments import PaymentNormalizer
from src.validaai.validators import TestValidator
from src.validaai.api_sales import APISalesBuilder
import pandas as pd
from collections import Counter

# 1. Read roteiro (ETAPA 2)
print('=' * 80)
print('BATERIA DE TESTES - ETAPA 2 (SDD v1.0)')
print('=' * 80)
print()

reader = TestScriptReader('/home/ubuntu/validaai_test_data/doc_2e02e003bd9a_TEMPLATE_ROTEIRO_DE_TESTES_CB_1.0.xlsx')
reader.set_etapa('ETAPA 2')
raw_tests = reader.read_tests()
print(f'Total testes lidos: {len(raw_tests)}')
print()

# 2. Parse items
item_parser = ItemParser()
parsed_tests = [item_parser.parse_items(t) for t in raw_tests]

# 3. Normalize payments
payment_normalizer = PaymentNormalizer()
normalized_tests = [payment_normalizer.normalize_payment(t) for t in parsed_tests]

# 4. Business rule validation (single stage)
validator = TestValidator(tolerance=0.01)
validated_tests = [validator.validate(t) for t in normalized_tests]

# 4. Load partner JSONs (audit + movimentos)
api_builder = APISalesBuilder()
audit_file = '/home/ubuntu/validaai_test_data/doc_0f4caf1d2b79_export_tickets_audit_companyId201901_auditDate2026-06-22_87bda8_24-06-2026_15-38.xlsx'
partner_jsons = api_builder._load_partner_jsons(audit_file)

movimentos_file = '/home/ubuntu/validaai_test_data/doc_c0c58b0e0c99_export_tickets_companyId201901_from2026-06-22_to2026-06-22_7892db_24-06-2026_15-38.xlsx'
df = pd.read_excel(movimentos_file, sheet_name='TICKETS', dtype=str)

# Build movimentos_jsons
movimentos_jsons = {}
for cupom, group in df.groupby('Número'):
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
    promocoes = group['ID Promoção'].dropna().unique()
    if len(promocoes) > 0:
        movimiento['promociones'] = []
        for promo_id in promocoes:
            promo_rows = group[group['ID Promoção'] == promo_id]
            desc_promo = promo_rows['Desconto promoção'].sum()
            if desc_promo:
                desc_str = str(desc_promo).replace('.', '').replace(',', '.')
                desc_val = float(desc_str) if desc_str else 0.0
                movimiento['promociones'].append({
                    'idPromocion': str(promo_id),
                    'descuento': desc_val,
                })
    desc_total = sum(float(d.get('descuento', 0) or 0) for d in movimiento['detalles'])
    movimiento['descuentoTotal'] = round(desc_total, 2)
    total_items = sum(float(d.get('importe', 0) or 0) for d in movimiento['detalles'])
    if total_items > 0:
        movimiento['total'] = round(total_items, 2)
    movimentos_jsons[cupom] = {'movimiento': movimiento}

# Merge: movimentos has priority
partner_jsons = api_builder._load_partner_jsons('/home/ubuntu/validaai_test_data/doc_0f4caf1d2b79_export_tickets_audit_companyId201901_auditDate2026-06-22_87bda8_24-06-2026_15-38.xlsx')
all_partner_jsons = {**partner_jsons, **movimentos_jsons}

# Build movimentos_jsons and add pagos
movimentos_jsons = {}
for cupom, group in df.groupby('Número'):
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
    promocoes = group['ID Promoção'].dropna().unique()
    if len(promocoes) > 0:
        movimiento['promociones'] = []
        for promo_id in promocoes:
            promo_rows = group[group['ID Promoção'] == promo_id]
            desc_promo = promo_rows['Desconto promoção'].sum()
            if desc_promo:
                desc_str = str(desc_promo).replace('.', '').replace(',', '.')
                desc_val = float(desc_str) if desc_str else 0.0
                movimiento['promociones'].append({
                    'idPromocion': str(promo_id),
                    'descuento': desc_val,
                })
    desc_total = sum(float(d.get('descuento', 0) or 0) for d in movimiento['detalles'])
    movimiento['descuentoTotal'] = round(desc_total, 2)
    total_items = sum(float(d.get('importe', 0) or 0) for d in movimiento['detalles'])
    if total_items > 0:
        movimiento['total'] = round(total_items, 2)
    movimentos_jsons[cupom] = {'movimiento': movimiento}

# Add pagos from validated tests
for cupom, group in df.groupby('Número'):
    if cupom in all_partner_jsons and 'movimiento' in all_partner_jsons[cupom]:
        test_for_cupom = next((t for t in validated_tests if str(t.get('cupom', '')).strip() == cupom), None)
        if test_for_cupom:
            pagos_esperados = test_for_cupom.get('pagamentos', [])
            if pagos_esperados:
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
                if 'movimiento' in built_json:
                    all_partner_jsons[cupom]['movimiento']['pagos'] = built_json['movimiento'].get('pagos', [])

all_partner_jsons = {**partner_jsons, **movimentos_jsons}

# Re-validate with partner JSONs
revalidator = TestValidator(tolerance=0.01)
revalidated_tests = []
for t in validated_tests:
    test_cupom = str(t.get('cupom', '')).strip()
    if test_cupom in all_partner_jsons:
        t['sale_json'] = all_partner_jsons[test_cupom]
    revalidated_tests.append(revalidator.validate(t))

# ============================================================
# RELATÓRIO POR ETAPA (SDD)
# ============================================================

print("=" * 100)
print("RELATÓRIO DETALHADO POR ETAPA SDD - ETAPA 2")
print("=" * 100)
print()

# Collect stage results
stage_results = {}
for t in revalidated_tests:
    teste_num = t.get('teste', 'N/A')
    cupom = t.get('cupom', 'N/A')
    tipo_promo = t.get('tipo_promo', '')[:50]
    
    # Extract stage results from test dict
    etapa1 = t.get('etapa1_itens', {})
    etapa2 = t.get('etapa2_pagamento', {})
    etapa3 = t.get('etapa3_valores', {})
    etapa4 = t.get('etapa4_observacoes', {})
    status_final = t.get('status_final', 'N/A')
    motivo = t.get('motivo_status', '')
    api_status = t.get('api_status', 'N/A')
    api_alertas = '; '.join(t.get('api_alertas', []))[:80]
    
    # Store for summary
    if teste_num not in stage_results:
        stage_results[teste_num] = {
            'cupom': cupom,
            'promo': t.get('tipo_promo', '')[:40],
            'etapa1': etapa1,
            'etapa2': etapa2,
            'etapa3': etapa3,
            'etapa4': etapa4,
            'final': status_final,
            'motivo': motivo[:100],
            'api_status': api_status,
            'api_alertas': api_alertas
        }

# Print detailed report per test
for teste_num in sorted(stage_results.keys(), key=lambda x: int(x) if str(x).isdigit() else 999):
    r = stage_results[teste_num]
    print(f"\n{'─' * 100}")
    print(f"TESTE {teste_num:>3} | Cupom: {r['cupom']:>6} | PROMO: {r['promo']}")
    print(f"{'─' * 100}")
    
    # ETAPA 1 - ITENS
    e1 = r['etapa1']
    print(f"  ETAPA 1 - ITENS: {e1.get('json', 'N/A'):>8} | {e1.get('json_motivo', '')}")
    
    # ETAPA 2 - PAGAMENTO + PROMOÇÕES
    e2 = r['etapa2']
    print(f"  ETAPA 2 - PAGTO+PROMO: {e2.get('json', 'N/A'):>8} | {e2.get('json_motivo', '')}")
    if e2.get('pagos_alerta'):
        print(f"    ↳ Pagos Alerta: {e2.get('pagos_alerta')}")
    
    # ETAPA 3 - VALORES + PROMOÇÕES
    e3 = r['etapa3']
    print(f"  ETAPA 3 - VALORES: {e3.get('json', 'N/A'):>8} | {e3.get('json_motivo', '')}")
    
    # ETAPA 4 - OBSERVAÇÕES ESPECIAIS
    e4 = r['etapa4']
    print(f"  ETAPA 4 - OBS ESPECIAIS:")
    for k, v in e4.items():
        if k != 'json' and v in ('REVISAO', 'ERRO'):
            print(f"    ↳ {k}: {v}")
    
    # FINAL
    print(f"  {'─' * 50}")
    print(f"  VEREDITO FINAL: {r['final']:>12} | MOTIVO: {r['motivo']}")
    print(f"  API: {r['api_status']:>12} | ALERTAS: {r['api_alertas']}")

# Summary
print(f"\n{'=' * 100}")
print("RESUMO CONSOLIDADO")
print(f"{'=' * 100}")

final_counts = Counter(r['final'] for r in stage_results.values())
etapa1_counts = Counter(r['etapa1'].get('json', 'N/A') for r in stage_results.values())
etapa2_counts = Counter(r['etapa2'].get('json', 'N/A') for r in stage_results.values())
etapa3_counts = Counter(r['etapa3'].get('json', 'N/A') for r in stage_results.values())

print(f"\nETAPA 1 (ITENS):        {dict(etapa1_counts)}")
print(f"ETAPA 2 (PAGTO+PROMO):  {dict(etapa2_counts)}")
print(f"ETAPA 3 (VALORES):      {dict(etapa3_counts)}")
print(f"\nVEREDITO FINAL:         {dict(final_counts)}")
print(f"Total testes: {len(stage_results)}")