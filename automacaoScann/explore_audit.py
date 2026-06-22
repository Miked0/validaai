import pandas as pd
import json

# Read the audit export - first sheet
print("=== AUDIT EXPORT ===")
df_audit = pd.read_excel('biblioteca/teste 2/export_tickets_audit_companyId=74866_auditDate=2026-06-11_a99383_18-06-2026_00-00.xlsx', header=None)
print('Shape:', df_audit.shape)
print('Row 0 (headers):', df_audit.iloc[0].tolist())
print()
print('Row 1 (first data):', df_audit.iloc[1].tolist())
print()
print('Row 2 (second data):', df_audit.iloc[2].tolist())

# Check all sheets
xls_audit = pd.ExcelFile('biblioteca/teste 2/export_tickets_audit_companyId=74866_auditDate=2026-06-11_a99383_18-06-2026_00-00.xlsx')
print('\nAudit sheets:', xls_audit.sheet_names)

for sheet in xls_audit.sheet_names:
    df = pd.read_excel('biblioteca/teste 2/export_tickets_audit_companyId=74866_auditDate=2026-06-11_a99383_18-06-2026_00-00.xlsx', sheet_name=sheet, header=None)
    print(f'\n--- Sheet: {sheet} ---')
    print('Shape:', df.shape)
    if df.shape[0] > 0:
        print('Row 0:', df.iloc[0].tolist())
    if df.shape[0] > 1:
        print('Row 1:', df.iloc[1].tolist())
