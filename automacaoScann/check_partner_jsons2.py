from src.validaai.api_sales import APISalesBuilder

builder = APISalesBuilder()
jsons = builder._load_partner_jsons('biblioteca/Teste de exemplo/export_tickets_audit_companyId-200056_auditDate-2026-06-08_2e9386_09-06-2026_19-35.xlsx')
print(f'Total partner JSONs loaded: {len(jsons)}')
for k, v in list(jsons.items())[:5]:
    print(f'Key: {k}')
    import json
    print(json.dumps(v, ensure_ascii=False, indent=2)[:500])
    print('...')
print(f'All keys: {sorted(jsons.keys())}')