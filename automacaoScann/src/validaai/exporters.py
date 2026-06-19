#!/usr/bin/env python3
"""
Result Exporter Module
Responsible for exporting validation results to Excel or CSV.
"""

import json
from typing import List, Dict, Any
from pathlib import Path

class ResultExporter:
    """Exports validation results to spreadsheet format."""
    
    def export(self, test_results: List[Dict[str, Any]], output_path: str) -> None:
        """
        Export test results to an Excel file.
        
        Args:
            test_results: List of validated test dictionaries
            output_path: Path where the output file should be saved
        """
        if not test_results:
            print("WARNING: No test results to export")
            # Create an empty file with headers
            self._create_empty_output(output_path)
            return
        
        # Prepare data for export
        export_data = []
        
        for test in test_results:
            row = {}
            row['Data recepção'] = test.get('data_recepcao') or test.get('generated_at') or ''
            
            # Items information
            itens_raw = test.get('itens_da_venda', test.get('itens_raw', ''))
            row['itens_raw'] = itens_raw
            
            itens_parseados = test.get('itens_parseados', [])
            # Convert parsed items to string representation for export
            itens_str = ', '.join([
                f"{item.get('quantidade', 0)} x {item.get('codigo', '')}" 
                for item in itens_parseados
            ]) if itens_parseados else ''
            row['itens_parseados'] = itens_str
            
            row['Usuario'] = ''
            row['Código empresa'] = test.get('empresa') or test.get('codigo_empresa') or ''
            row['Código loja'] = test.get('loja') or test.get('codigo_loja') or ''
            row['Código caixa'] = test.get('caixa') or test.get('codigo_caixa') or ''
            row['Método'] = 'agregarMovimiento'
            row['Data comercial'] = test.get('data_comercial') or test.get('fecha') or ''
            row['Número cupom'] = test.get('numero_cupom') or test.get('numero') or test.get('teste', '')
            row['Código status'] = test.get('status_final') or test.get('api_status') or ''
            row['Banco de dados'] = ''
            row['Host'] = ''
            row['Versão'] = ''
            row['Checksum'] = ''
            row['Versão PDV'] = ''
            row['Versão Backend'] = ''
            row['Código transação pendente'] = test.get('codigo_transacao_pendente') or ''
            row['Id request'] = test.get('id_request') or ''
            row['Trace id'] = test.get('trace_id') or ''
            sale_json = test.get('sale_json') or {}
            if isinstance(sale_json, dict):
                def _default(obj):
                    from decimal import Decimal
                    if isinstance(obj, Decimal):
                        return float(obj)
                    raise TypeError(f'Object of type {obj.__class__.__name__} is not JSON serializable')

                sale_json = json.dumps(sale_json, ensure_ascii=False, default=_default)
            row['Request'] = sale_json or ''
            row['Response'] = test.get('response') or test.get('api_response') or ''
            
            export_data.append(row)
        
        # Create DataFrame if pandas is available, otherwise fall back to manual CSV
        try:
            import pandas as pd
            df = pd.DataFrame(export_data)
            pandas_available = True
        except ImportError:
            pandas_available = False

        if pandas_available:
            # Define column order for output
            column_order = [
                'teste', 'bloco', 'tipo_promo',
                'itens_raw', 'itens_parseados',
                'pagamento_raw', 'codigo_tipo_pago',
                'subtotal_esperado', 'subtotal_norm',
                'desconto_esperado', 'desconto_norm',
                'total_esperado', 'total_norm',
                'status_final', 'motivo_status',
                'alertas', 'observacoes_originais',
                'api_status', 'api_alertas', 'sale_json'
            ]

            # Ensure all columns exist
            for col in column_order:
                if col not in df.columns:
                    df[col] = ''

            # Reorder columns
            df = df[column_order]

            # Save to Excel
            try:
                df.to_excel(output_path, index=False)
                print(f"   Exported {len(df)} test results to {output_path}")
            except Exception as e:
                # Fallback to CSV if Excel fails
                csv_path = output_path.replace('.xlsx', '.csv')
                df.to_csv(csv_path, index=False)
                print(f"   Excel export failed, saved as CSV instead: {csv_path}")
                print(f"   Error: {str(e)}")
        else:
            # Fallback: manually create CSV when pandas is not available
            print("   WARNING: Pandas not available. Creating CSV output manually.")
            # Define column order
            column_order = [
                'teste', 'bloco', 'tipo_promo',
                'itens_raw', 'itens_parseados',
                'pagamento_raw', 'codigo_tipo_pago',
                'subtotal_esperado', 'subtotal_norm',
                'desconto_esperado', 'desconto_norm',
                'total_esperado', 'total_norm',
                'status_final', 'motivo_status',
                'alertas', 'observacoes_originais'
            ]
            
            # Write CSV manually
            try:
                with open(output_path.replace('.xlsx', '.csv'), 'w', newline='', encoding='utf-8') as csvfile:
                    # Write header
                    csvfile.write(','.join([f'"{col}"' for col in column_order]) + '\n')
                    # Write data rows
                    for row in export_data:
                        # Ensure all columns exist with default empty string
                        csv_row = []
                        for col in column_order:
                            value = row.get(col, '')
                            # Handle None values and convert to string
                            if value is None:
                                value = ''
                            # Escape quotes and wrap in quotes if needed
                            str_value = str(value)
                            if '"' in str_value or ',' in str_value or '\n' in str_value:
                                str_value = '"' + str_value.replace('"', '""') + '"'
                            csv_row.append(str_value)
                        csvfile.write(','.join(csv_row) + '\n')
                print(f"   Created CSV output manually: {output_path.replace('.xlsx', '.csv')}")
            except Exception as e:
                print(f"   ERROR: Failed to create CSV output: {str(e)}")
    
    def _create_empty_output(self, output_path: str) -> None:
        """Create an empty output file with headers."""
        column_order = [
            'teste', 'bloco', 'tipo_promo',
            'itens_raw', 'itens_parseados',
            'pagamento_raw', 'codigo_tipo_pago',
            'subtotal_esperado', 'subtotal_norm',
            'desconto_esperado', 'desconto_norm',
            'total_esperado', 'total_norm',
            'status_final', 'motivo_status',
            'alertas', 'observacoes_originais'
        ]
        
        # Try to use pandas if available, otherwise fall back to manual CSV
        try:
            import pandas as pd
            df = pd.DataFrame(columns=column_order)
            pandas_available = True
        except ImportError:
            pandas_available = False

        if pandas_available:
            try:
                df.to_excel(output_path, index=False)
                print(f"   Created empty output file: {output_path}")
            except Exception as e:
                csv_path = output_path.replace('.xlsx', '.csv')
                df.to_csv(csv_path, index=False)
                print(f"   Created empty CSV output file: {csv_path}")
        else:
            # Fallback: manually create CSV when pandas is not available
            print("   WARNING: Pandas not available. Creating empty CSV output manually.")
            try:
                with open(output_path.replace('.xlsx', '.csv'), 'w', newline='', encoding='utf-8') as csvfile:
                    # Write header only
                    csvfile.write(','.join([f'"{col}"' for col in column_order]) + '\n')
                print(f"   Created empty CSV output manually: {output_path.replace('.xlsx', '.csv')}")
            except Exception as e:
                print(f"   ERROR: Failed to create empty CSV output: {str(e)}")
