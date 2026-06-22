import pandas as pd
import json

# Read the template - all sheets
print("=== TEMPLATE (2) - ALL SHEETS ===")
xls = pd.ExcelFile('biblioteca/teste 2/TEMPLATE_COM_BIN_NOVO (2).xlsx')
print('Sheets:', xls.sheet_names)

for sheet in xls.sheet_names:
    df = pd.read_excel('biblioteca/teste 2/TEMPLATE_COM_BIN_NOVO (2).xlsx', sheet_name=sheet, header=None)
    print(f'\n--- Sheet: {sheet} ---')
    print('Shape:', df.shape)
    # Print first 15 rows
    for i in range(min(15, len(df))):
        print(f'Row {i}: {df.iloc[i].tolist()}')
