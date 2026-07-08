# Módulo: Payments (`src/validaai/payments.py`)

**Versão:** 2.1.0  
**Responsável:** ValidaAI Team  
**Status:** Produção

---

## 1. Objetivo do Módulo

Normalizar strings de pagamento brutas do roteiro em **códigos padrão da API 3.0 Scanntech**, detectar POS, canal de venda, pagamentos múltiplos e necessidades de BIN.

---

## 2. Responsabilidade Principal

| Responsabilidade | Detalhe |
|------------------|---------|
| **Mapeamento Pagamento → Código API** | `dinheiro`→9, `cartao credito`→10, `cartao debito`→13, `pix`→14, `vale`→12, `finalizadora`→15 |
| **Detecção POS** | Qualquer menção a cartão/PIX/terminal POS → `tem_pos=True` |
| **Canal de Venda** | `canal de venda 2`→2, `diferente de 1 e 2`→3, padrão→1 |
| **Pagamentos Múltiplos** | Split por `+`, `e`, vírgula → lista de pagamentos com códigos |
| **Detecção Cancelamentos** | `cancelar venda`, `cancelar antes de finalizar` |
| **Requisito BIN** | Cartão crédito/débito + promoção → `requires_bin=True` |

---

## 3. Funcionalidades Existentes

| Funcionalidade | Método | Saída Principal |
|----------------|--------|-----------------|
| `normalize_payment()` | Público | `pagamento_normalizado`, `codigo_tipo_pago`, `pagamentos[]`, `tem_pos`, `canal_venda`, `requires_bin`, `is_cancelamento_venda`, `is_cancelamento_antecipado` |
| `_normalize_payment_string()` | Privado | Core logic de parsing |

### Mapeamento de Pagamentos (`PAYMENT_MAPPING`)

| String (lowercase) | Código API | Label |
|--------------------|------------|-------|
| `dinheiro`, `dinheiro com troco` | 9 | Dinheiro |
| `cartao credito`, `cartao crédito` | 10 | Crédito |
| `cartao debito`, `cartao débito` | 13 | Débito |
| `pix`, `qr`, `pix/qr` | 14 | PIX |
| `cheque` | 11 | Cheque |
| `vale` | 12 | Vale (ticket refeição) |
| `finalizadora` | 15 | Finalizadora |

---

## 4. Dependências

### Internas
- Nenhuma

### Externas
| Dependência | Uso |
|-------------|-----|
| `re` (stdlib) | Split pagamentos múltiplos, detecção palavras-chave |
| `typing` | Type hints |

---

## 5. Módulos Relacionados

| Módulo | Relação | Dados |
|--------|---------|-------|
| `reader.py` | **Fornecedor** | Fornece `pagamento`, `observacoes` padronizados |
| `api_sales.py` | **Consumidor** | Usa `pagamentos[]`, `tem_pos`, `canal_venda`, `codigo_tipo_pago` no `build_sale_json()` |
| `validators.py` | **Consumidor** | Valida Etapa 2 (Pagamento): códigos, POS, BIN, múltiplo |

---

## 6. Pontos de Entrada

```python
from validaai import PaymentNormalizer

normalizer = PaymentNormalizer()
result = normalizer.normalize_payment(test_dict)

# test_dict deve conter:
# - 'pagamento': str (ex: "Dinheiro e Cartao Debito")
# - 'observacoes': str (opcional, para POS/canal/cancelamento)

# Resultado (cópia enriquecida):
{
    ...campos originais...,
    'pagamento_normalizado': 'MULTIPLO',
    'codigo_tipo_pago': None,  # None se múltiplo
    'is_multiplo': True,
    'requires_bin': True,
    'pagamentos': [
        {'norm': 'dinheiro', 'codigo': 9, 'raw': 'Dinheiro', 'tem_pos': False},
        {'norm': 'cartao debito', 'codigo': 13, 'raw': 'Cartao Debito', 'tem_pos': True}
    ],
    'tem_pos': True,  # Qualquer cartão = POS
    'canal_venda': 1,  # Padrão
    'is_cancelamento_venda': False,
    'is_cancelamento_antecipado': False
}
```

