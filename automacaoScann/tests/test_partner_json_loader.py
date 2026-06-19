"""
Unit tests for partner JSON loader - filtering 'nan' key.
P2 Priority: Filter 'nan' key in loader de partner JSONs.
"""
import pytest
import pandas as pd
from pathlib import Path
from validaai.api_sales import APISalesBuilder


class TestPartnerJSONLoader:
    """Test partner JSON loading and filtering."""

    @pytest.fixture
    def api_builder(self):
        return APISalesBuilder()

    def test_load_partner_jsons_filters_nan_key(self, tmp_path):
        """Test that 'nan' key is filtered out from loaded JSONs."""
        excel_file = tmp_path / "test_audit.xlsx"
        
        # Create test data with various invalid keys
        data = {
            'Número cupom': ['1', '2', float('nan'), '4', 'nan', 'None', ''],
            'Request': [
                self._json(1, 9),
                self._json(2, 10),
                self._json(3, 13),
                self._json(4, 14),
                self._json(5, 15),
                self._json(6, 9),
                self._json(7, 10),
            ]
        }
        df = pd.DataFrame(data)
        df.to_excel(excel_file, index=False)

        api = APISalesBuilder()
        partner_jsons = api._load_partner_jsons(str(excel_file))
        
        keys = list(partner_jsons.keys())
        invalid_keys = [k for k in keys if k.lower() in ['nan', 'none', '']]
        
        # Invalid keys should be filtered out
        assert len(invalid_keys) == 0, f"Invalid keys found: {invalid_keys}"
        
        # Should have at least 3 valid keys
        valid_keys = [k for k in keys if k.lower() not in ['nan', 'none', '']]
        assert len(valid_keys) >= 3, f"Expected at least 3 valid keys, got {len(valid_keys)}: {valid_keys}"

    def test_load_partner_jsons_uses_numero_cupom(self, tmp_path):
        """Test that loader uses 'Número cupom' column as key (not 'Id request')."""
        excel_file = tmp_path / "test_audit.xlsx"
        data = {
            'Número cupom': ['1', '2', '3'],
            'Id request': ['999', '888', '777'],
            'Request': [
                '{"numero": "1", "pagos": [{"codigoTipoPago": 9}]}',
                '{"numero": "2", "pagos": [{"codigoTipoPago": 10}]}',
                '{"numero": "3", "pagos": [{"codigoTipoPago": 13}]}',
            ]
        }
        df = pd.DataFrame(data)
        df.to_excel(excel_file, index=False)

        api = APISalesBuilder()
        partner_jsons = api._load_partner_jsons(str(excel_file))
        
        keys = list(partner_jsons.keys())
        assert '1' in keys, f"Expected key '1' in {keys}"
        assert '2' in keys, f"Expected key '2' in {keys}"
        assert '3' in keys, f"Expected key '3' in {keys}"
        assert '999' not in keys, f"Should not use 'Id request' as key: {keys}"
        assert '888' not in keys, f"Should not use 'Id request' as key: {keys}"
        assert '777' not in keys, f"Should not use 'Id request' as key: {keys}"

    def test_load_partner_jsons_prefers_request_column(self, tmp_path):
        """Test that loader prefers 'Request' column over 'Id request'."""
        excel_file = tmp_path / "test_audit.xlsx"
        data = {
            'Número cupom': ['1'],
            'Request': ['{"numero": "1", "pagos": [{"codigoTipoPago": 9}]}'],
            'Id request': ['999'],
        }
        df = pd.DataFrame(data)
        df.to_excel(excel_file, index=False)

        api = APISalesBuilder()
        partner_jsons = api._load_partner_jsons(str(excel_file))
        
        assert '1' in partner_jsons
        assert partner_jsons['1'].get('numero') == '1'
        assert partner_jsons['1'].get('pagos')[0].get('codigoTipoPago') == 9

    @staticmethod
    def _json(numero, codigo):
        return f'{{"numero": "{numero}", "pagos": [{{"codigoTipoPago": {codigo}}}]}}'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])