"""
Unit tests for payment label mapping (codigoTipoPago -> readable labels).
P0 Priority: Map codigoTipoPago → readable labels in logs/spreadsheet.
"""
import pytest
from validaai.api_sales import APISalesBuilder


class TestPaymentLabelMapping:
    """Test payment code to label mapping."""

    @pytest.fixture
    def api_builder(self):
        return APISalesBuilder()

    def test_codigo_tipo_pago_to_label_mapping(self):
        """Test that all known payment codes map to correct labels."""
        # Expected mapping based on P0 requirement
        expected_mapping = {
            9: "Dinheiro",
            10: "Crédito",
            13: "Débito",
            14: "PIX",
            15: "Finalizadora",
        }
        
        # Test each mapping
        for code, expected_label in expected_mapping.items():
            label = APISalesBuilder._codigo_to_label(code)
            assert label == expected_label, f"Code {code} should map to '{expected_label}', got '{label}'"

    def test_unknown_code_returns_unknown(self):
        """Test that unknown codes return a sensible default."""
        label = APISalesBuilder._codigo_to_label(999)
        assert label == "Desconhecido (999)" or "Desconhecido" in label

    def test_detalle_finalizadora_mapping(self):
        """Test that payment types map to correct detalleFinalizadora."""
        # This tests the existing DETALLE_FINALIZADORA mapping
        api = APISalesBuilder()
        
        test_cases = [
            ("dinheiro", "DINHEIRO"),
            ("dinheiro com troco", "DINHEIRO"),
            ("cartao credito", "CARTAO_CREDITO"),
            ("cartao débito", "CARTAO_DEBITO"),
            ("pix", "PIX"),
            ("qr", "PIX"),
            ("cheque", "CHEQUE"),
            ("vale", "VALE"),
            ("finalizadora", "FINALIZADORA"),
        ]
        
        for input_val, expected in test_cases:
            result = api._detalle_finalizadora(input_val)
            assert result == expected, f"Input '{input_val}' should map to '{expected}', got '{result}'"

    def test_codigo_pagamento_mapping(self):
        """Test payment string to code mapping."""
        api = APISalesBuilder()
        
        test_cases = [
            ("dinheiro", 9),
            ("dinheiro com troco", 9),
            ("cartao credito", 10),
            ("cartao débito", 13),
            ("pix", 14),
            ("finalizadora", 15),
        ]
        
        for input_val, expected_code in test_cases:
            code = api._codigo_pagamento(input_val)
            assert code == expected_code, f"Input '{input_val}' should map to code {expected_code}, got {code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])