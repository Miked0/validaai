"""
validaai-core - Core validation library for PDV test scripts.
"""

from .reader import TestScriptReader
from .parser_items import ItemParser
from .payments import PaymentNormalizer
from .validators import TestValidator
from .exporters import ResultExporter
from .api_sales import APISalesBuilder
from .payment_codes import (
    CODIGO_TIPO_PAGO_LABELS,
    get_payment_label,
    get_payment_labels,
    format_pagamentos_for_log,
    is_card_payment,
    is_pix_payment,
)

__version__ = "2.0.0"
__author__ = "ValidaAI Team"
API_SALES_AVAILABLE = True

__all__ = [
    "TestScriptReader",
    "ItemParser", 
    "PaymentNormalizer",
    "TestValidator",
    "ResultExporter",
    "APISalesBuilder",
    "API_SALES_AVAILABLE",
    "CODIGO_TIPO_PAGO_LABELS",
    "get_payment_label",
    "get_payment_labels",
    "format_pagamentos_for_log",
    "is_card_payment",
    "is_pix_payment",
    "__version__",
]