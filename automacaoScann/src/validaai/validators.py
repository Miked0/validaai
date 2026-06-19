#!/usr/bin/env python3
"""
Test Validator Module - SDD v1.0 Compliant
Responsible for validating test cases against business rules following
the 5-stage workflow: Items, Payment, Financial Values, Special Observations, Consolidation.
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal, ROUND_HALF_UP
import json


class TestValidator:
    """Validates test cases according to SDD Scanntech business rules."""

    def __init__(
        self,
        tolerance: float = 0.01,
        partner_jsons: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the validator.

        Args:
            tolerance: Base tolerance for value comparisons (default 0.01).
            partner_jsons: Dict mapping test/cupom -> partner JSON from audit export.
        """
        self.tolerance = tolerance
        self.partner_jsons = partner_jsons or {}

    def validate(self, test_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a test case through all 5 stages and determine final verdict.

        Args:
            test_dict: Dictionary containing test data

        Returns:
            Updated test dictionary with validation results per stage and final verdict
        """
        result = test_dict.copy()
        result = self._to_builtin(result)

        # Initialize validation tracking
        result['status_final'] = 'ERRO_DESCONHECIDO'
        result['motivo_status'] = ''
        result['alertas'] = []
        
        # Stage results for audit trail
        result['etapa1_itens'] = {}
        result['etapa2_pagamento'] = {}
        result['etapa3_valores'] = {}
        result['etapa4_observacoes'] = {}

        # Priority tracking (SDD order: Observação Parceiro > Casos Especiais > ERRO > OK)
        observacao_parceiro = str(result.get('observacao_parceiro', '')).strip()
        tem_obs_parceiro = observacao_parceiro and observacao_parceiro.lower() not in ['nan', 'none', '']
        
        revisao_required = False
        revisao_motivos = []
        erro_status = None
        erro_motivo = None
        ok_motivo = None

        # ============================================================
        # ETAPA 1 — Validação dos Itens (EAN, quantidades, pesáveis)
        # ============================================================
        etapa1_result = self._validate_etapa1_itens(result)
        result['etapa1_itens'] = etapa1_result
        
        if etapa1_result['json'] == 'ERRO':
            erro_status = 'ERRO_ITENS'
            erro_motivo = etapa1_result['json_motivo']
        elif etapa1_result['json'] == 'REVISAO':
            revisao_required = True
            revisao_motivos.append(etapa1_result['json_motivo'])

        # ============================================================
        # ETAPA 2 — Validação do Pagamento (meios, finalizadoras, POS)
        # ============================================================
        etapa2_result = self._validate_etapa2_pagamento(result)
        result['etapa2_pagamento'] = etapa2_result
        
        if etapa2_result['json'] == 'ERRO':
            if not erro_status:  # Don't override ERRO_ITENS
                erro_status = 'ERRO_PAGAMENTO'
                erro_motivo = etapa2_result['json_motivo']
        elif etapa2_result['json'] == 'REVISAO':
            revisao_required = True
            revisao_motivos.append(etapa2_result['json_motivo'])

        # ============================================================
        # ETAPA 3 — Validação dos Valores Financeiros
        # ============================================================
        etapa3_result = self._validate_etapa3_valores(result)
        result['etapa3_valores'] = etapa3_result
        
        if etapa3_result['json'] == 'ERRO':
            if not erro_status:
                erro_status = 'ERRO_VALORES'
                erro_motivo = etapa3_result['json_motivo']
        elif etapa3_result['json'] == 'REVISAO':
            revisao_required = True
            revisao_motivos.append(etapa3_result['json_motivo'])

        # ============================================================
        # ETAPA 4 — Validação das Observações Especiais
        # ============================================================
        etapa4_result = self._validate_etapa4_observacoes(result)
        result['etapa4_observacoes'] = etapa4_result
        
        for check_name, check_result in etapa4_result.items():
            if check_result == 'ERRO':
                if not erro_status:
                    erro_status = f'ERRO_{check_name.upper()}'
                    erro_motivo = f'Falha em {check_name}'
            elif check_result == 'REVISAO':
                revisao_required = True
                revisao_motivos.append(f'Observação especial: {check_name}')

        # ============================================================
        # ETAPA 5 — Consolidação e Veredicto Final (Priority Logic)
        # ============================================================
        
        # Priority 1: Observação do Parceiro (coluna U / Observacoes.1) -> REVISAO overrides ALL
        if tem_obs_parceiro:
            result['status_final'] = 'REVISAO'
            result['motivo_status'] = f'Observação do parceiro: {observacao_parceiro}'
            if revisao_motivos:
                result['motivo_status'] += ' | ' + '; '.join(revisao_motivos)
            if erro_motivo:
                result['motivo_status'] += f' | Erro também detectado: {erro_motivo}'
        # Priority 2: REVISAO from special cases
        elif revisao_required:
            result['status_final'] = 'REVISAO'
            result['motivo_status'] = '; '.join(revisao_motivos)
        # Priority 3: ERRO (hard error)
        elif erro_status:
            result['status_final'] = erro_status
            result['motivo_status'] = erro_motivo or 'Erro de validação'
        # Priority 4: OK
        else:
            result['status_final'] = 'OK'
            result['motivo_status'] = 'Todos os campos válidos e consistentes'

        # Consolidate alerts
        all_alertas = []
        for etapa_key in ['etapa1_itens', 'etapa2_pagamento', 'etapa3_valores', 'etapa4_observacoes']:
            etapa_data = result.get(etapa_key, {})
            for evid in ['json', 'minoristas', 'cupom']:
                alerta_key = f'{evid}_alerta'
                if alerta_key in etapa_data and etapa_data[alerta_key]:
                    all_alertas.append(etapa_data[alerta_key])
        
        if revisao_motivos:
            all_alertas.extend(revisao_motivos)
        if erro_motivo and not tem_obs_parceiro and not revisao_required:
            all_alertas.append(erro_motivo)
            
        result['alertas'] = list(set(all_alertas))

        return result

    def _to_builtin(self, value):
        """Convert Decimal and other types to builtin for JSON serialization."""
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, dict):
            return {k: self._to_builtin(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._to_builtin(v) for v in value]
        return value

    def _to_decimal(self, value: Any) -> Optional[Decimal]:
        """Safely convert value to Decimal."""
        if value is None or value == '':
            return None
        if isinstance(value, Decimal):
            return value
        s = str(value).strip()
        s = s.replace(',', '.')
        try:
            return Decimal(s)
        except Exception:
            return None

    def _round2(self, value: Any) -> float:
        dec = self._to_decimal(value)
        if dec is None:
            return 0.0
        return float(dec.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

    # ============================================================
    # ETAPA 1 — Itens
    # ============================================================
    def _validate_etapa1_itens(self, test_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Validate items against roteiro and partner JSON."""
        itens_parseados = test_dict.get('itens_parseados', [])
        pesaveis_esperados = test_dict.get('pesaveis_esperados', {})
        cupom = str(test_dict.get('cupom', '')).strip()
        teste_num = str(test_dict.get('teste', '')).strip()

        # Get partner JSON for this test
        partner_json = self.partner_jsons.get(cupom) or self.partner_jsons.get(teste_num)

        # Extract expected items from roteiro
        itens_esperados = []
        for item in itens_parseados:
            itens_esperados.append({
                'codigo': item.get('codigo'),
                'quantidade': item.get('quantidade'),
                'tipo': item.get('tipo'),
                'quantidade_esperada': item.get('quantidade_esperada', item.get('quantidade')),
                'cancelar_item': item.get('cancelar_item', False)
            })

        # Validate against partner JSON
        json_result = self._compare_itens_with_partner(itens_esperados, partner_json, 'json')
        minoristas_result = json_result  # Same JSON for now
        cupom_result = self._compare_itens_with_cupom(itens_esperados, test_dict)

        return {
            'json': json_result['status'],
            'json_motivo': json_result['motivo'],
            'minoristas': minoristas_result['status'],
            'cupom': cupom_result['status'],
            'json_alerta': json_result.get('alerta'),
        }

    def _compare_itens_with_partner(self, itens_esperados: List[Dict], partner_json: Dict, source: str) -> Dict[str, str]:
        """Compare expected items with partner JSON (movimiento.detalles)."""
        if not partner_json:
            return {'status': 'não avaliado', 'motivo': 'JSON do parceiro ausente', 'alerta': None}
        
        try:
            detalles = partner_json.get('movimiento', {}).get('detalles', [])
            if not detalles and 'detalles' in partner_json:
                detalles = partner_json.get('detalles', [])
        except Exception:
            return {'status': 'ERRO', 'motivo': f'{source}: estrutura inválida', 'alerta': None}

        # Extract EAN + qty from partner JSON
        partner_items = []
        for det in detalles:
            ean = det.get('codigoBarras') or det.get('codigoArticulo') or ''
            qtd = det.get('cantidad') or det.get('quantidade') or 0
            if ean:
                partner_items.append((str(ean).strip(), float(qtd)))

        # Compare each expected item
        alertas = []
        for exp in itens_esperados:
            if exp.get('cancelar_item'):
                continue  # Cancelled items shouldn't appear in partner JSON
            
            exp_codigo = str(exp.get('codigo', '')).strip()
            exp_qtd = float(exp.get('quantidade_esperada', exp.get('quantidade', 0)))
            exp_tipo = exp.get('tipo', '')
            
            if exp_tipo == 'pesavel':
                # For pesável, find by PESABLE or similar
                found = False
                for p_ean, p_qtd in partner_items:
                    if p_ean.upper() in ['PESABLE', 'PESAVEL', '000562'] or exp_codigo.upper() == p_ean.upper():
                        diff = abs(p_qtd - exp_qtd)
                        if diff > self.tolerance:
                            return {'status': 'ERRO', 'motivo': f'{source}: Pesável qtd divergente - roteiro {exp_qtd} vs parceiro {p_qtd}', 'alerta': f'Peso divergente: {diff:.3f}'}
                        found = True
                        break
                if not found:
                    alertas.append(f'{source}: Pesável {exp_codigo} não encontrado no parceiro')
            else:
                # Regular EAN item
                found = False
                for p_ean, p_qtd in partner_items:
                    if exp_codigo == p_ean:
                        if abs(p_qtd - exp_qtd) > self.tolerance:
                            return {'status': 'ERRO', 'motivo': f'{source}: Item {exp_codigo} qtd divergente - roteiro {exp_qtd} vs parceiro {p_qtd}', 'alerta': f'Qtd divergente item {exp_codigo}'}
                        found = True
                        break
                if not found:
                    # Check if it's a cancelamento item that should NOT appear
                    alertas.append(f'{source}: Item {exp_codigo} não encontrado no parceiro')

        if alertas:
            return {'status': 'REVISAO', 'motivo': '; '.join(alertas), 'alerta': '; '.join(alertas)}
        return {'status': 'OK', 'motivo': 'Itens conferem com parceiro', 'alerta': None}

    def _compare_itens_with_cupom(self, itens_esperados: List[Dict], test_dict: Dict) -> Dict[str, str]:
        """Compare with cupom fiscal data (from reader's json/minoristas fields)."""
        # For now, use the same partner JSON logic since cupom data comes from audit export
        # In future, could parse actual PDF cupom
        cupom_json_str = test_dict.get('json', '')
        if cupom_json_str and isinstance(cupom_json_str, str) and cupom_json_str.strip():
            try:
                cupom_json = json.loads(cupom_json_str)
                return self._compare_itens_with_partner(itens_esperados, cupom_json, 'cupom')
            except Exception:
                pass
        return {'status': 'não avaliado', 'motivo': 'Cupom fiscal não disponível', 'alerta': None}