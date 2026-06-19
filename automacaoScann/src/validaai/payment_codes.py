"""
Centralized mapping for codigoTipoPago codes to readable labels.
Used across the codebase for logs, spreadsheets, and UI display.
"""

# Mapping from codigoTipoPago to human-readable payment method description
CODIGO_TIPO_PAGO_LABELS = {
    9: 'Dinheiro',
    10: 'Crédito',
    11: 'Cheque',
    12: 'Vale',
    13: 'Débito',
    14: 'PIX',
    15: 'Finalizadora',
}

# Reverse mapping for lookup by label (if needed)
LABEL_TO_CODIGO_TIPO_PAGO = {v: k for k, v in CODIGO_TIPO_PAGO_LABELS.items()}

# Codes that represent card payments (require bin, autorizacao, etc.)
CARD_PAYMENT_CODES = {10, 13}

# Codes that require QR code provider info (PIX)
PIX_PAYMENT_CODES = {14}


def get_payment_label(codigo_tipo_pago: int) -> str:
    """
    Get human-readable label for a codigoTipoPago.
    
    Args:
        codigo_tipo_pago: The payment type code (e.g., 9, 10, 13, 14, 15)
        
    Returns:
        Readable label (e.g., 'Dinheiro', 'Crédito', 'Débito', 'PIX', 'Finalizadora')
        or 'Desconhecido({code})' if code not in mapping.
    """
    if codigo_tipo_pago is None:
        return 'N/A'
    return CODIGO_TIPO_PAGO_LABELS.get(codigo_tipo_pago, f'Desconhecido({codigo_tipo_pago})')


def get_payment_labels(codigos: list[int]) -> list[str]:
    """
    Get labels for a list of payment codes.
    
    Args:
        codigos: List of codigoTipoPago values
        
    Returns:
        List of readable labels
    """
    return [get_payment_label(c) for c in codigos]


def format_pagamentos_for_log(pagamentos: list[dict]) -> str:
    """
    Format a list of pagamento dicts for logging/spreadsheet display.
    
    Args:
        pagamentos: List of payment dicts with 'codigoTipoPago' and optionally 'importe'
        
    Returns:
        Formatted string like "Dinheiro (R$ 50,00) + Crédito (R$ 100,00)"
    """
    parts = []
    for p in pagamentos:
        codigo = p.get('codigoTipoPago')
        importe = p.get('importe', 0)
        label = get_payment_label(codigo)
        # Format number with Brazilian convention: 1234.56 -> 1.234,56
        if isinstance(importe, (int, float)):
            importe_str = f'{importe:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
        else:
            importe_str = str(importe)
        parts.append(f'{label} (R$ {importe_str})')
    return ' + '.join(parts)


def is_card_payment(codigo_tipo_pago: int) -> bool:
    """Check if payment code represents a card payment (crédito/débito)."""
    return codigo_tipo_pago in CARD_PAYMENT_CODES


def is_pix_payment(codigo_tipo_pago: int) -> bool:
    """Check if payment code represents PIX."""
    return codigo_tipo_pago in PIX_PAYMENT_CODES