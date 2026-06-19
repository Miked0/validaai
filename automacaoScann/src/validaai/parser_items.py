#!/usr/bin/env python3
"""
Item Parser Module
Responsible for parsing item strings into structured format.
Supports validation of pesável quantities against roteiro.
"""

import re
from typing import List, Dict, Any, Union

class ItemParser:
    """Parses item strings from test scripts into structured format."""
    
    def parse_items(self, test_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse the items string into a structured format.

        Args:
            test_dict: Dictionary containing test data with 'itens_da_venda' field (from reader)
                   or 'itens_raw' field (for backward compatibility)
           
        Returns:
            Updated test dictionary with parsed items and expected quantities for pesáveis
        """
        # Create a copy to avoid modifying the original
        result = test_dict.copy()

        # Get the raw items string - try reader's field name first, then fallback
        itens_raw = test_dict.get('itens_da_venda', test_dict.get('itens_raw', ''))

        if not itens_raw or not isinstance(itens_raw, str):
            result['itens_parseados'] = []
            result['pesaveis_esperados'] = {}
            return result

        # Parse the items
        parsed_items, pesaveis_esperados = self._parse_item_string(itens_raw)
        result['itens_parseados'] = parsed_items
        result['pesaveis_esperados'] = pesaveis_esperados

        return result
    
    def _parse_item_string(self, item_string: str) -> tuple:
        """
        Parse an item string into a list of item dictionaries.
        
        Supports formats like:
        - "3 x 7894904500383"
        - "7894904500383 + 7894904500383 + 7894904500383"
        - "3.579 x PESABLE" or "3,579 * PESABLE"
        - Mixed formats with +
        - Cancelamento item: "7891000029329 (Cancelar este ultimo item)"
        - Cancelamento unidade: "6 x 7896079500175(Cancelar 1 unidade)"
        
        Args:
            item_string: Raw item string from the test script
           
        Returns:
            Tuple of (List of dictionaries with keys: codigo, quantidade, tipo, quantidade_esperada), 
            Dict mapping pesavel_codigo -> quantidade_esperada
        """
        if not item_string or not isinstance(item_string, str):
            return [], {}
        
        # Split by + to get individual items or groups
        parts = [part.strip() for part in item_string.split('+') if part.strip()]
        
        parsed_items = []
        pesaveis_esperados = {}
        
        for part in parts:
            # Check for cancelamento item pattern: "EAN (Cancelar ...)"
            cancelar_item_match = re.search(r'\(cancelar[^)]*\)', part, re.IGNORECASE)
            cancelar_item = cancelar_item_match.group(0) if cancelar_item_match else ''
            
            # Remove cancelamento part for parsing
            part_clean = re.sub(r'\(cancelar[^)]*\)', '', part, flags=re.IGNORECASE).strip()
            # Remove annotations like "$5 de acrescimo na linha 1"
            part_clean = re.sub(r'\$[0-9]+(?:\.[0-9]+)?\s*de\s+(?:acrescimo|desconto).*', '', part_clean, flags=re.IGNORECASE).strip()
            
            # Check if this part has a quantity specification (number x item)
            # Support both "x" and "*" as multipliers, and comma/point decimal
            match = re.match(r'^([\d]+[.,]?\d*)\s*[x*]\s*(.+)$', part_clean.strip())
            if match:
                qty_str = match.group(1).replace(',', '.')
                quantity = float(qty_str)
                codigo = match.group(2).strip()
                item_type = self._determine_item_type(codigo)
                
                # If pesável, store expected quantity
                if item_type == 'pesavel':
                    # Use a generic key for pesável since multiple pesáveis could exist
                    pesaveis_esperados[codigo] = quantity
                    parsed_items.append({
                        'codigo': codigo,
                        'quantidade': quantity,
                        'quantidade_esperada': quantity,
                        'tipo': item_type,
                        'cancelar_item': bool(cancelar_item)
                    })
                else:
                    parsed_items.append({
                        'codigo': codigo,
                        'quantidade': quantity,
                        'tipo': item_type,
                        'cancelar_item': bool(cancelar_item)
                    })
            else:
                # No explicit quantity, assume 1
                codigo = part_clean.strip()
                if codigo and codigo.upper() not in ['PESABLE', 'PESAVEL', 'WEIGHT', 'PESO']:  # Skip standalone PESABLE without qty
                    if codigo:  # Only add if not empty
                        parsed_items.append({
                            'codigo': codigo,
                            'quantidade': 1.0,
                            'tipo': self._determine_item_type(codigo),
                            'cancelar_item': bool(cancelar_item)
                        })
        
        return parsed_items, pesaveis_esperados
    
    def _determine_item_type(self, codigo: str) -> str:
        """
        Determine the type of item based on its code.
        
        Args:
            codigo: Item code (EAN or special identifier)
           
        Returns:
            Item type: 'ean', 'pesavel', or 'outro'
        """
        codigo_upper = codigo.upper().strip()
        
        # Check for pesável items (typically marked as PESABLE or similar)
        if codigo_upper in ['PESABLE', 'PESAVEL', 'WEIGHT', 'PESO']:
            return 'pesavel'
        
        # Check if it looks like an EAN (8-13 digits, or 19 digits for invalid EAN test)
        if re.match(r'^\d{8,13}$', codigo_upper):
            return 'ean'
        if re.match(r'^\d{19}$', codigo_upper):
            return 'ean_invalido'
        
        # Default to 'outro' for other types
        return 'outro'