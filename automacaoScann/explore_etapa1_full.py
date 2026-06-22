import pandas as pd

# Read the full ETAPA 1 sheet
df = pd.read_excel('biblioteca/teste 2/TEMPLATE_COM_BIN_NOVO (2).xlsx', sheet_name='ETAPA 1', header=None)
print(f'Shape: {df.shape}')
print()

# Print all rows from row 7 onwards (test data)
for i in range(7, min(65, len(df))):
    row = df.iloc[i]
    teste = row[0]
    tipo_promo = row[1]
    itens = row[2]
    pagamento = row[3]
    obs = row[4]
    sat = row[5]
    ecf = row[6]
    nfce = row[7]
    subtotal = row[8]
    desconto = row[9]
    total = row[10]
    
    if pd.notna(teste):
        print(f'Teste {teste}: Tipo={tipo_promo}, Itens={itens}, Pag={pagamento}, Obs={obs}, Cupom={nfce}, Sub={subtotal}, Desc={desconto}, Total={total}')
