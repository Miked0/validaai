#!/usr/bin/env python3
"""
API Sales Builder and Validator (MVP)
"""
import json
import re
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional


class APISalesBuilder:
    CODIGO_MOEDA = "986"
    COTIZACION = 1.00

    DETALLE_FINALIZADORA = {
        'dinheiro': 'DINHEIRO',
        'dinheiro com troco': 'DINHEIRO',
        'cartao credito': 'CARTAO_CREDITO',
        'cartao crédito': 'CARTAO_CREDITO',
        'cartao debito': 'CARTAO_DEBITO',
        'cartao débito': 'CARTAO_DEBITO',
        'pix': 'PIX',
        'qr': 'PIX',
        'pix/qr': 'PIX',
        'cheque': 'CHEQUE',
        'vale': 'VALE',
        'finalizadora': 'FINALIZADORA',
    }

    def _detalle_finalizadora(self, pagamento_raw: str) -> str:
        if not pagamento_raw:
            return ''
        low = str(pagamento_raw).lower().strip()
        return self.DETALLE_FINALIZADORA.get(low, low.upper())

    PAGAMENTO_CODIGO = {
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
        'finalizadora': 15,
    }

    PAGAMENTO_CODIGO = {
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
        'finalizadora': 15,
    }

    # P0: Mapping from codigoTipoPago to human-readable labels
    CODIGO_TIPO_PAGO_LABEL = {
        9: "Dinheiro",
        10: "Crédito",
        11: "Cheque",
        12: "Vale",
        13: "Débito",
        14: "PIX",
        15: "Finalizadora",
    }

    @classmethod
    def _codigo_to_label(cls, codigo: int) -> str:
        """P0: Map codigoTipoPago to human-readable label for logs/spreadsheet."""
        return cls.CODIGO_TIPO_PAGO_LABEL.get(codigo, f"Desconhecido ({codigo})")

    CODIGO_INTERNO_POR_EAN = {
        '7896079500175': '123',
        '7896079500151': '123',
        '7891149103119': '124',
        '7891149103102': '124',
        '7891991294959': '125',
        '7891991294942': '125',
    }

    def _to_decimal(self, value: Any) -> Optional[Decimal]:
        if value is None or value == '':
            return None
        if isinstance(value, Decimal):
            return value
        s = str(value).strip()
        s = re.sub(r'[^0-9,.\-]', '', s)
        if s.count('.') > 1:
            s = s.replace('.', '')
        if s.count(',') > 1:
            s = s.replace(',', '')
        if ',' in s and '.' in s:
            s = s.replace('.', '').replace(',', '.')
        elif ',' in s:
            s = s.replace(',', '.')
        if s in ('', '.', '-', '-.', ',-'):
            return None
        try:
            return Decimal(s)
        except Exception:
            return None

    def _round2(self, value: Any) -> float:
        dec = self._to_decimal(value)
        if dec is None:
            return 0.0
        return float(dec.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

    def _codigo_pagamento(self, pagamento_raw: str) -> Optional[int]:
        if not pagamento_raw:
            return None
        low = str(pagamento_raw).lower().strip()
        if low in self.PAGAMENTO_CODIGO:
            return self.PAGAMENTO_CODIGO[low]
        for key, cod in self.PAGAMENTO_CODIGO.items():
            if key in low:
                return cod
        return None

    def _eh_cancelamento(self, observacoes: str) -> bool:
        if not observacoes:
            return False
        return 'cancelar venda' in str(observacoes).lower()

    def _canal_venda(self, observacoes: str, pagamento: str) -> Dict[str, Any]:
        texto = ' '.join(filter(None, [str(observacoes or ''), str(pagamento or '')])).lower()
        if 'canal de venda 2' in texto or 'canal 2' in texto:
            return {'codigoCanalVenta': 2, 'descripcionCanalVenta': 'E-COMMERCE'}
        if ('diferente de 1 e 2' in texto or
                'canal diferente de 1' in texto or
                'canal de venda diferente' in texto):
            return {'codigoCanalVenta': 3, 'descripcionCanalVenta': 'OUTROS'}
        return {'codigoCanalVenta': 1, 'descripcionCanalVenta': 'VENDA NA LOJA'}

    LIMITE_PROMOCIONES_POR_TICKET = {
        'ADICIONAL_REGALO': 1,
        'ADICIONAL_DESCUENTO': 1,
        'DESCUENTO_FIJO': 1,
        'DESCUENTO_VARIABLE': 2,
        'LLEVA_PAGA': 1,
        'PRECIO_FIJO': 1,
    }

    def _beneficios_count(self, tipo_promo: str) -> int:
        return self.LIMITE_PROMOCIONES_POR_TICKET.get(tipo_promo.strip().upper(), 1)

    def _tem_promo(self, tipo_promo: str) -> bool:
        return bool(str(tipo_promo or '').strip())

    def _extrair_bin(self, numero_cupom: str) -> str | None:
        numero = str(numero_cupom or '').strip()
        if not numero:
            return None
        apenas_digitos = ''.join(ch for ch in numero if ch.isdigit())
        if len(apenas_digitos) >= 8:
            return apenas_digitos[:8]
        if len(apenas_digitos) >= 6:
            return apenas_digitos[:6]
        return None

    def _parse_itens(self, itens_raw: str) -> List[Dict[str, Any]]:
        if not itens_raw or not isinstance(itens_raw, str):
            return []

        partes = [p.strip() for p in itens_raw.split('+') if p.strip()]
        detalhes = []
        for parte in partes:
            m = re.match(r'^(\d+(?:\.\d+)?)\s*x\s*(.+)$', parte.strip())
            if m:
                quantidade = float(m.group(1))
                codigo = m.group(2).strip()
            else:
                quantidade = 1.0
                codigo = parte.strip()

            if not codigo:
                continue

            codigo_limpo = codigo.strip()
            codigo_interno = self.CODIGO_INTERNO_POR_EAN.get(codigo_limpo, codigo_limpo)

            detalhes.append({
                'codigoBarras': codigo_limpo,
                'codigoArticulo': codigo_interno,
                'descripcionArticulo': '',
                'cantidad': quantidade,
                'importeUnitario': None,
                'impuesto': None,
                'importe': None,
                'descuento': None,
                'recargo': None,
                'datosExtra': {},
                '_tipo': self._classificar_item(codigo_limpo),
            })
        return detalhes

    def _classificar_item(self, codigo: str) -> str:
        codigo = codigo.upper().strip()
        if codigo in ('PESABLE', 'PESAVEL', 'WEIGHT', 'PESO'):
            return 'pesavel'
        if re.match(r'^\d{8,13}$', codigo):
            return 'ean'
        # fallback para códigos curtos/não-EAN usados em peso (ex.: '33')
        if re.match(r'^\d+$', codigo) and len(codigo) < 8:
            return 'pesavel'
        return 'outro'

    def build_sale_json(
        self,
        teste: Any,
        itens_da_venda: str,
        pagamento: str,
        subtotal: Any,
        desconto: Any,
        total: Any,
        observacoes: str = '',
        numero_cupom: str = '',
        is_cancelamento: Optional[bool] = None,
        data_venda: Optional[str] = None,
        tipo_promo: str = '',
        pagamentos: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:

        sub_dec = self._to_decimal(subtotal)
        desc_dec = self._to_decimal(desconto)
        tot_dec = self._to_decimal(total)

        if is_cancelamento is None:
            is_cancelamento = self._eh_cancelamento(observacoes)

        if data_venda is None:
            data_venda = datetime.now().isoformat()

        canal = self._canal_venda(observacoes, pagamento)
        itens_parseados = self._parse_itens(itens_da_venda)

        # Conserva valores do roteiro para itens; PESAVEL sem preço tabela não é inventado aqui.
        for item in itens_parseados:
            val = item.get('importe')
            if val is None:
                val = Decimal('0')
            item['importe'] = val
            item['importeUnitario'] = item.get('importeUnitario') or Decimal('0')
            item['impuesto'] = item.get('impuesto') or Decimal('0')
            item['descuento'] = item.get('descuento') or Decimal('0')
            item['recargo'] = item.get('recargo') or Decimal('0')

        # Parse pagamentos using provided list or fallback to single payment
        pagos = []
        if pagamentos:
            for p in pagamentos:
                codigo = p.get('codigo')
                raw = p.get('raw') or p.get('norm')
                if codigo is not None:
                    pago = {
                        'codigoTipoPago': int(codigo),
                        'codigoMoneda': int(self.CODIGO_MOEDA),
                        'importe': round(float(tot_dec), 2),  # Will be adjusted proportionally if needed
                        'cotizacion': 1.00,
                        'documentoCliente': '',
                        'bin': self._extrair_bin(numero_cupom) if codigo in (10, 13) and self._tem_promo(tipo_promo) else '',
                        'codigoTarjeta': '',
                        'numeroAutorizacao': '',
                        'ultimosDigitosTarjeta': '',
                        'detalleFinalizadora': self._detalle_finalizadora(raw),
                        'cuotas': 0,
                    }
                    if codigo == 14:
                        pago['codigoProveedorQR'] = 1
                        pago['codigoBanco'] = ''
                        pago['descripcionBanco'] = ''
                    pagos.append(pago)
        else:
            # Fallback: single payment from 'pagamento' string
            codigo_pago = self._codigo_pagamento(pagamento)
            if codigo_pago is not None:
                pago = {
                    'codigoTipoPago': int(codigo_pago),
                    'codigoMoneda': int(self.CODIGO_MOEDA),
                    'importe': round(float(tot_dec), 2),
                    'cotizacion': 1.00,
                    'documentoCliente': '',
                    'bin': self._extrair_bin(numero_cupom) if codigo_pago in (10, 13) and self._tem_promo(tipo_promo) else '',
                    'codigoTarjeta': '',
                    'numeroAutorizacao': '',
                    'ultimosDigitosTarjeta': '',
                    'detalleFinalizadora': self._detalle_finalizadora(pagamento),
                    'cuotas': 0,
                }
                if codigo_pago == 14:
                    pago['codigoProveedorQR'] = 1
                    pago['codigoBanco'] = ''
                    pago['descripcionBanco'] = ''
                pagos.append(pago)

        # Adjust importe per payment if multiple (split total proportionally)
        if len(pagos) > 1:
            # For now, just split equally - real implementation would need amounts from template
            split_val = round(float(tot_dec) / len(pagos), 2)
            for p in pagos:
                p['importe'] = split_val

        detalles = []
        for item in itens_parseados:
            extra = item.get('datosExtra')
            if isinstance(extra, dict):
                extra = json.dumps(extra, ensure_ascii=False) if extra else ''
            elif extra is None:
                extra = ''
            det = {
                'codigoArticulo': item['codigoArticulo'] or '',
                'codigoBarras': item['codigoBarras'] or '',
                'descripcionArticulo': item['descripcionArticulo'] or '',
                'cantidad': round(float(item['cantidad'] or 0), 2),
                'importeUnitario': round(float(item['importeUnitario'] or 0), 2),
                'importe': round(float(item['importe'] or 0), 2),
                'impuesto': round(float(item['impuesto'] or 0), 2),
                'descuento': round(float(item['descuento'] or 0), 2),
                'recargo': round(float(item['recargo'] or 0), 2),
                'datosExtra': extra,
            }
            detalles.append(det)

        numero = numero_cupom if numero_cupom else ''
        if is_cancelamento and numero and not numero.startswith('-'):
            numero = f'-{numero}'

        movimiento = {
            'fecha': data_venda,
            'numero': numero,
            'descuentoTotal': round(self._to_decimal(desc_dec) or 0, 2),
            'recargoTotal': 0.0,
            'codigoMoneda': int(self.CODIGO_MOEDA),
            'cotizacion': 1.00,
            'total': round(self._to_decimal(tot_dec) or 0, 2),
            'cancelacion': bool(is_cancelamento),
            'documentoCliente': '',
            'codigoCanalVenta': canal['codigoCanalVenta'],
            'descripcionCanalVenta': canal['descripcionCanalVenta'],
            'idCliente': '',
            'detalles': detalles,
            'pagos': pagos,
        }

        payload = {'movimiento': movimiento}
        return payload

    def validate_sale_json(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(payload, dict):
            return {'status': 'ERRO_JSON', 'motivo': 'JSON inválido', 'alertas': []}

        obrigatorios = [
            'fecha', 'numero', 'descuentoTotal', 'recargoTotal',
            'codigoMoneda', 'cotizacion', 'total', 'cancelacion',
            'detalles', 'pagos'
        ]
        erros = [f'Campo obrigatorio ausente: {c}' for c in obrigatorios if c not in payload]
        alertas = []

        if payload.get('codigoMoneda') != self.CODIGO_MOEDA:
            erros.append(f"codigoMoneda deve ser {self.CODIGO_MOEDA}")
        if payload.get('cotizacion') != self.COTIZACION:
            erros.append(f"cotizacion deve ser {self.COTIZACION}")

        for campo in ('descuentoTotal', 'recargoTotal', 'total'):
            val = payload.get(campo)
            if val is not None:
                s = str(val)
                if '.' in s:
                    dec = len(s.split('.')[1])
                    if dec > 2:
                        alertas.append(f'{campo} com mais de 2 casas decimais: {s}')

        if payload.get('cancelacion') is True and not str(payload.get('numero', '')).startswith('-'):
            erros.append('Cancelamento deve ter numero com hifen')

        detalles = payload.get('detalles', [])
        if not isinstance(detalles, list):
            erros.append('detalles nao e uma lista')
        else:
            for idx, det in enumerate(detalles):
                if not isinstance(det, dict):
                    erros.append(f'Item {idx} nao e um dicionario')
                    continue
                for campo in ('codigoArticulo', 'codigoBarras', 'cantidad'):
                    if campo not in det:
                        erros.append(f'Item {idx} sem {campo}')

        if erros:
            return {
                'status': 'ERRO_JSON',
                'motivo': '; '.join(erros),
                'alertas': alertas,
            }

        if alertas:
            return {
                'status': 'ALERTA_JSON',
                'motivo': 'Estrutura OK, mas com alertas',
                'alertas': alertas,
            }

        return {
            'status': 'OK',
            'motivo': 'JSON valido',
            'alertas': [],
        }

    def _load_partner_jsons(self, audit_file: str) -> Dict[str, Any]:
        """Carrega JSONs do parceiro do arquivo de export de auditoria (xlsx).
        Espera colunas: 'Teste' (ou 'Número cupom') e 'Request' (JSON do parceiro).
        Retorna dict mapeando teste -> JSON do parceiro.
        Procura em TODAS as abas do arquivo.
        """
        import pandas as pd
        import json
        
        jsons = {}
        total_parsed = 0
        
        # Ler todas as abas do arquivo
        xls = pd.ExcelFile(audit_file)
        
        for sheet_name in xls.sheet_names:
            try:
                df = pd.read_excel(audit_file, sheet_name=sheet_name, dtype=str)
                
                # Procurar colunas de teste/cupom - priorizar matches exatos
                test_col = None
                test_cols = [c for c in df.columns if c and ('teste' in c.lower() or 'cupom' in c.lower() or 'numero' in c.lower())]
                if test_cols:
                    # Priorizar colunas com nome mais específico
                    for preferred in ['Número cupom', 'Numero cupom', 'Teste', 'Teste', 'Numero', 'Numero cupom']:
                        if preferred in df.columns:
                            test_col = preferred
                            break
                        for c in test_cols:
                            if preferred.lower() in c.lower():
                                test_col = preferred
                                break
                    if test_col is None and test_cols:
                        test_col = test_cols[0]
                
                # Procurar coluna de request/json - priorizar 'Request' EXATO antes de qualquer outro
                request_col = None
                # PRIMEIRO: buscar coluna 'Request' exata (a que tem os JSONs)
                if 'Request' in df.columns:
                    request_col = 'Request'
                else:
                    # Fallback: buscar outras variações, MAS excluir 'Id request'
                    request_cols = [c for c in df.columns 
                                   if c and ('request' in c.lower() or 'json' in c.lower() or 'movimiento' in c.lower())
                                   and c.lower() != 'id request']  # EXCLUIR 'Id request'
                    if request_cols:
                        for preferred in ['Request JSON', 'Json Request', 'JSON', 'Json']:
                            for c in request_cols:
                                if preferred.lower() == c.lower():
                                    request_col = c
                                    break
                            if request_col:
                                break
                        if request_col is None:
                            request_col = request_cols[0]
                
                if not test_col or not request_col:
                    continue
                
                print(f"   Aba '{sheet_name}': colunas detectadas - Teste: '{test_col}', Request: '{request_col}'")
                
                parsed_count = 0
                for _, row in df.iterrows():
                    test_val = str(row.get(test_col, '')).strip()
                    request_val = str(row.get(request_col, '')).strip()
                    
                    # P2: Filter out 'nan' keys (from NaN cells)
                    if test_val.lower() in ['nan', 'none', '']:
                        continue
                    
                    if test_val and request_val and request_val not in ['nan', 'None', '']:
                        try:
                            parsed = json.loads(request_val)
                            jsons[test_val] = parsed
                            total_parsed += 1
                            parsed_count += 1
                        except Exception:
                            pass
                if total_parsed > 0:
                    print(f"   Aba '{sheet_name}': {total_parsed} JSONs válidos carregados")
            except Exception as e:
                print(f"   Erro ao processar aba '{sheet_name}': {e}")
        
        print(f"   Total de JSONs do parceiro carregados: {total_parsed}")
        if jsons:
            print(f"   Testes com JSON do parceiro: {sorted(jsons.keys())}")
        return jsons
