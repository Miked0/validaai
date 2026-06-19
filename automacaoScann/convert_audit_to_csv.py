import openpyxl
import json
from pathlib import Path

# Import centralized payment codes from package
from validaai import get_payment_label

def extract_test_case_from_row(row):
    """Extract a test case dictionary from a row of the audit export."""
    # The row is a tuple of cell values, in order of columns
    # We need to map column indices to values
    # From the header we saw earlier:
    # 0: Data recepção
    # 1: Usuario
    # 2: Código empresa
    # 3: Código loja
    # 4: Código caixa
    # 5: Método
    # 6: Data comercial
    # 7: Número cupom
    # 8: Código status
    # 9: Banco de dados
    # 10: Host
    # 11: Versão
    # 12: Checksum
    # 13: Versão PDV
    # 14: Versão Backend
    # 15: Código transação pendente
    # 16: Id request
    # 17: Trace id
    # 18: Request (JSON string)
    # 19: Response (JSON string)
    
    # We're interested in:
    # - Número cupom (index 7) -> teste
    # - Request (index 18) -> JSON with detalhes, pagos, total, descontoTotal, etc.
    # - Response (index 19) -> maybe for observacoes?
    
    teste_value = row[7]  # Número cupom
    request_json_str = row[18]
    response_json_str = row[19]  # might use for observacoes
    
    # Parse the Request JSON
    try:
        request_data = json.loads(request_json_str)
    except json.JSONDecodeError as e:
        print(f"Error parsing Request JSON for cupom {teste_value}: {e}")
        return None
    
    # Extract detalles (items)
    detalles = request_data.get('detalles', [])
    # Extract pagos (payments)
    pagos = request_data.get('pagos', [])
    # Extract total
    total = request_data.get('total', 0.0)
    # Extract descontoTotal
    desconto_total = request_data.get('descontoTotal', 0.0)
    
    # Process items: format as "quantidade x codigoBarras"
    item_strings = []
    subtotal = 0.0
    total_desconto_items = 0.0
    for item in detalles:
        cantidad = item.get('cantidad', 0)
        codigo_barras = item.get('codigoBarras', '')
        importe_unitario = item.get('importeUnitario', 0.0)
        importe_item = item.get('importe', 0.0)  # this is the net amount for the item line
        descuento_item = item.get('desconto', 0.0)
        
        # Format item string: "quantidade x codigoBarras"
        if codigo_barras:  # only add if we have a barcode
            item_strings.append(f"{cantidad} x {codigo_barras}")
        
        # Accumulate for subtotal (quantity * unit price)
        subtotal += cantidad * importe_unitario
        # Accumulate discount from items
        total_desconto_items += descuento_item
    
    # Join item strings with " + "
    itens_da_venda = " + ".join(item_strings) if item_strings else ""
    
    # Process payments: get payment method descriptions
    pago_strings = []
    for pago in pagos:
        codigo_tipo_pago = pago.get('codigoTipoPago')
        importe_pago = pago.get('importe', 0.0)
        # Get description from centralized mapping
        desc = get_payment_label(codigo_tipo_pago)
        pago_strings.append(desc)
    pagamento = " + ".join(pago_strings) if pago_strings else ""
    
    # Use the total from JSON, or compute subtotal - desconto_total
    # We'll use the total from JSON as it's authoritative
    total_val = float(total)
    # Compute subtotal as sum of (cantidad * importeUnitario) - we already have subtotal variable
    # But note: our subtotal variable above is sum of (cantidad * importeUnitario)
    # We can use that, or we can compute total + desconto_total
    # Let's use our computed subtotal to be consistent
    subtotal_val = subtotal  # sum of quantity * unit price
    desconto_val = desconto_total  # from JSON
    
    # Observacoes: we can try to get from Response or other fields
    observacoes = ""
    # For now, leave empty; maybe we can put something from Response if needed
    
    # Tipo promo: we don't have a direct equivalent; maybe leave empty or use something else
    tipo_promo = ""
    # Bloco: empty
    bloco = ""
    
    # Build the test case dictionary in the format expected by our reader
    test_case = {
        'teste': teste_value,
        'itens_da_venda': itens_da_venda,
        'pagamento': pagamento,
        'subtotal': str(subtotal_val),
        'desconto': str(desconto_val),
        'total': str(total_val),
        'observacoes': observacoes,
        'bloco': bloco,
        'tipo_promo': tipo_promo
    }
    return test_case

def main():
    # Path to the audit export Excel file
    excel_path = "C:/Users/Mike/.hermes/automacaoScann/biblioteca/Teste de exemplo/export_tickets_audit_companyId-200056_auditDate-2026-06-08_2e9386_09-06-2026_19-35.xlsx"
    
    # Load the workbook
    workbook = openpyxl.load_workbook(excel_path)
    sheet = workbook.active
    
    # Skip header row
    rows = list(sheet.iter_rows(min_row=2, values_only=True))  # min_row=2 to skip header
    
    # Extract test cases
    test_cases = []
    for row in rows:
        test_case = extract_test_case_from_row(row)
        if test_case is not None:
            test_cases.append(test_case)
    
    print(f"Extracted {len(test_cases)} test cases from the audit export.")
    
    # If we have test cases, write them to a CSV file in the format expected by our reader
    if test_cases:
        # Define the header in the order expected by our reader
        # Our reader expects columns like: teste, itens_da_venda, pagamento, subtotal, desconto, total, observacoes, bloco, tipo_promo
        # But note: the reader also uses these fields in _process_data, and we want to match the format of the original CSV
        # Looking at the original roteiro_testes.csv, it had columns:
        # teste, tipo_promo, itens_da_venda, pagamento, observacoes, subtotal, desconto, total
        # and also bloco_atual is computed by the reader.
        # So we should output at least: teste, tipo_promo, itens_da_venda, pagamento, observacoes, subtotal, desconto, total
        # The reader will compute bloco_atual.
        
        # Define the header order as in the original CSV
        header = ['teste', 'tipo_promo', 'itens_da_venda', 'pagamento', 'observacoes', 'subtotal', 'desconto', 'total']
        
        # Write to CSV
        output_path = "C:/Users/Mike/.hermes/automacaoScann/input/roteiro_testes.csv"
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            # Write header
            f.write(','.join([f'"{col}"' for col in header]) + '\n')
            # Write data rows
            for test_case in test_cases:
                # Build row in header order
                row_vals = []
                for col in header:
                    val = test_case.get(col, '')
                    # Ensure it's a string
                    if val is None:
                        val = ''
                    else:
                        val = str(val)
                    # Escape quotes and wrap in quotes if necessary
                    if '"' in val or ',' in val or '\n' in val:
                        val = '"' + val.replace('"', '""') + '"'
                    row_vals.append(val)
                f.write(','.join(row_vals) + '\n')
        print(f"Wrote converted test cases to {output_path}")
    else:
        print("No test cases extracted.")

if __name__ == "__main__":
    main()