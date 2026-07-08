# Módulo: Validators (`src/validaai/validators.py`)

**Versão:** 2.1.0  
**Responsável:** ValidaAI Team  
**Status:** Produção

---

## 1. Objetivo do Módulo

Implementar o **pipeline de validação SDD v1.0 (5 estágios)** e manter compatibilidade com **validação legada** usada pelo `.exe` e testes headless.

---

## 2. Responsabilidade Principal

| Responsabilidade | Detalhe |
|------------------|---------|
| **Pipeline SDD (5 Estágios)** | 1.Itens → 2.Pagamento → 3.Valores → 4.Obs Especiais → 5.Consolidação |
| **Prioridade de Status** | Observação Parceiro > REVISAO (casos especiais) > ERRO > OK |
| **Tolerância Inteligente** | `effective_tolerance = max(tolerance, 0.011)` para float edge cases |
| **Validação Legada** | `validate_legacy()` - compatível com `.exe` e testes headless |
| **Logging Estruturado** | Etapa-a-etapa via `ValidationLogger` |
| **Validação JSON Parceiro** | Confronta roteiro vs `export_auditoria` + `export_movimentos` |

---

## 3. Funcionalidades Existentes

### 3.1 Pipeline SDD (`validate()`)

| Estágio | Método | Valida |
|---------|--------|---------|
| **Etapa 1** | `_validate_etapa1_itens()` | EANs, quantidades, pesáveis vs partner JSON |
| **Etapa 2** | `_validate_etapa2_pagamento()` | Códigos pagamento, POS, BIN, múltiplo vs partner JSON |
| **Etapa 3** | `_validate_etapa3_valores()` | Subtotal, desconto, total vs roteiro + partner JSON |
| **Etapa 4** | `_validate_etapa4_observacoes()` | Cancelamento, acréscimo, desconto especial, pesável, troco, multiplo |
| **Etapa 5** | Consolidação (linhas 176-195) | Prioridade: Obs Parceiro → REVISAO → ERRO → OK |

### 3.2 Validação Legada (`validate_legacy()`)

| Método Legado | Função |
|---------------|--------|
| `_validate_teste_id` | ID do teste válido |
| `_validate_itens_parsed` | Itens parseados existem |
| `_validate_special_cases` | Cancelamento, acréscimo, pesável, etc |
| `_validate_payment_mapped` | Pagamento mapeado para código API |
| `_validate_subtotal_numeric` | Subtotal numérico |
| `_validate_desconto_numeric` | Desconto numérico |
| `_validate_total_numeric` | Total numérico |
| `_validate_total_consistency` | Total = Subtotal - Desconto + Acréscimo |
| `_validate_pagos_json` | Array `pagos` no partner JSON |
| `_validate_api_not_run` | Partner JSON não encontrado |

---

## 4. Dependências

### Internas
| Módulo | Uso |
|--------|-----|
| `logger.py` | `ValidationLogger`, `LogLevel`, `TestStatus` para logging estruturado |

### Externas
| Dependência | Uso |
|-------------|-----|
| `decimal.Decimal` | Cálculos financeiros precisos |
| `json` | Parse partner JSONs |
| `typing` | Type hints |

---

## 5. Módulos Relacionados

| Módulo | Relação | Dados |
|--------|---------|-------|
| `reader.py` | **Fornecedor** | Test cases estruturados + `product_catalog` |
| `parser_items.py` | **Fornecedor** | `itens_parseados`, `pesaveis_esperados` |
| `payments.py` | **Fornecedor** | `pagamento_normalizado`, `codigo_tipo_pago`, `pagamentos[]`, `tem_pos`, `canal_venda` |
| `api_sales.py` | **Bidirecional** | Usa `partner_jsons` para validação cruzada; validador usa builder para JSON ideal |
| `logger.py` | **Consumidor** | `ValidationLogger.log_test_result()` |

---

## 6. Pontos de Entrada

