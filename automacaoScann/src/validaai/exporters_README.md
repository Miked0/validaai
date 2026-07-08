# Módulo: Exporters (`src/validaai/exporters.py`)

**Versão:** 2.1.0  
**Responsável:** ValidaAI Team  
**Status:** Produção:** Produção

---

## 1. Objetivo do Módulo

Exportar resultados de validação para **Excel (.xlsx)** ou **CSV** com colunas padronizadas para auditoria e entrega ao parceiro.

---

## 2. Responsabilidade Principal

| Responsabilidade | Detalhe |
|------------------|---------|
| **Export Multi-formato** | Excel (pandas) + CSV fallback (stdlib) |
| **Colunas Padronizadas** | Formato compatível com auditoria Scanntech |
| **Serialização JSON** | `sale_json` e `response` serializados com Decimal support |
| **Empty Output Handling** | Cria arquivo com headers mesmo sem resultados |

---

## 3. Funcionalidades Existentes

| Funcionalidade | Método | Descrição |
|----------------|--------|-----------|
| `export()` | Público | Principal - recebe `List[Dict]` + `output_path` |
| `_create_empty_output()` | Privado | Cria arquivo só com headers se lista vazia |

### Colunas de Exportação (Ordem Definida)

| Coluna | Origem no test_dict |
|--------|---------------------|
| `teste` | `teste` |
| `bloco` | `bloco_atual` |
| `tipo_promo` | `tipo_promo` |
| `itens_raw` | `itens_da_venda` / `itens_raw` |
| `itens_parseados` | `itens_parseados` (formatado) |
| `pagamento_raw` | `pagamento` |
| `codigo_tipo_pago` | `codigo_tipo_pago` |
| `pagamento_label` | `get_payment_label(codigo_tipo_pago)` |
| `subtotal_esperado` | `subtotal_esperado` |
| `subtotal_norm` | `subtotal` calculado |
| `desconto_esperado` | `desconto_esperado` |
| `desconto_norm` | `desconto` calculado |
| `total_esperado` | `total_esperado` |
| `total_norm` | `total` calculado |
| `status_final` | `status_final` |
| `motivo_status` | `motivo_status` |
| `alertas` | `alertas` (join) |
| `observacoes_originais` | `observacoes` |
| `sat`, `ecf`, `nfce` | Campos diretos |
| `json`, `minoristas`, `cupom` | Campos diretos |
| `api_status`, `api_alertas` | Validação JSON parceiro |
| `sale_json` | JSON API 3.0 serializado |

---

## 4. Dependências

### Internas
- Nenhuma

### Externas
| Dependência | Obrigatória? | Uso |
|-------------|--------------|-----|
| `pandas` | **Sim** | Excel export, DataFrame manipulation |
| `json`, `decimal` | Stdlib | Serialização JSON com Decimal support |

---

## 5. Módulos Relacionados

| Módulo | Relação |
|--------|---------|
| `validators.py` | **Fornecedor** - Consome resultados de `validate()` |
| `gui_app_standalone.py` | **Consumidor** - Usa `ResultExporter` para botão "Exportar" |
| `run_full_validation.py` | **Consumidor** - Headless export |

---

## 6. Pontos de Entrada

```python
from validaai import ResultExporter

exporter = ResultExporter()
exporter.export(test_results, 'resultado_validacao.xlsx')
# ou
exporter.export(test_results, 'resultado_validacao.csv')
```

---

## 7. Fluxos Importantes

### 7.1 Export Pipeline
```python
export(test_results, output_path)
    1. Valida se test_results não vazio
    2. Para cada test:
        - Extrai campos mapeados
        - Formata itens_parseados como string legível
        - Serializa sale_json com Decimal support
        - Converte alertas list para string
    3. Cria DataFrame pandas
    4. Reordena colunas (column_order)
    4. Exporta: df.to_excel() ou df.to_csv()
    5. Fallback CSV se pandas não disponível
```

### 7.2 Serialização Decimal
```python
def _default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(...)

json.dumps(sale_json, ensure_ascii=False, default=_default)
```

---

## 8. Arquivos Críticos

| Arquivo | Função |
|---------|--------|
| `src/validaai/exporters.py` | **Único arquivo** (195 linhas) |

---

## 9. Observações Técnicas e Débitos

### 🟢 Pontos Fortes
- **Fallback CSV**: Funciona sem pandas (stdlib `csv`)
- **Colunas Fixas**: Ordem consistente para auditoria
- **Empty Handling**: Não falha com lista vazia
- **Label Pagamento**: Usa `get_payment_label()` para legibilidade

### 🟡 Débitos Técnicos
| Débitos | Descrição | Prioridade |
|---------|-----------|------------|
| **Pandas Obrigatório para Excel** | Sem pandas só CSV | P2 |
| **Colunas Hardcoded** | `COLUMNS` fixo na classe | P3 - Config YAML |
| **Formatação Itens** | String simples, não estruturada | P3 |
| **Duplicação com GUI** | `gui_app_standalone.py` tem `ResultExporter` próprio | **P1** - Unificar |

### 🔴 Riscos
- **Duplicação Real**: `gui_app_standalone.py` linhas 1072-1200 tem `ResultExporter` quase idêntico
- **Pandas Dependency**: Quebra build em ambientes sem pandas

---

## 9.1 Hipóteses de Melhoria

| Hipótese | Impacto |
|----------|---------|
| Unificar `ResultExporter` único (remover do GUI) | Single source of truth |
| Config `export_columns.yaml` | Customização por parceiro |
| Streaming export para datasets grandes | Memória constante |

---

**Fim do README - Módulo Exporters**  
*Última atualização: 2026-06-21 | Versão 2.1.0*