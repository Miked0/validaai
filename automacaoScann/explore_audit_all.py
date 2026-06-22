import pandas as pd
import json

# Read the audit export - extract all JSONs
print("=== AUDIT EXPORT - ALL JSONs ===")
df_audit = pd.read_excel('biblioteca/teste 2/export_tickets_audit_companyId=74866_auditDate=2026-06-11_a99383_18-06-2026_00-00.xlsx', header=None)

# Column 18 is Request (JSON), column 7 is cupom
for i in range(1, len(df_audit)):
    row = df_audit.iloc[i]
    cupom = str(row[7]).strip()
    request_json_str = str(row[18]).strip()
    metodo = str(row[5]).strip()
    
    try:
        request_json = json.loads(request_json_str)
        # Extract cupom from JSON
        json_cupom = str(request_json.get('numero', '')).strip()
        pagos = request_json.get('pagos', [])
        total = request_json.get('total', 0)
        detalles = request_json.get('detalles', [])
        recargoTotal = request_json.get('recargoTotal', 0)
        descuentoTotal = request_json.get('descuentoTotal', 0)
        codigoCanalVenta = request_json.get('codigoCanalVenta', 0)
        
        print(f"Row {i}: Cupom={cupom}, JSON Cupom={json_cupom}, Metodo={metodo}, Total={total}, Pagos={len(pagos)}, Items={len(detalles)}, RecargoTotal={recargoTotal}, DescTotal={descuentoTotal}, Canal={codigoCanalVenta}")
        for p in pagos:
            print(f"  Pago: codigoTipoPago={p.get('codigoTipoPago')}, detalleFinalizadora={p.get('detalleFinalizadora')}, importe={p.get('importe')}")
        for d in detalles[:3]:
            print(f"  Item: EAN={d.get('codigoBarras')}, qty={d.get('cantidad')}, unit={d.get('importeUnitario')}, recargo={d.get('recargo')}, desc={d.get('descuento')}")
        if len(detalles) > 3:
            print(f"  ... and {len(detalles)-3} more items")
    except Exception as e:
        print(f"Row {i}: ERROR parsing JSON: {e}")
