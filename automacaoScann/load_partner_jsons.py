from src.validaai.api_sales import APISalesBuilder

builder = APISalesBuilder()
jsons = builder._load_partner_jsons('biblioteca/teste 2/export_tickets_audit_companyId=74866_auditDate=2026-06-11_a99383_18-06-2026_00-00.xlsx')
print(f'Total partner JSONs loaded: {len(jsons)}')
for k, v in list(jsons.items())[:10]:
    print(f'Key: {k}')
    import json
    print(json.dumps(v, ensure_ascii=False, indent=2)[:500])
    print('...')
print(f'\nAll keys: {list(jsons.keys())}')