---

## 7. Fluxos Importantes

### 7.1 Normalização de Pagamento
```
normalize_payment(test_dict)
    → _normalize_payment_string(pagamento_raw, observacoes)
        1. Detecta POS: keywords em obs/pagamento (pos, terminal, cartao, pix, etc)
        2. Detecta Canal: "canal de venda 2"→2, "diferente de 1 e 2"→3
        3. Detecta Cancelamentos: "cancelar venda", "cancelar antes de finalizar"
        4. Split múltiplo: regex split por `+`, ` e `, vírgulas
        5. Para cada parte:
            - Detecta multiplicador: "duas vezes cartao credito"
            - Match exato ou parcial em PAYMENT_MAPPING
            - Gera entrada em pagamentos[] com norm, codigo, raw, tem_pos
        6. Retorna dict com todos os flags
```

### 7.2 Lógica de POS (Auto-detect)
```python
# Qualquer indício de cartão/PIX = POS
tem_pos = any(keyword in obs_lower for keyword in [
    'pos', 'pos.', 'pos ', 'p.o.s', 'terminal pos', 'maquina pos', 'maquininha pos'
]) or any(keyword in pagamento_lower for keyword in [
    'cartao', 'cartão', 'credito', 'crédito', 'debito', 'débito', 'pix', 'qr'
])
```

### 7.3 Canal de Venda
| Observação | Canal |
|------------|-------|
| `canal de venda 2` ou `canal 2` | 2 (E-COMMERCE) |
| `diferente de 1 e 2` / `canal diferente de 1` | 3 (OUTROS) |
| Padrão | 1 (VENDA NA LOJA) |

---

## 8. Arquivos Críticos

| Arquivo | Função |
|---------|--------|
| `src/validaai/payments.py` | **Único arquivo** (219 linhas) |

---

## 9. Observações Técnicas e Débitos

### 🟢 Pontos Fortes
- **POS Auto-detect**: Qualquer cartão/PIX implica POS (regra de negócio Scanntech)
- **Múltiplos Robustos**: Suporta "duas vezes", "3x", separadores variados
- **Cancelamento Antecipado**: Retorna estrutura especial sem pagamento
- **BIN Inteligente**: `requires_bin=True` apenas para cartão + promoção

### 🟡 Débitos Técnicos
| Débitos | Descrição | Prioridade |
|---------|-----------|------------|
| **Mapeamento Hardcoded** | `PAYMENT_MAPPING` fixo em classe | P2 - Externalizar para config YAML |
| **Multiplicador Limitado** | Apenas "duas vezes", "tres vezes" | P3 - Suportar números |
| **Banco não Detectado** | `codigoBanco` sempre 0 no JSON | P2 - Extrair de observações |
| **Vale = 12 vs 15** | `vale` mapeia para 12, mas `finalizadora`=15 | P2 - Confirmar com Scanntech |

### 🔴 Riscos
- **Mapeamento Scanntech**: Mudança de códigos pela API quebra integração → externalizar config
- **POS Over-detection**: Qualquer "cartao" no texto ativa POS → pode gerar falsos positivos em observações

---

## 9.1 Hipóteses de Melhoria

| Hipótese | Impacto |
|----------|---------|
| Config `payment_mappings.yaml` versionado por parceiro | Deploy-free updates |
| Detecção de banco via regex `banco\s+(\w+)` em observações | Preenche `codigoBanco`/`descripcionBanco` |
| Validação cruzada: `tem_pos=True` ↔ `pagamentos[].tem_pos=True` | Consistência interna |

---

**Fim do README - Módulo Payments**  
*Última atualização: 2026-06-21 | Versão 2.1.0*