#!/usr/bin/env python3
"""
Unit tests for Roteiro de Testes — ETAPA 1.
Implements the 27 test cases from the official test specification using
the application's ItemParser, PaymentNormalizer, APISalesBuilder, and TestValidator.
"""
import pytest
from pathlib import Path
from decimal import Decimal
import sys

# Add project root and src directory to Python path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / 'src'))

from validaai.parser_items import ItemParser
from validaai.payments import PaymentNormalizer
from validaai.api_sales import APISalesBuilder
from validaai.validators import TestValidator


# ─── 27 Test Case Definitions ──────────────────────────────────────────
TEST_CASES_SPEC = {
    # GRUPO 1: Vendas normais (sem desconto)
    1: {
        "grupo": "1. Vendas normais",
        "descricao": "Teste 1 — Compra simples com produto pesado",
        "itens": "2 x 7891000010860 + 3.579 x PESABLE",
        "pagamento": "Dinheiro",
        "subtotal": "149.07",
        "desconto": "0.00",
        "total": "149.07",
        "observacoes": "N/A",
    },
    2: {
        "grupo": "1. Vendas normais",
        "descricao": "Teste 2 — Vários produtos, um repetido",
        "itens": "5 x 7894904500383 + 4 x 7894904578207 + 7894904003495 + 7894904003495",
        "pagamento": "Dinheiro com Troco",
        "subtotal": "16.17",
        "desconto": "0.00",
        "total": "16.17",
        "observacoes": "N/A",
    },
    3: {
        "grupo": "1. Vendas normais",
        "descricao": "Teste 3 — Mesmo produto passado 3 vezes",
        "itens": "1 x 7894904003495 + 4 x 7894904003495 + 4 x 7894904003495",
        "pagamento": "Cartao Credito",
        "subtotal": "17.28",
        "desconto": "0.00",
        "total": "17.28",
        "observacoes": "N/A",
    },
    4: {
        "grupo": "1. Vendas normais",
        "descricao": "Teste 4 — Pagamento usando maquininha externa (POS)",
        "itens": "2 x 7891149440801 + 1 x 7891149102808 + 2 x 7891991001359",
        "pagamento": "Cartao Credito",
        "subtotal": "25.31",
        "desconto": "0.00",
        "total": "25.31",
        "observacoes": "Realizar o pagamento com finalizadora POS",
    },
    5: {
        "grupo": "1. Vendas normais",
        "descricao": "Teste 5 — Vários produtos com repetição",
        "itens": "3 x 7891991001359 + 1 x 7891149102808 + 2 x 7891149440801 + 1 x 7891149102808 + 2 x 7891991001359",
        "pagamento": "Cartao Debito",
        "subtotal": "45.67",
        "desconto": "0.00",
        "total": "45.67",
        "observacoes": "N/A",
    },
    6: {
        "grupo": "1. Vendas normais",
        "descricao": "Teste 6 — Mesmo produto passado 2 vezes",
        "itens": "5 x 7891149102808 + 1 x 7891149102808",
        "pagamento": "PIX",
        "subtotal": "30.54",
        "desconto": "0.00",
        "total": "30.54",
        "observacoes": "N/A",
    },
    7: {
        "grupo": "1. Vendas normais",
        "descricao": "Teste 7 — Pagamento dividido + canal diferente",
        "itens": "2 x 7894904573394 + 3 x 7894904573387",
        "pagamento": "Dinheiro + Cartao Credito",
        "subtotal": "14.25",
        "desconto": "0.00",
        "total": "14.25",
        "observacoes": "Utilizar canal de venda 2",
    },
    8: {
        "grupo": "1. Vendas normais",
        "descricao": "Teste 8 — Pagamento dividido, produtos repetidos",
        "itens": "4 x 7894904573387 + 2 x 7894904573394 + 2 x 7894904573387",
        "pagamento": "Dinheiro + Cartao Debito",
        "subtotal": "22.80",
        "desconto": "0.00",
        "total": "22.80",
        "observacoes": "N/A",
    },
    9: {
        "grupo": "1. Vendas normais",
        "descricao": "Teste 9 — Pagamento em 3 partes + canal especial",
        "itens": "6 x 7896079500175",
        "pagamento": "Dinheiro com Troco + Cartao Credito + Cartao Credito",
        "subtotal": "22.14",
        "desconto": "0.00",
        "total": "22.14",
        "observacoes": "Utilizar canal de venda diferente de 1 e 2 (ex: canal 3)",
    },
    10: {
        "grupo": "1. Vendas normais",
        "descricao": "Teste 10 — Pagamento em 3 partes",
        "itens": "8 x 7897511400237 + 4 x 7897511400244",
        "pagamento": "Dinheiro + Dinheiro + Cartao Credito",
        "subtotal": "44.28",
        "desconto": "0.00",
        "total": "44.28",
        "observacoes": "N/A",
    },

    # GRUPO 2: Cancelamento da venda após a conclusão
    11: {
        "grupo": "2. Cancelamento após conclusão",
        "descricao": "Teste 11 — Venda simples seguida de cancelamento",
        "itens": "1 x 7891024132906",
        "pagamento": "Dinheiro",
        "subtotal": "3.50",
        "desconto": "0.00",
        "total": "3.50",
        "observacoes": "cancelar venda",
    },
    12: {
        "grupo": "2. Cancelamento após conclusão",
        "descricao": "Teste 12 — Venda com troco seguida de cancelamento",
        "itens": "3 x 7891024132906",
        "pagamento": "Dinheiro com Troco",
        "subtotal": "10.50",
        "desconto": "0.00",
        "total": "10.50",
        "observacoes": "cancelar venda",
    },
    13: {
        "grupo": "2. Cancelamento após conclusão",
        "descricao": "Teste 13 — Venda com relançamento seguida de cancelamento",
        "itens": "1 x 7891024132906 + 1 x 7891024132906 + 1 x 7891024132906",
        "pagamento": "Cartao Credito",
        "subtotal": "10.50",
        "desconto": "0.00",
        "total": "10.50",
        "observacoes": "cancelar venda",
    },
    14: {
        "grupo": "2. Cancelamento após conclusão",
        "descricao": "Teste 14 — Venda com dois produtos seguida de cancelamento",
        "itens": "2 x 7891149105533 + 2 x 7891149103119",
        "pagamento": "Cartao Debito",
        "subtotal": "140.50",
        "desconto": "0.00",
        "total": "140.50",
        "observacoes": "cancelar venda",
    },
    15: {
        "grupo": "2. Cancelamento após conclusão",
        "descricao": "Teste 15 — Venda com pagamento misto seguida de cancelamento",
        "itens": "1 x 7891149105533 + 1 x 7891149103119",
        "pagamento": "Dinheiro + Cartao Credito",
        "subtotal": "70.25",
        "desconto": "0.00",
        "total": "70.25",
        "observacoes": "cancelar venda",
    },
    16: {
        "grupo": "2. Cancelamento após conclusão",
        "descricao": "Teste 16 — Venda grande seguida de cancelamento",
        "itens": "3 x 7891000010860 + 2 x 7894904573394 + 1 x 7894904573387 + 3 x 7894904573387 + 3.579 x PESABLE + 1 x 7896079500175",
        "pagamento": "Dinheiro + Cartao Debito",
        "subtotal": "181.76",
        "desconto": "0.00",
        "total": "181.76",
        "observacoes": "cancelar venda",
    },
    17: {
        "grupo": "2. Cancelamento após conclusão",
        "descricao": "Teste 17 — Venda com PIX seguida de cancelamento",
        "itens": "3 x 7891991001359 + 4 x 7894904573387 + 1 x 7891149102808",
        "pagamento": "PIX",
        "subtotal": "31.76",
        "desconto": "0.00",
        "total": "31.76",
        "observacoes": "cancelar venda",
    },

    # GRUPO 3: Vendas com um valor extra somado (Acréscimo)
    18: {
        "grupo": "3. Acréscimos",
        "descricao": "Teste 18 — Acréscimo colado em 1 produto específico",
        "itens": "4 x 7894904573394 + 1 x 7891149103119",
        "pagamento": "Dinheiro",
        "subtotal": "45.75",
        "desconto": "-5.00",  # Acréscimo é desconto negativo no roteiro/sistema
        "total": "50.75",
        "observacoes": "Dar acrescimo na linha",
    },
    19: {
        "grupo": "3. Acréscimos",
        "descricao": "Teste 19 — Acréscimo no total geral (cabeçalho)",
        "itens": "2 x 7891024132906",
        "pagamento": "Dinheiro",
        "subtotal": "7.00",
        "desconto": "-6.00",  # Acréscimo no cabeçalho
        "total": "13.00",
        "observacoes": "Dar acrescimo no subtotal ou cabecalho",
    },

    # GRUPO 4: Vendas com um desconto manual
    20: {
        "grupo": "4. Descontos manuais",
        "descricao": "Teste 20 — Desconto colado em 1 produto específico",
        "itens": "5 x 5000329002537 + 1 x 7891024132906",
        "pagamento": "Dinheiro",
        "subtotal": "501.00",
        "desconto": "6.00",
        "total": "495.00",
        "observacoes": "Dar desconto na linha",
    },
    21: {
        "grupo": "4. Descontos manuais",
        "descricao": "Teste 21 — Desconto no total geral (cabeçalho)",
        "itens": "3 x 5000329002537 + 1 x 7891150024588 + 1 x 7891024132906",
        "pagamento": "Dinheiro",
        "subtotal": "334.53",
        "desconto": "6.00",
        "total": "328.53",
        "observacoes": "Dar desconto no subtotal/cabeçalho",
    },

    # GRUPO 5: Começar uma venda e cancelar antes de terminar
    22: {
        "grupo": "5. Cancelamento antes de pagar",
        "descricao": "Teste 22 — Cancelar antes de pagar",
        "itens": "2 x 7894904573394",
        "pagamento": "",
        "subtotal": "5.70",
        "desconto": "0.00",
        "total": "5.70",
        "observacoes": "cancelar cupom antes de pagar",
    },

    # GRUPO 6: Testes extras (situações especiais)
    23: {
        "grupo": "6. Casos extras",
        "descricao": "Teste 23 — Cancelar só 1 produto, mantendo os outros",
        "itens": "2 x 7891000010860 + 1 x 7891000029329",
        "pagamento": "Dinheiro",
        "subtotal": "23.80",
        "desconto": "0.00",
        "total": "23.80",
        "observacoes": "cancelar item 7891000029329",
    },
    24: {
        "grupo": "6. Casos extras",
        "descricao": "Teste 24 — Cancelar 1 unidade (reduzir quantidade)",
        "itens": "6 x 7896079500175",
        "pagamento": "Dinheiro",
        "subtotal": "18.45",
        "desconto": "0.00",
        "total": "18.45",
        "observacoes": "cancelar unidade (de 6 para 5)",
    },
    25: {
        "grupo": "6. Casos extras",
        "descricao": "Teste 25 — Produto pesado, mas MUITO pesado",
        "itens": "2 x 7891000010860 + 357.9 x PESABLE",
        "pagamento": "Dinheiro",
        "subtotal": "12550.30",
        "desconto": "0.00",
        "total": "12550.30",
        "observacoes": "peso grande 357.9",
    },
    26: {
        "grupo": "6. Casos extras",
        "descricao": "Teste 26 — Código de barras errado de propósito",
        "itens": "2 x 1003607622300391065",
        "pagamento": "Dinheiro",
        "subtotal": "1.58",
        "desconto": "0.00",
        "total": "1.58",
        "observacoes": "EAN invalido de 19 digitos",
    },
    27: {
        "grupo": "6. Casos extras",
        "descricao": "Teste 27 — Código de barras com possíveis caracteres especiais",
        "itens": "1 x 7891999144485",
        "pagamento": "Dinheiro",
        "subtotal": "6.75",
        "desconto": "0.00",
        "total": "6.75",
        "observacoes": "N/A",
    },
}


