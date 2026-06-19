#!/usr/bin/env python3
"""
Payment Normalizer Module
Responsible for normalizing payment methods to standard codes.
Supports POS, canal de venda, cancelamentos, and multiple payments.
"""

import re
from typing import List, Dict, Any, Optional

class PaymentNormalizer:
    """Normalizes payment methods from test scripts to standard payment codes."""
    
    # Mapping from payment descriptions to standard codes
    PAYMENT_MAPPING = {
        'dinheiro': 9,
        'dinheiro com troco': 9,
        'cartao credito': 10,
        'cartao crédito': 10,
        'cartao debito': 13,
        'cartao débito': 13,
        'pix': 14,
        'qr': 14,
        'pix/qr': 14,
        'cheque': 11,
        'vale': 12,
        'finalizadora': 15
    }
    
    # Multiplier words
    MULTIPLIER_WORDS = {
        'uma': 1, 'um': 1, '1': 1,
        'duas': 2, 'dois': 2, '2': 2,
        'tres': 3, 'três': 3, '3': 3,
        'quatro': 4, '4': 4,
        'cinco': 5, '5': 5,
    }
    
    def normalize_payment(self, test_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize the payment method in a test dictionary.

        Args:
            test_dict: Dictionary containing test data with 'pagamento' field (from reader)
                   or 'pagamento_raw' field (for backward compatibility)

        Returns:
            Updated test dictionary with normalized payment information
        """
        # Create a copy to avoid modifying the original
        result = test_dict.copy()

        # Get the raw payment string - try reader's field name first, then fallback
        pagamento_raw = test_dict.get('pagamento', test_dict.get('pagamento_raw', ''))
        observacoes = test_dict.get('observacoes', '')

        if not pagamento_raw or not isinstance(pagamento_raw, str):
            result['pagamento_normalizado'] = ''
            result['codigo_tipo_pago'] = None
            result['is_multiplo'] = False
            result['requires_bin'] = False
            result['pagamentos'] = []
            result['tem_pos'] = False
            result['canal_venda'] = 1
            result['is_cancelamento_venda'] = False
            result['is_cancelamento_antecipado'] = False
            return result

        # Normalize the payment
        normalized = self._normalize_payment_string(pagamento_raw, observacoes)

        result['pagamento_normalizado'] = normalized['normalized']
        result['codigo_tipo_pago'] = normalized['codigo']
        result['is_multiplo'] = normalized['is_multiplo']
        result['requires_bin'] = normalized['requires_bin']
        result['pagamentos'] = normalized['pagamentos']
        result['tem_pos'] = normalized['tem_pos']
        result['canal_venda'] = normalized['canal_venda']
        result['is_cancelamento_venda'] = normalized['is_cancelamento_venda']
        result['is_cancelamento_antecipado'] = normalized['is_cancelamento_antecipado']

        return result
    
    def _normalize_payment_string(self, pagamento_string: str, observacoes: str = '') -> Dict[str, Any]:
        """
        Normalize a payment string to determine if it's single or multiple.
        
        Args:
            pagamento_string: Raw payment string from the test script
            observacoes: Observations field for POS/canal detection
            
        Returns:
            Dictionary with keys: normalized, codigo, is_multiplo, requires_bin, 
            pagamentos, tem_pos, canal_venda, is_cancelamento_venda, is_cancelamento_antecipado
        """
        # Convert to lowercase for comparison
        pagamento_lower = pagamento_string.lower().strip()
        obs_lower = observacoes.lower().strip() if observacoes else ''
        
        # Detect POS in observations or payment
        tem_pos = 'pos' in obs_lower or 'pos' in pagamento_lower
        
        # Detect canal de venda
        canal_venda = 1  # default
        if 'canal de venda 2' in obs_lower or 'canal 2' in obs_lower:
            canal_venda = 2
        elif ('diferente de 1 e 2' in obs_lower or 
             
              'canal diferente de 1' in obs_lower or
              'canal de venda diferente' in obs_lower):
            canal_venda = 3
        
        # Detect cancelamentos
        is_cancelamento_venda = 'cancelar venda' in obs_lower
        is_cancelamento_antecipado = 'cancelar antes de pagar' in obs_lower or \
                                     ('cancelar' in obs_lower and not pagamento_lower.strip())
        
        # If cancelamento antecipado, no payment expected
        if is_cancelamento_antecipado:
            return {
                'normalized': 'CANCELAMENTO_ANTECIPADO',
                'codigo': None,
                'is_multiplo': False,
                'requires_bin': False,
                'pagamentos': [],
                'tem_pos': tem_pos,
                'canal_venda': canal_venda,
                'is_cancelamento_venda': False,
                'is_cancelamento_antecipado': True
            }
        
        # Check if it's a multiple payment
        # Normalize separators: replace ", e " with " e " and "," with " + "
        normalized_sep = pagamento_lower.replace(', e ', ' e ').replace(', ', ' + ').replace(',', ' + ')
        # Split by + or " e "
        parts = re.split(r'\s*\+\s*|\s+e\s+', normalized_sep)
        parts = [p.strip() for p in parts if p.strip()]
        
        pagamentos = []
        
        for part in parts:
            multiplier = 1
            clean_part = part
            
            # Check for "duas vezes", "tres vezes", etc.
            mult_match = re.match(r'^(\d+|duas?|tres?|quatro|cinco)\s*vezes?\s+(.+)$', clean_part)
            if mult_match:
                mult_str = mult_match.group(1)
                clean_part = mult_match.group(2).strip()
                multiplier = self.MULTIPLIER_WORDS.get(mult_str, 1)
            
            clean_part = clean_part.strip()
            
            # Try to match payment type
            norm = codigo = None
            if clean_part in self.PAYMENT_MAPPING:
                norm, codigo = clean_part, self.PAYMENT_MAPPING[clean_part]
            else:
                for k, v in self.PAYMENT_MAPPING.items():
                    if k in clean_part or clean_part in k:
                        norm, codigo = k, v
                        break
            
            if norm is not None:
                for _ in range(multiplier):
                    pagamentos.append({
                        'norm': norm,
                        'codigo': codigo,
                        'raw': clean_part,
                        'tem_pos': tem_pos and (norm in ['cartao credito', 'cartao débito', 'cartao debito'])
                    })
        
        is_multiplo = len(pagamentos) > 1
        
        if is_multiplo:
            return {
                'normalized': 'MULTIPLO',
                'codigo': None,
                'is_multiplo': True,
                'requires_bin': any(p['codigo'] in [10, 13] for p in pagamentos),
                'pagamentos': pagamentos,
                'tem_pos': tem_pos,
                'canal_venda': canal_venda,
                'is_cancelamento_venda': is_cancelamento_venda,
                'is_cancelamento_antecipado': False
            }
        elif len(pagamentos) == 1:
            p = pagamentos[0]
            return {
                'normalized': p['norm'],
                'codigo': p['codigo'],
                'is_multiplo': False,
                'requires_bin': p['codigo'] in [10, 13],
                'pagamentos': pagamentos,
                'tem_pos': p['tem_pos'],
                'canal_venda': canal_venda,
                'is_cancelamento_venda': is_cancelamento_venda,
                'is_cancelamento_antecipado': False
            }
        else:
            # No recognized payment
            return {
                'normalized': pagamento_string,
                'codigo': None,
                'is_multiplo': False,
                'requires_bin': False,
                'pagamentos': [],
                'tem_pos': tem_pos,
                'canal_venda': canal_venda,
                'is_cancelamento_venda': is_cancelamento_venda,
                'is_cancelamento_antecipado': False
            }