```python
from validaai import TestValidator

# Pipeline SDD (novo, recomendado)
validator = TestValidator(tolerance=0.01, partner_jsons=audit_jsons, logger=logger)
result = validator.validate(test_dict)

# Validação Legada (compatibilidade .exe/headless)
validator = TestValidator()
result = validator.validate_legacy(test_dict)

# Resultado comum:
{
    'status_final': 'OK' | 'REVISAO' | 'ERRO_ITENS' | 'ERRO_PAGAMENTO' | 'ERRO_VALORES' | 'NOT_RUN',
    'motivo_status': 'Descrição legível',
    'etapa1_itens': {'json': 'OK'|'REVISAO'|'ERRO', 'json_motivo': '...'},
    'etapa2_pagamento': {...},
    'etapa3_valores': {...},
    'etapa4_observacoes': {...},
    'alertas': [...],
    'api_status': 'OK'|'ALERTA_JSON'|'ERRO_JSON'|'NOT_RUN',
    'api_alertas': [...]
}
```

---

## 7. Fluxos Importantes

### 7.1 Pipeline SDD - Prioridade de Status (Linhas 176-195)

```python
# 1. Observação do Parceiro (coluna Observacoes.1) → REVISAO override TUDO
if tem_obs_parceiro:
    status_final = 'REVISAO'

# 2. REVISAO de casos especiais (cancelamento, acréscimo, etc)
elif revisao_required:
    status_final = 'REVISAO'

# 3. ERRO hard (qualquer etapa falhou)
elif erro_status:
    status_final = erro_status  # ERRO_ITENS, ERRO_PAGAMENTO, ERRO_VALORES

# 4. OK
else:
    status_final = 'OK'
```

### 7.2 Tolerância Efetiva
```python
def __init__(self, tolerance=0.01, ...):
    self.tolerance = tolerance
    self.effective_tolerance = max(tolerance, 0.011)  # Absorve 0.010000001
```

### 7.3 Validação Cruzada Partner JSONs
- Carrega `partner_jsons` (auditoria) + `movimentos_jsons` (promoções aplicadas)
- Merge: `all_partner_jsons = {**partner_jsons, **movimentos_jsons}` (movimentos tem prioridade)
- Compara EAN-a-EAN, quantidade, valores, pagamentos

---

## 8. Arquivos Críticos

| Arquivo | Função |
|---------|--------|
| `src/validaai/validators.py` | **Único arquivo** (1295 linhas) |

---

## 9. Observações Técnicas e Débitos

### 🟢 Pontos Fortes
- **Duas validações coexistem**: SDD (novo, estruturado) + Legacy (compatibilidade)
- **Tolerância 0.011**: Resolve `0.010000001` sem falsos positivos
- **Logging estruturado**: Cada etapa logada com `test_num, status, motivo, resumo_etapas, detalhes_etapas`
- **Prioridade explícita**: Código legível, ordem de precedência clara

### 🟡 Débitos Técnicos
| Débitos | Descrição | Prioridade |
|---------|-----------|------------|
| **God Class** | 1295 linhas, validação + logging + legacy + consolidação | **P0** - Split em classes |
| **Legacy Chain Rígida** | 10 métodos encadeados com side-effects | **P1** - Extrair `LegacyValidationChain` |
| **Coupling com api_sales** | Validador conhece builder internamente | **P1** - Injetar interface |
| **partner_jsons Loading** | Feito dentro do validador (linha 463 api_sales) | **P1** - Mover para loader dedicado |
| **Métodos Privados Longos** | `_validate_etapa1_itens` 150+ linhas | **P2** - Decompor |

### 🔴 Riscos
- **Mudança no SDD quebra Legacy**: Dois pipelines compartilham estado
- **Acoplamento Circular**: `validators` ↔ `api_sales` via `partner_jsons`
- **Testabilidade**: `validate_legacy()` difícil de testar unitariamente

---

## 9.1 Hipóteses de Refatoração (Roadmap)

| Refatoração | Esforço | Benefício |
|-------------|---------|-----------|
| `Stage1Validator`..`Stage5Validator` + `Consolidator` | 3 dias | Testável, extensível, SRP |
| `LegacyValidationChain` class separada | 1 dia | Isola legado, facilita remoção futura |
| `IPartnerJSONLoader` interface | 1 dia | Quebra circular dependency |
| `ValidationFacade` para GUI | 2 dias | Single entry point, testável |

---

**Fim do README - Módulo Validators**  
*Última atualização: 2026-06-21 | Versão 2.1.0*