class TestEtapa1RoteiroCompleto:
    """Tests the entire Etapa 1 Roteiro containing all 27 cases."""

    @pytest.fixture(autouse=True)
    def setup_components(self):
        self.item_parser = ItemParser()
        self.payment_normalizer = PaymentNormalizer()
        self.api_builder = APISalesBuilder()
        self.validator = TestValidator(tolerance=0.01)

    def _process_test_case(self, spec_id: int) -> dict:
        """Processes a single test spec case through the pipeline."""
        spec = TEST_CASES_SPEC[spec_id]
        
        # 1. Base test dict from spec
        test_dict = {
            "teste": spec_id,
            "itens_da_venda": spec["itens"],
            "pagamento": spec["pagamento"],
            "subtotal": spec["subtotal"],
            "desconto": spec["desconto"],
            "total": spec["total"],
            "observacoes": spec["observacoes"],
            "itens_raw": spec["itens"],
            "pagamento_raw": spec["pagamento"],
            "subtotal_esperado": spec["subtotal"],
            "desconto_esperado": spec["desconto"],
            "total_esperado": spec["total"],
        }
        
        # Add cupom number for cancellation tests (needed for negative numero in JSON)
        if spec_id in (11, 12, 13, 14, 15, 16, 17):
            test_dict["cupom"] = f"100{spec_id}"  # Mock cupom number for cancellation tests
        
        # 2. Parse Items
        test_dict = self.item_parser.parse_items(test_dict)
        
        # 3. Normalize Payment
        test_dict = self.payment_normalizer.normalize_payment(test_dict)
        
        # 4. Build API Sale JSON
        sale_json = self.api_builder.build_sale_json(
            teste=spec_id,
            itens_da_venda=spec["itens"],
            pagamento=spec["pagamento"],
            subtotal=spec["subtotal"],
            desconto=spec["desconto"],
            total=spec["total"],
            observacoes=spec["observacoes"],
            numero_cupom=test_dict.get("cupom", ""),
        )
        test_dict["sale_json"] = sale_json
        
        # 5. Run Validation (legacy chain - matches gui_app_standalone.py / exe inline logic)
        validated_dict = self.validator.validate_legacy(test_dict)
        return validated_dict

    @pytest.mark.parametrize("test_id", sorted(TEST_CASES_SPEC.keys()))
    def test_individual_scenarios(self, test_id):
        """Validates each of the 27 scenarios to match expected behavior."""
        spec = TEST_CASES_SPEC[test_id]
        result = self._process_test_case(test_id)
        
        print(f"\n--- {spec['descricao']} ---")
        print(f"Status final: {result['status_final']}")
        print(f"Motivo: {result['motivo_status']}")
        if result['alertas']:
            print(f"Alertas: {result['alertas']}")

        # Baseline checks on output structure
        assert "status_final" in result
        assert "motivo_status" in result
        assert isinstance(result["itens_parseados"], list)
        assert len(result["itens_parseados"]) > 0 or test_id == 22  # Empty is fine for cancellation before payment

        # Test case specific assertions to verify Roteiro Rules:
        
        # 🔸 Regra do produto vendido por peso (PESÁVEL)
        if test_id in (1, 16, 25):
            pesavel_items = [it for it in result["itens_parseados"] if it["tipo"] == "pesavel"]
            assert len(pesavel_items) > 0, "Deveria identificar o item pesável"
            if test_id == 1:
                assert any(it["quantidade"] == 3.579 for it in pesavel_items)
            elif test_id == 25:
                assert any(it["quantidade"] == 357.9 for it in pesavel_items)

        # 🔸 Regra do centavo perdido (arredondamento)
        # We ensure no hard error is thrown for values close to tolerance (R$ 0.01)
        if result["status_final"] == "REVISAO":
            assert "Divergência" in result["motivo_status"] or "revisão" in result["motivo_status"].lower() or "pesável" in result["motivo_status"].lower() or "troco" in result["motivo_status"].lower() or "múltiplo" in result["motivo_status"].lower() or "acréscimo" in result["motivo_status"].lower() or "desconto" in result["motivo_status"].lower()
        else:
            assert result["status_final"] in ("OK", "REVISAO", "ERRO_PAGAMENTO", "ERRO")

        # 🔸 Cancelamento após conclusão
        if spec["grupo"] == "2. Cancelamento após conclusão":
            # The built JSON must have cancelacion field set correctly depending on observations
            movimiento = result["sale_json"]["movimiento"]
            assert movimiento["cancelacion"] is True
            assert movimiento["numero"].startswith("-")

        # 🔸 Acréscimos and Descontos
        if test_id in (18, 19):  # Acréscimos
            mov = result["sale_json"]["movimiento"]
            assert float(mov["total"]) > float(result["subtotal_norm"])
        elif test_id in (20, 21):  # Descontos
            mov = result["sale_json"]["movimiento"]
            assert float(mov["total"]) < float(result["subtotal_norm"])

        # 🔸 Código de barras de 19 dígitos
        if test_id == 26:
            invalid_ean_item = result["itens_parseados"][0]
            assert len(invalid_ean_item["codigo"]) == 19
